import json, time, datetime,os, csv
from tqdm import tqdm
from typing import List
from fetching_meteo import *
from meteo_classes import *
import pandas as pd
import mysql.connector as sql
#############################################################################################
class ManagerTernaSql():
    """
    class created to handle the file transfer from Terna to our databases.
    """
    def __init__(self):
        self.connection = sql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password= os.environ.get("SQL"),
            database='energy')
        self.connection.autocommit = True

    def generation_from_terna_to_db(self, path_to_file:str, process:str='linebyline')->None:
        """
        Function that given the .csv obtained from the Terna Download Center
        it preprocess the data and add to our local database.
        Process line by line it took around 20 second.
        While the same with pandas without spark it took around 40 second.
        """
        if os.path.exists(path_to_file):
            cursor = self.connection.cursor()
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
                            cursor.execute(query, (row["date"],row["energy_source"], row["generation"]))
                else:
                    query = """INSERT into energy_production (date, energy_source, generation) VALUES (%s,%s,%s)"""
                    df = pd.read_csv(path_to_file)
                    for i,row in tqdm(df.iterrows()):
                        cursor.execute(query, (row["Date"],row["Energy Source"], row["Renewable Generation [GWh]"]))
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
            cursor = self.connection.cursor()
            holiday = pd.read_csv(path_to_holiday)
            holiday.rename(columns={'Date': 'cross_date'}, inplace=True)
            holiday.drop(columns=["DayName"], inplace=True)
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
                        current.rename(columns={'Total Load [MW]': "Load"}, inplace=True)
                        query = """INSERT into energy_load(date, holiday, total_load) VALUES (%s,%s,%s)"""
                        for i, row in (current.iterrows()):
                            cursor.execute(query,(str(row["Date"]), row["Holiday"], row["Load"]))
                    else:
                        extension = path.split('.')[1]
                        print(f".{extension} is not a valid format!")
                else:
                    print(f"{path} is not a valid load path!")
        else:
            print(f"{path_to_holiday} is not a valid holiday path!")

    def load_energy_installed_capacity(self, path:str)->None:
        """
        Accept only csv.
        """
        cursor = self.connection.cursor()
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
                    cursor.execute(query, (str(row["Year"]), row["Type"], row["Installed Capacity [GW]"]))
        else:
            print(f"{path} is not a valid path!")


#############################################################################################
class JsonManagerCurrentMeteo():
    """
    Manager created to deal the JSON operation as save and load for
    current meteo data. Used for the first collection of the storico.
    """
    def load(self)->List[dict]:
        if os.path.exists('storico_meteo.json'):
            with open("storico_meteo.json", "r") as file:
                storico = json.load(file)
                file.close()
            return storico
        else:
            self.first_update()
            return self.load()

    def first_update(self):
        print("File not found, created 'storico_meteo.json' and first update")
        obs = (GetMeteoData().fetching_current_meteo_json())
        with open("storico_meteo.json", "w") as file:
            json.dump(obs, file, indent=4)

    def update(self)->None:
        storico = self.load()
        new_obs = (GetMeteoData().fetching_current_meteo_json())
        update = storico + new_obs # must optimize this process
        with open("storico_meteo.json", "w") as file:
            json.dump(update, file, indent=4)
#############################################################################################
class JsonManagerCurrentRadiation():
    """
    Manager created to deal the JSON operation as save and load for
    current radiation data. Used for the first collection of the storico.
    """
    def load(self)->List[dict]:
        if os.path.exists('storico_radiation.json'):
            with open("storico_radiation.json", "r") as file:
                storico = json.load(file)
                file.close()
            return storico
        else:
            self.first_update()
            return self.load()

    def first_update(self):
        print("File not found, created 'storico_radiation.json' and first update")
        obs = (GetMeteoData().fetching_current_solar_radiation())
        with open("storico_radiation.json", "w") as file:
            json.dump(obs, file, indent=4)

    def update(self)->None:
        storico = self.load()
        new_obs = (GetMeteoData().fetching_current_solar_radiation())
        update = storico + new_obs # must optimize this process
        with open("storico_radiation.json", "w") as file:
            json.dump(update, file, indent=4)
#############################################################################################
class ForecastData():
    def update_forecast_radiation(self):
        tmp = []
        datas = GetMeteoData().fetching_forecast_solar_radiation()
        for data in datas:
            city = MeteoRadiationData.forecast_from_dict_to_class(data)
            for obs in city:
                tmp.append(obs.current_from_class_to_dict())
        df=pd.DataFrame(tmp)
        df.sort_values(by="date", ascending=False, inplace=True)
        # df.to_csv("forecast_solar_radiation.csv", index=False)
        return df

    def update_forecast_meteo(self):
        res = []
        forecast = GetMeteoData().fetching_forecast_meteo()
        for city in forecast:
            tmp = MeteoData.forecast_from_dict_to_class(city)
            for hour in tmp:
                obj = hour.from_class_to_dict()
                res.append(obj)
        df = pd.DataFrame(res)
        df.sort_values(by="date", inplace=True)
        # df.to_csv("forecast_meteo.csv", index=False)
        return df

    def merge_forecast(self,):
        meteo=ForecastData().update_forecast_meteo()
        radiation=ForecastData().update_forecast_radiation()
        final = pd.merge(meteo, radiation[
            ['name', 'date', 'globalhorizontalirradiance', 'directnormalirradiance',
             'diffusehorizontalirradiance', 'globalhorizontalirradiance_2',
             'directnormalirradiance_2', 'diffusehorizontalirradiance_2']],
                         on=["date", "name"], how='left')

        final.drop(columns=["cross_join"], inplace=True)
        # final.to_csv("new_forecast_obs.csv", index=False)
        return final


def into_the_loop_json():
    """
    General function to start the operations and collect data.
    """
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

def load_energy_load()->None:
    listu = os.listdir("files/load_terna")
    listu = ["files/load_terna/"+path for path in listu]
    ManagerTernaSql().load_from_terna_and_holiday(listu,"files/italian-holiday-calendar.csv")
def load_energy_generation()->None:
    ManagerTernaSql().generation_from_terna_to_db("files/generation_terna/renawable_production.csv")
def load_energy_capacity()->None:
    ManagerTernaSql().load_energy_installed_capacity("files/installed_capacity.csv")



if __name__ == "__main__":
    print("im fine")
