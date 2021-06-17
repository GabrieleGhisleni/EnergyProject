from sqlalchemy import create_engine
import json, time, datetime,os, csv, datetime,argparse
from tqdm import tqdm
from typing import List, TypeVar
from fetching_meteo import *
from meteo_classes import *
import pandas as pd
import mysql.connector as sql
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")
from KEYS.config import RDS_USER,RDS_PSW,RDS_HOST



###################################################################################################################
class ManagerTernaSql():
    """
    class created to handle the file transfer from Terna to our databases.
    """
    def __init__(self):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        self.engine.connect()

    def MeteoAndRadiationSave(self, meteos:List[MeteoData], radiations:List[MeteoRadiationData])->None:
        """
        Given two list of MeteoData and MeteoRadiation data it update the local SQL database.
        """
        print(f"Updating energy.meteo database with {len(meteos)/20} MeteoData and {len(radiations)/20} RadiationData")
        i,o, check, n=0,0,0,1
        cursor = self.engine
        for iel in range(len(meteos)):
            check += 1
            if ":00" in meteos[iel].cross_join:
                tmp = dict(date=datetime.datetime.strptime(meteos[iel].cross_join, "%d/%m/%Y %H:%M %p"),
                   clouds=meteos[iel].clouds, pressure=meteos[iel].pressure, humidity=meteos[iel].humidity,
                   temp=meteos[iel].temp, rain_1h=meteos[iel].rain_1h, snow_1h=meteos[iel].snow_1h,
                   wind_deg=meteos[iel].wind_deg, wind_speed=meteos[iel].wind_speed,
                   globalhorizontalirradiance_2=radiations[iel].globalhorizontalirradiance_2,
                   directnormalirradiance=radiations[iel].directnormalirradiance,
                   directnormalirradiance_2=radiations[iel].directnormalirradiance_2,
                   diffusehorizontalirradiance_2=radiations[iel].diffusehorizontalirradiance_2,
                   diffusehorizontalirradiance= radiations[iel].diffusehorizontalirradiance)
                print(f'Exit tmp at {check}')
                break

        query = """INSERT into energy_meteo (
        date, clouds, pressure, humidity, temp, rain_1h, snow_1h, wind_deg, wind_speed,
        globalhorizontalirradiance_2,directnormalirradiance,directnormalirradiance_2,
        diffusehorizontalirradiance,diffusehorizontalirradiance_2) VALUES 
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        for iel in tqdm(range(check, len(radiations))):
            if ":00" in meteos[iel].cross_join:
                if (datetime.datetime.strptime(meteos[iel].cross_join, "%d/%m/%Y %H:%M %p")) == tmp['date']:
                    n += 1
                    tmp['clouds'] += meteos[iel].clouds
                    tmp['pressure'] += meteos[iel].pressure
                    tmp['humidity'] += meteos[iel].humidity
                    tmp['temp'] += meteos[iel].temp
                    tmp['rain_1h'] += meteos[iel].rain_1h
                    tmp['snow_1h'] += meteos[iel].snow_1h
                    tmp['wind_deg'] += meteos[iel].wind_deg
                    tmp['wind_speed'] += meteos[iel].wind_speed
                    tmp['directnormalirradiance'] += radiations[iel].directnormalirradiance
                    tmp['diffusehorizontalirradiance'] += radiations[iel].diffusehorizontalirradiance
                    tmp['directnormalirradiance_2'] += radiations[iel].directnormalirradiance_2
                    tmp['diffusehorizontalirradiance_2'] += radiations[iel].diffusehorizontalirradiance_2
                    tmp['globalhorizontalirradiance_2'] += radiations[iel].globalhorizontalirradiance_2
                else:
                    o+=1
                    for k in tmp:
                        if type(tmp[k])!= datetime.datetime: tmp[k]= tmp[k] / n
                    cursor.execute(query, (
                        tmp['date'],
                        tmp['clouds'],
                        tmp['pressure'],
                        tmp['humidity'] ,
                        tmp['temp'] ,
                        tmp['rain_1h'],
                        tmp['snow_1h'],
                        tmp['wind_deg'] ,
                        tmp['wind_speed'],
                        tmp['directnormalirradiance'] ,
                        tmp['diffusehorizontalirradiance'] ,
                        tmp['directnormalirradiance_2'],
                        tmp['diffusehorizontalirradiance_2'],
                        tmp['globalhorizontalirradiance_2']))
                    n=1
                    tmp = dict(date=datetime.datetime.strptime(meteos[iel].cross_join, "%d/%m/%Y %H:%M %p"),
                       clouds=meteos[iel].clouds, pressure=meteos[iel].pressure, humidity=meteos[iel].humidity,
                       temp=meteos[iel].temp, rain_1h=meteos[iel].rain_1h, snow_1h=meteos[iel].snow_1h,
                       wind_deg=meteos[iel].wind_deg, wind_speed=meteos[iel].wind_speed,
                       globalhorizontalirradiance_2=radiations[iel].globalhorizontalirradiance_2,
                       directnormalirradiance=radiations[iel].directnormalirradiance,
                       directnormalirradiance_2=radiations[iel].directnormalirradiance_2,
                       diffusehorizontalirradiance_2=radiations[iel].diffusehorizontalirradiance_2,
                       diffusehorizontalirradiance= radiations[iel].diffusehorizontalirradiance)
        print(f"Rows executed = {o}")

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
                            query = """INSERT into energy_generation (date, energy_source, generation) VALUES (%s,%s,%s)"""
                            self.engine.execute(query, (row["date"],row["energy_source"], row["generation"]))
                else:
                    df = pd.read_csv(path_to_file)
                    df.rename(columns={'Date': "date", 'Energy Source': 'energy_source',
                                       'Renewable Generation [GWh]': 'generation'},inplace=True)
                    df.to_sql('energy_generation', con=self.engine, if_exists='append', index=False)
            elif path_to_file.endswith(".xlsx"):  print("to implement yet, pass a csv instead")
            else: print(f".{path_to_file.split('.')[1]} is not a valid format!" )
        else: print(f"{path_to_file} is not a valid path.")

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
                        current = current[current['Date'].dt.strftime("%M") == '00']
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
                else: print(f"{path} is not a valid load path!")
        else: print(f"{path_to_holiday} is not a valid holiday path!")
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

    def prediction_to_sql(self, predictions:Dict):
        ""
        i=0
        query = """insert into prediction_energy(date, energy, generation) VALUES(%s,%s,%s);"""
        predictions = predictions
        df = pd.DataFrame.from_dict(predictions, orient='index')
        df.reset_index(inplace=True, drop = False)
        df.rename(columns={'index':'date'}, inplace=True)
        for source in df.columns:
            if str(source) != 'date' and str(source) != 'index':
                tmp = df[['date', source]].copy()
                tmp['energy']= source
                tmp.rename(columns={source:'generation'}, inplace=True)
                tmp.to_sql("prediction_energy",  con=self.engine,
                                         if_exists = 'append', index = False)


    def preprocess_thermal_prediction_to_sql(self, pred, dates: pd.Series)->None:
        """
        Must find a way to UPDATE IF EXISTS ELSE INSERT INTO
        """
        df =  pd.DataFrame(pred, dates)
        df["date"] = df.index
        df["energy"] = "thermal"
        df.rename(columns={0:'generation'}, inplace=True)
        df.to_sql("prediction_energy",  con=self.engine,
                                         if_exists = 'append', index = False)

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

class populating_the_sql_database:
    """
    Following the already prepared folder inside the git, launch this function
    to populate all the SQL tables.
    """
    def energy_load(self)->None:
        listu = os.listdir("../Documentation/Files example/load_terna")
        listu = ["../Documentation/Files example/load_terna/"+path for path in listu]
        ManagerTernaSql().load_from_terna_and_holiday(listu, "../Documentation/Files example/holiday_BACKWARD.csv")
    def energy_production(self)->None:
        ManagerTernaSql().generation_from_terna_to_db("../Documentation/Files example/generation_terna/generation_2.csv", "asd")
    def energy_thermal(self)->None:
        paths = ["Files example/Energy_balance/" + i for i in os.listdir("Files example/Energy_balance")]
        #paths = ["Files example/EnergyBalance_all/" + i for i in os.listdir("Files example/EnergyBalance_all")]
        ManagerTernaSql().thermal_from_terna_to_db(paths)
    def energy_installed_capacity(self)->None:
        ManagerTernaSql().load_energy_installed_capacity("Files example/installed_capacity.csv")
    def from_json_to_db(self):
        rad = JsonManagerCurrentRadiation('../Documentation/Files example/json_meteo/storico_radiation.json').load_unprocess()
        meteo = JsonManagerCurrentMeteo('../Documentation/Files example/json_meteo/storico_meteo.json').load_unprocess()
        ManagerTernaSql().MeteoAndRadiationSave(radiations=rad, meteos= meteo)


def main():
    arg_parser = argparse.ArgumentParser(description="Data Collector Meteo")
    arg_parser.add_argument("-r", "--rate", default='auto', choices = ['crontab','auto'],
                            help="Rate of the collection, if type 'auto' it will deal the best option for collecting data, otherwhise it just" \
                                 "collect the data and finish so is possible to deal with crontab options")
    args = arg_parser.parse_args()
    if args.rate == 'auto':
        now = datetime.datetime.now()
        if not(now.strftime("%M").endswith("00")):
            print("i'll start at the :00 of the next hour!")
        while True:
            now = datetime.datetime.now()
            if now.strftime("%M").endswith("00"):
                print(f'Uploading MySQL database at {now}')
                mysql = ManagerTernaSql()
                radiations = GetMeteoData().fetching_current_solar_radiation()
                radiations = [MeteoRadiationData.current_from_original_dict_to_class(rad) for rad in radiations]
                meteos = GetMeteoData().fetching_current_meteo_json()
                meteos = [MeteoData.current_from_original_dict_to_class(meteo) for meteo in meteos]
                mysql.MeteoAndRadiationSave(meteos, radiations)
                print("Updated")
    elif args.rate =='crontab':
        now = datetime.datetime.now()
        print(f'Uploading MySQL database at {now}')
        mysql = ManagerTernaSql()
        radiations = GetMeteoData().fetching_current_solar_radiation()
        radiations = [MeteoRadiationData.current_from_original_dict_to_class(rad) for rad in radiations]
        meteos = GetMeteoData().fetching_current_meteo_json()
        meteos = [MeteoData.current_from_original_dict_to_class(meteo) for meteo in meteos]
        mysql.MeteoAndRadiationSave(meteos, radiations)
        print("Updated")
    else: print(f"Not valid broker - {args.broker}"),exit()

if __name__ == "__main__":
    main()