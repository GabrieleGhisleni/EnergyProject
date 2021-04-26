import requests, time, datetime, json, copy
from pprint import pprint
from typing import List


class GetMeteoData():
    def __init__(self):
        self.coordinates= {'Bari': {'lat': 41.1177, 'lon': 16.8512},
                     'Bologna': {'lat': 44.4667, 'lon': 11.4333},
                     'Catanzaro': {'lat': 38.8908, 'lon': 16.5987},
                     'Florence': {'lat': 43.7667, 'lon': 11.25},
                     "L'Aquila": {'lat': 42.365, 'lon': 13.3935},
                     'Milan': {'lat': 45.4643, 'lon': 9.1895},
                     'Naples': {'lat': 40.8333, 'lon': 14.25},
                     'Potenza': {'lat': 40.6443, 'lon': 15.8086},
                     'Province of Palermo': {'lat': 37.8167, 'lon': 13.5833},
                     'Province of Turin': {'lat': 45.1333, 'lon': 7.3667},
                     'Provincia di Ancona': {'lat': 43.55, 'lon': 13.1667},
                     'Provincia di Campobasso': {'lat': 41.6333, 'lon': 14.5833},
                     'Provincia di Genova': {'lat': 44.5, 'lon': 9.0667},
                     'Provincia di Perugia': {'lat': 43.05, 'lon': 12.55},
                     'Rome': {'lat': 41.8947, 'lon': 12.4839},
                     'Sardinia': {'lat': 40, 'lon': 9},
                     'Trento': {'lat': 46.0679, 'lon': 11.1211},
                     'Trieste': {'lat': 45.6486, 'lon': 13.78},
                     "Valle d'Aosta": {'lat': 45.7667, 'lon': 7.4167},
                     'Venice': {'lat': 45.4386, 'lon': 12.3267}}


        nord = ['Aosta','Genova','Torino','Milano','Trento','Venezia','Bologna','Trieste']
        centro_nord = ['Perugia','Firenze','Ancona']
        centro_sud = ['Aquila','Roma','Aquila','Roma','Campobasso']
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
                except Exception: #done so the program won't crash if something go wrong.
                    print(" --> Fatal error with the requests connection <-- ")
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
            except Exception:  # done so the program won't crash if something go wrong.
                print(" --> Fatal error with the requests connection <-- ")
        return res

    def fetching_forecast_meteo(self):
        coordinates = self.coordinates
        cross_join_detail = datetime.datetime.now().strftime("%d/%m/%Y %H:%M %p")
        res = []
        for citta in coordinates:
            try:
                url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&units=metric&exclude=minutely,current,daily,alerts&appid=a054032d5e094190a9eba85b70421ff3".format(coordinates[citta]["lat"],coordinates[citta]["lon"])
                response = requests.request("GET", url)
                if not response.ok:
                    print("Something wrong with the respunsus ok API" + str(response) + "at " + citta)
                    pass
                else:
                    tmp = response.json()
                    tmp["cross_join"] = cross_join_detail
                    for hour in tmp["hourly"]:
                        hour["orario"] = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
                    res.append(tmp)
            except Exception:  # done so the program won't crash if something go wrong.
                print(" --> Fatal error with the requests connection <-- ")
        return res

if __name__ == "__main__":
    print(datetime.datetime.now())
    pprint(GetMeteoData().fetching_current_meteo_json()[0])
    pprint(GetMeteoData().fetching_current_meteo_json()[0])
    print(datetime.datetime.now())

