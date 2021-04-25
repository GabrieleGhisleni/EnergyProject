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

        "fetch all the meteo data from the regions, return a list of dict aka json\
        it collect the data from the API as dictionary and insert them all into a list\
        so the function return a list of dictionary, each dictionary is a registration\
        for a particular capoluogo                                                   "

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



if __name__ == "__main__":
    print("i'm fine")





