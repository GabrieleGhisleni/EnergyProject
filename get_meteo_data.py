import requests, time, datetime, json, copy
from pprint import pprint
from typing import List
from tqdm import tqdm

class GetMeteoData():
    def __init__(self):
        self.coordinates= {'Bari': {'lat': 41.1177, 'lon': 16.8512, 'region':'sud'},
                     'Bologna': {'lat': 44.4667, 'lon': 11.4333,'region':'nord'},
                     'Catanzaro': {'lat': 38.8908, 'lon': 16.5987,'region':'calabria'},
                     'Florence': {'lat': 43.7667, 'lon': 11.25,'region':'centro_nord'},
                     "L'Aquila": {'lat': 42.365, 'lon': 13.3935,'region':'centro_sud'},
                     'Milan': {'lat': 45.4643, 'lon': 9.1895,'region':'nord'},
                     'Naples': {'lat': 40.8333, 'lon': 14.25,'region':'sud'},
                     'Potenza': {'lat': 40.6443, 'lon': 15.8086,'region':'sud'},
                     'Province of Palermo': {'lat': 37.8167, 'lon': 13.5833,'region':'sicilia'},
                     'Province of Turin': {'lat': 45.1333, 'lon': 7.3667,'region':'nord'},
                     'Provincia di Ancona': {'lat': 43.55, 'lon': 13.1667,'region':'centro_nord'},
                     'Provincia di Campobasso': {'lat': 41.6333, 'lon': 14.5833,'region':'centro_sud'},
                     'Provincia di Genova': {'lat': 44.5, 'lon': 9.0667,'region':'nord'},
                     'Provincia di Perugia': {'lat': 43.05, 'lon': 12.55,'region':'centro_nord'},
                     'Rome': {'lat': 41.8947, 'lon': 12.4839,'region':'centro_sud'},
                     'Sardinia': {'lat': 40, 'lon': 9,'region':'sardegna'},
                     'Trento': {'lat': 46.0679, 'lon': 11.1211,'region':'nord'},
                     'Trieste': {'lat': 45.6486, 'lon': 13.78,'region':'nord'},
                     "Valle d'Aosta": {'lat': 45.7667, 'lon': 7.4167,'region':'nord'},
                     'Venice': {'lat': 45.4386, 'lon': 12.3267,'region':'nord'}}


        nord = ['Aosta','Genova','Torino','Milano','Trento','Venezia','Bologna','Trieste']
        centro_nord = ['Perugia','Firenze','Ancona']
        centro_sud = ['Aquila','Roma','Campobasso']
        sud = ['Napoli','Bari','Potenza']
        sicilia = ['Palermo']
        sardegna = ['Sardegna']
        calabria = ['Catanzaro']
        tmp = dict(nord=nord, centro_nord=centro_nord, centro_sud=centro_sud,
                    sud=sud, sicilia=sicilia,sardegna=sardegna, calabria=calabria)

        self.dictionary= tmp

    def fetching_current_meteo_json(self)-> List[dict]:

        "fetch all the meteo data from the regions, return a list of dict aka json\
        it collect the data from the API as dictionary and insert them all into a list\
        so the function return a list of dictionary, each dictionary is a registration\
        for a particular capoluogo                                                   "

        res = []
        regions = self.dictionary
        cross_join_detail = datetime.datetime.now().strftime("%d/%m/%Y %H:%M %p")
        current_time = False
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
                        if not current_time:
                            current_time = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(tmp["dt"]))
                        tmp["region"] = regione
                        tmp["organized_data"] = current_time
                        tmp["cross_join"] = cross_join_detail
                        res.append(tmp)
                except Exception as e:  # done so the program won't crash if something go wrong.
                    print("\n --> Fatal error with the requests connection <--")
                    print(str(e))
        return res

    def find_coordinate(self):
        tmp = {}
        for row in (GetMeteoData().fetching_current_meteo_json()):
            tmp[row["name"]] = dict(lat=row["coord"]["lat"], lon=row["coord"]["lon"])
        return tmp

    def fetching_solar_radiation(self):
        coordinates = self.coordinates
        current_time = False
        cross_join_detail = datetime.datetime.now().strftime("%d/%m/%Y %H:%M %p")
        res = []
        for citta in coordinates:
            try:
                url = "http://api.openweathermap.org/data/2.5/solar_radiation?lat={}&lon={}&appid=a054032d5e094190a9eba85b70421ff3".format(coordinates[citta]["lat"],coordinates[citta]["lon"])
                response = requests.request("GET", url)
                if not response.ok:
                    print("Something wrong with the respunsus ok API" + str(response) + "at " + citta)
                    pass
                else:
                    tmp = response.json()
                    tmp["cross_join"] = cross_join_detail
                    if not current_time:
                        current_time= time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(tmp["list"][0]["dt"]))
                    tmp["organized_data"] = current_time
                    tmp["name"] = citta
                    res.append(tmp)
            except Exception as e:  # done so the program won't crash if something go wrong.
                print("\n --> Fatal error with the requests connection <--")
                print(str(e))
        return res

    def fetching_forecast_meteo(self):
        coordinates = self.coordinates
        res = []
        for citta in tqdm(coordinates):
            try:
                url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=minutely,current,daily,alerts&appid=a054032d5e094190a9eba85b70421ff3".format(coordinates[citta]["lat"],coordinates[citta]["lon"])
                response = requests.request("GET", url)
                if not response.ok:
                    print("Something wrong with the respunsus ok API" + str(response) + "at " + citta)
                    pass
                else:
                    tmp = response.json()
                    tmp["region"] = coordinates[citta]["region"]
                    tmp["name"] = citta
                    for hour in tmp["hourly"]:
                        hour["orario"] = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
                    res.append(tmp)
            except Exception as e:  # done so the program won't crash if something go wrong.
                print("\n --> Fatal error with the requests connection <--")
                print(str(e))
        return res

if __name__ == "__main__":
    print(datetime.datetime.now())
    print(GetMeteoData().fetching_forecast_meteo()[0])
    print(datetime.datetime.now())

