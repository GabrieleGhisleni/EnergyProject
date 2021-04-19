import requests, time, datetime, json
from pprint import pprint
from typing import List


class GetMeteoData():
    def dict_regions(self) -> dict:

        " Returns a dictionary having as key the regions divided by Terna\
        and having as values all the capoluoghi of that region.           "

        nord = ['Aosta','Genova','Torino','Milano','Trento','Venezia','Bologna','Trieste']
        centro_nord = ['Perugia','Firenze','Ancona']
        centro_sud = ['Aquila','Roma','Aquila','Roma','Campobasso']
        sud = ['Napoli','Bari','Potenza']
        sicilia = ['Palermo']
        sardegna = ['Sardegna']
        calabria = ['Catanzaro']
        return dict(nord=nord, centro_nord=centro_nord, centro_sud=centro_sud,
                    sud=sud, sicilia=sicilia,sardegna=sardegna, calabria=calabria)

    def organize_date(self) -> str:

        "since AWS works with different timezone (-2 hours) it returns the data\
        already as string with the same format as Terna Data"

        return (datetime.datetime.now()+datetime.timedelta(hours=2)).strftime("%d/%m/%Y %H:%M:%S %p")

    def fetching_current_meteo_json(self)-> List[dict]:

        "fetch all the meteo data from the regions, return a list of dict aka json"

        res = []
        regions = self.dict_regions()
        current_time = self.organize_date()
        for regione in regions:
            for capoluogo in regions[regione]:
                try:
                    url = " https://api.openweathermap.org/data/2.5/weather?appid=a054032d5e094190a9eba85b70421ff3&units=metric&q={},it".format(capoluogo)
                    response = requests.request("GET", url)
                    if not response.ok:
                        print ("Something wrong with the respunsus ok API" + str(response) + "at " + capoluogo)
                        pass
                    else:
                        tmp = response.json()
                        tmp["region"] = regione
                        tmp["organized_data"] = current_time
                        res.append(tmp)
                except Exception: #done so the program won't crash if something go wrong.
                    print(" --> Fatal error with the requests connection <-- ")
        return res


class JsonManagerMeteo():
    def load(self)->List[dict]:

        " try except to handle the first run. \
        the function load all the JSON file "

        try:
            with open("storico_meteo.json", "r") as file:
                storico = json.load(file)
                file.close()
            return storico
        except Exception:
            with open("storico_meteo.json", "w") as file:
                print("File not found, created 'storico_meteo.json'.")
                self.first_load()
                return self.load()

    def first_load(self):
        print("First Load.")
        obs = (GetMeteoData().fetching_current_meteo_json())
        with open("storico_meteo.json", "w") as file:
            json.dump(obs, file, indent=4)

    def update(self)->None:
        storico = self.load()
        new_obs = (GetMeteoData().fetching_current_meteo_json())
        update = storico + new_obs # must optimize this process
        with open("storico_meteo.json", "w") as file:
            json.dump(update, file, indent=4)


if __name__ == "__main__":
    manager = JsonManagerMeteo()
    while True:
        if str(datetime.datetime.now().time().minute).endswith('0')\
            or str(datetime.datetime.now().time().minute).endswith('5'):
                manager.update()
                time.sleep(290)



