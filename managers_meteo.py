from sqlalchemy import create_engine
import json, time, datetime,os, csv, datetime
from tqdm import tqdm
from typing import List, TypeVar
from fetching_meteo import *
from meteo_classes import *
import pandas as pd
import mysql.connector as sql
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")

###################################################################################################################
class ManagerTernaSql():
    """
    class created to handle the file transfer from Terna to our databases.
    """
    def __init__(self):
        self.engine = create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        self.engine.connect()

    def MeteoAndRadiationSave(self, meteos:List[MeteoData], radiations:List[MeteoRadiationData])->None:
        """
        Given two list of MeteoData and MeteoRadiation data it update the local SQL database.
        """
        print("Updating Meteo database")
        cursor = self.connection.cursor()
        query = """INSERT into energy_meteo (
        date, clouds, pressure, humidity, temp, rain_1h, snow_1h, wind_deg, wind_speed,
        globalhorizontalirradiance_2,directnormalirradiance,directnormalirradiance_2,
        diffusehorizontalirradiance,diffusehorizontalirradiance_2) VALUES 
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        fix_hour = datetime.timedelta(hours=2)
        for iel in tqdm(range(len(radiations))):
            if ":00 " in radiations[iel].cross_join and ":00" in meteos[iel].cross_join:
                cursor.execute(query, (
                    str(datetime.datetime.strptime(meteos[iel].cross_join, "%d/%m/%Y %H:%M %p")-fix_hour),
                    meteos[iel].clouds,
                    meteos[iel].pressure,
                    meteos[iel].humidity,
                    meteos[iel].temp,
                    meteos[iel].rain_1h,
                    meteos[iel].snow_1h,
                    meteos[iel].wind_deg,
                    meteos[iel].wind_speed,
                    radiations[iel].globalhorizontalirradiance_2,
                    radiations[iel].directnormalirradiance,
                    radiations[iel].directnormalirradiance_2,
                    radiations[iel].diffusehorizontalirradiance,
                    radiations[iel].diffusehorizontalirradiance_2,
                ))

    def generation_from_terna_to_db(self, path_to_file:str, process:str='linebyline')->None:
        """
        Function that given the .csv obtained from the Terna Download Center
        it preprocess the data and add to our local database.
        Process line by line it took around 20 second.
        While the same with pandas without spark it took around 40 second.
        """
        if os.path.exists(path_to_file):
            if path_to_file.endswith(".csv"):
                if process == 'linebyline':
                    with open(path_to_file, "r", encoding="utf-8") as file:
                        obs = csv.DictReader(file)
                        next(obs)
                        field = ['date', 'generation','energy_source']
                        obs.fieldnames = field
                        print("Start process and updating energy_generation table!")
                        for row in tqdm(obs):
                            query = """INSERT into energy_production (date, energy_source, generation) VALUES (%s,%s,%s)"""
                            self.engine.execute(query, (row["date"],row["energy_source"], row["generation"]))
                else:
                    df = pd.read_csv(path_to_file)
                    df.rename(columns={'Date': "date", 'Energy Source': 'energy_source',
                                       'Renewable Generation [GWh]': 'generation'},inplace=True)
                    df.to_sql('energy_production', con=self.engine, if_exists='append', index=False)
            elif path_to_file.endswith(".xlsx"):
                print("to implement yet, pass a csv instead")
            else:
                print(f".{path_to_file.split('.')[1]} is not a valid format!" )
        else:
            print(f"{path_to_file} is not a valid path.")

    def load_from_terna_and_holiday(self, paths_to_file:List[str], path_to_holiday:str)->None:
        """
        Function that given a list of .xlsx file obtained from the Terna Download Center
        it preprocess the data, add the socio-economic predictor refered to the holidays
        and store it into our local sql database. this is a process to made just once.
        """
        if os.path.exists(path_to_holiday):
            tot = 0
            holiday = pd.read_csv(path_to_holiday)
            holiday.rename(columns={'Date': 'cross_date'}, inplace=True)
            #holiday.drop(columns=["DayName"], inplace=True)
            print("Start process and updating energy_load table!")
            for path in tqdm(paths_to_file):
                if os.path.exists(path):
                    if path.endswith('.xlsx'):
                        current = pd.read_excel(path, skiprows=[1], header=[1])
                        current = current[current["Bidding zone"] == "Italy"]
                        current.drop(columns=["Forecast Total load [MW]", "Bidding zone"], inplace=True)
                        tmp = pd.to_datetime(current["Date"], format="%d/%m/%Y %H:%M:%S %p")
                        current["cross_date"] = tmp.dt.strftime("%Y-%m-%d")
                        current["Date"] = current["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
                        current = current.merge(holiday, how="inner", on="cross_date")
                        current.drop(columns=["cross_date"], inplace=True)
                        current.rename(columns={'Total Load [MW]': "total_load", 'Date':'date', 'Holiday':'holiday'}, inplace=True)
                        current["total_load"] = current["total_load"]/1000
                        current.to_sql('energy_load', con=self.engine, if_exists='append', index=False)
                        tot += len(current)
                    else:
                        extension = path.split('.')[1]
                        print(f".{extension} is not a valid format!")
                else:
                    print(f"{path} is not a valid load path!")
        else:
            print(f"{path_to_holiday} is not a valid holiday path!")
        print(f"Update {tot} rows")

    def load_energy_installed_capacity(self, path:str)->None:
        """
        Accept only csv.
        """
        if os.path.exists(path):
            if not path.endswith(".csv"):
                extension = path.split(".")[1]
                print(f".{extension} is not a valid extension")
                return
            else:
                df = pd.read_csv(path)
                query = """INSERT into energy_installed_capacity(relevation_year, energy_source, capacity) 
                VALUES (%s,%s,%s)"""
                print("Updating energy_installed_capacity databse!")
                for i, row in df.iterrows():
                    self.engine.execute(query, (str(row["Year"]), row["Type"], row["Installed Capacity [GW]"]))
        else:
            print(f"{path} is not a valid path!")

    def query_from_sql_to_pandas(self,query)-> PandasDataFrame:
        """
        Fancy function that given a query it return the result as
        a Pandas DataFrame, if the query return none the data frame
        will be empty
        """
        return (pd.read_sql_query(query, self.engine))

    def prediction_to_sql(self, predictions:List[Dict]):
        ""
        i=0
        query = """insert into prediction_energy(date, energy, generation) VALUES(%s,%s,%s);"""
        predictions = predictions[0]
        for hour in predictions:
            for source in predictions[hour]:
                self.engine.execute(query, (hour, source, predictions[hour][source]))
                i+=1
        print()
        print(f"Updating renewable generation and load --> {i} rows")

    def preprocess_thermal_prediction_to_sql(self, pred, dates: pd.Series):
        df =  pd.DataFrame(pred, dates)
        df["date"] = df.index
        df["energy"] = "thermal"
        df.rename(columns={0:'generation'}, inplace=True)
        df.to_sql("prediction_energy",  con=self.engine,
                                         if_exists = 'append', index = False)
        print(f"Updating thermal generation --> {len(df)} rows")

    def thermal_from_terna_to_db(self, paths:List[str])->None:
        """
        Given all the csv from energy balance in Terna it will update perform some
        preprocess operation, it will sum up all the energy source that are not thermal
        and will update the database. the field are date, sum_energies, thermal_energy.
        """
        tmp = []
        for path in paths:
            df = pd.read_csv(path, parse_dates=["Date"])
            tmp.append(df)
        final = pd.concat(tmp)
        final = final.sort_values("Date")
        only_thermal = final[final["Energy Source"] == "Thermal"]
        only_but_thermal = final[final["Energy Source"] != "Thermal"]
        only_but_thermal.drop(columns=["Energy Source"], inplace=True)
        only_thermal.drop(columns=["Energy Source"], inplace=True)
        only_but_thermal.rename(columns={"Energy Balance [GWh]": "Sum_of_rest_GW"}, inplace=True)
        only_thermal.rename(columns={"Energy Balance [GWh]": "termal_GW"}, inplace=True)
        g = only_but_thermal.groupby('Date', as_index=False)
        res = []
        for name, group in tqdm(g):
            tmp = pd.DataFrame(group.sum())
            columns = list(tmp.index)[0:]
            valori = list(tmp[0][0:].values)
            df_2 = pd.DataFrame([valori], columns=columns)
            df_2.insert(loc=0, column='Date', value=name)
            res.append(df_2)
        final_sources = pd.concat(res)
        final = final_sources.merge(only_thermal, how="inner", on="Date")
        final.rename(columns={"Date":"date","Sum_of_rest_GW":"sum_of_rest_GW","termal_GW":"thermal_GW"},inplace=True)
        print(f"Updating {len(final)} into the database!")
        #final.to_csv("energy_thermal.csv", index=False)
        final.to_sql("energy_thermal",  con=self.engine,if_exists = 'append', index = False)

    # def load_prediction_to_sql(self, predictions:list[dict])->None:
    #     """
    #     Function created to drop the messages from Mqtt to the local database
    #     since we perform this operation twice a day first it try to insert the value
    #     and in case those values are already present (since there are unique) python will
    #     raise an error and in this case it will update those rows with the new predictions :P.
    #     """
    #     new,tot = 0,0
    #     for day in predictions:
    #         for hour in day:
    #             try:
    #                 query = """insert into prediction_load(date, prediction_load) VALUES(%s,%s);"""
    #                 self.engine.execute(query, (hour, day[hour]))
    #                 new+=1
    #             except Exception as e:
    #                 query = f"""update  prediction_load
    #                             set  prediction_load={day[hour]}
    #                             where(date='{hour}');"""
    #                 self.engine.execute(query)
    #                 tot+=1
    #     print(f"Update {tot}, Added {new} --> records into prediction_load")

###################################################################################################################
def into_the_loop_json():
    manager = JsonManagerCurrentMeteo()
    manager_2 = JsonManagerCurrentRadiation()
    while True:
        now = datetime.datetime.now()
        if now.strftime("%M").endswith("00") or now.strftime("%M").endswith("15") \
                or now.strftime("%M").endswith("30") or now.strftime("%M").endswith("45"):
                    print("inside")
                    manager.update()
                    manager_2.update()
                    time.sleep(890)
                    print("done")

###################################################################################################################
class JsonManagerCurrentMeteo():
    """
    Manager created to deal the JSON operation as save and load for
    current meteo data. Used for the first collection of the storico.
    """
    def __init__(self, path:str=None):
        self.path = path

    def load_unprocess(self)->List[MeteoData]:
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                storico = json.load(file)
                file.close()
            return [MeteoData.current_from_original_dict_to_class(obj) for obj in storico]
        else:
            print(f"Do not find the right path!")

    def load(self)->List[MeteoData]:
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                storico = json.load(file)
                file.close()
            return [MeteoData.current_from_preprocess_dict_to_class(obj) for obj in storico]
        else:
            print(f"Do not find the right path!")

    def first_update(self, current_meteo:List[MeteoData]):
        print("File not found, created 'storico_meteo.json' and first update")
        obs = [MeteoData.from_class_to_dict(obj) for obj in current_meteo]
        with open("storico_meteo.json", "w") as file:
            json.dump(obs, file, indent=4)
            self.path = "storico_meteo.json"

    def update(self, current_meteo:List[MeteoData])->None:
        if os.path.exists(self.path):
            storico = self.load()
            update = storico + current_meteo
            with open(self.path, "w") as file:
                json.dump([MeteoData.from_class_to_dict(obj) for obj in update], file, indent=4)
        else:
            self.first_update(current_meteo)

class JsonManagerCurrentRadiation():
    """
    Manager created to deal the JSON operation as save and load for
    current radiation data. Used for the first collection of the storico.
    """
    def __init__(self, path:str=None):
        self.path = path

    def load_unprocess(self)->List[MeteoRadiationData]:
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                storico = json.load(file)
                file.close()
            return [MeteoRadiationData.current_from_original_dict_to_class(obj) for obj in storico]
        else:
            print(f"Do not find the right path!")

    def load(self)->List[MeteoRadiationData]:
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                storico = json.load(file)
                file.close()
            return [MeteoRadiationData.current_from_preprocess_dict_to_class(obj) for obj in storico]
        else:
            print(f"Do not find the right path!")

    def first_update(self, radiations:List[MeteoRadiationData])->None:
        print("File not found, created 'storico_radiation.json' and first update")
        obs = [MeteoRadiationData.current_from_class_to_dict(obj) for obj in radiations]
        with open("storico_radiation.json", "w") as file:
            json.dump(obs, file, indent=4)
            self.path = "storico_radiation.json"

    def update(self, radiations:List[MeteoRadiationData])->None:
        if os.path.exists(self.path):
            storico = self.load()
            update = storico + radiations # must optimize this process
            with open(self.path, "w") as file:
                json.dump([MeteoRadiationData.current_from_class_to_dict(obj) for obj in update], file, indent=4)
        else:
            self.first_update(radiations)
###################################################################################################################
class populating_the_sql_database:
    """
    Following the already prepared folder inside the git, launch this function
    to populate all the SQL tables.
    """
    def energy_load(self)->None:
        listu = os.listdir("Files example/load_terna")
        listu = ["Files example/load_terna/"+path for path in listu]
        ManagerTernaSql().load_from_terna_and_holiday(listu, "Files example/holiday_BACKWARD.csv")
    def energy_production(self)->None:
        ManagerTernaSql().generation_from_terna_to_db("Files example/generation_terna/renawable_production.csv")
    def energy_thermal(self)->None:
        paths = ["Files example/Energy_balance/" + i for i in os.listdir("Files example/Energy_balance")]
        #paths = ["Files example/EnergyBalance_all/" + i for i in os.listdir("Files example/EnergyBalance_all")]
        ManagerTernaSql().thermal_from_terna_to_db(paths)
    def energy_installed_capacity(self)->None:
        ManagerTernaSql().load_energy_installed_capacity("Files example/installed_capacity.csv")
###################################################################################################################
if __name__ == "__main__":
    populating_the_sql_database().energy_load()