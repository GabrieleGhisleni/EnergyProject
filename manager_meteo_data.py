import json, time, datetime,os
from typing import List
from get_meteo_data import *
from meteo_class import *
import pandas as pd

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

class CSVForecastSolarRadiation():
    def update_csv(self):
        tmp = []
        datas = GetMeteoData().fetching_forecast_solar_radiation()
        for data in datas:
            city = MeteoRadiationData.forecast_from_dict_to_class(data)
            for obs in city:
                tmp.append(obs.current_from_class_to_dict())
        #df= df.append(tmp, ignore_index=True)
        df=pd.DataFrame(tmp)
        df.sort_values(by="date", ascending=False, inplace=True)
        df.to_csv("forecast_solar_radiation.csv", index=False)
        return df

class CSVForecastMeteo():
    def update_csv(self):
        res = []
        forecast = GetMeteoData().fetching_forecast_meteo()
        for city in forecast:
            tmp = MeteoData.forecast_from_dict_to_class(city)
            for hour in tmp:
                obj = hour.from_class_to_dict()
                res.append(obj)
        df = pd.DataFrame(res)
        df.sort_values(by="date", inplace=True)
        df.to_csv("forecast_meteo.csv", index=False)
        return df



def into_the_loop():
    """
    General function to start the operations and collect data.
    """
    manager = JsonManagerCurrentMeteo()
    manager_2 = JsonManagerCurrentRadiation()
    while True:
        if str(datetime.datetime.now().time().minute).endswith('00')\
            or str(datetime.datetime.now().time().minute).endswith('15')\
                or str(datetime.datetime.now().time().minute).endswith('30')\
                or str(datetime.datetime.now().time().minute).endswith('45'):
                    manager.update()
                    manager_2.update()
                    time.sleep(890)
                    print("done")



if __name__ == "__main__":
    print("i'm fine")