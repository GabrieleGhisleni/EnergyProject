from pprint import pprint
from typing import List
from tqdm import tqdm
import typing, json, time

class MeteoData():
    def __init__(self, date, name, region, clouds, text_description,
                 pressure, humidity, temp, wind_deg, wind_speed,
                 sunrise, sunset, rain_1h=0, snow_1h=0):
        ## General info
        self.date = date
        self.name = name
        self.region = region
        ## Meteo general description
        self.clouds = clouds
        self.text_description = text_description
        ## Meteo main
        self.pressure = pressure
        self.humidity = humidity
        self.temp = temp
        ## Meteo rain-snow-wind
        self.rain_1h = rain_1h
        self.snow_1h= snow_1h
        self.wind_deg = wind_deg
        self.wind_speed = wind_speed
        ## Meteo sunset-sunrise
        self.sunrise = sunrise
        self.sunset = sunset

    def __str__(self):
        return str(self.name + " " + str(self.date))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is not MeteoData:
            raise TypeError("You are not comparing two MeteoData object!")
        else:
            return self.__str__() == other.__str__()

    def print_all(self):
        return str(self.from_class_to_dict())

    def __iter__(self):
        for key,value in self.from_class_to_dict().items():
            yield key,value

    def from_class_to_dict(self):
        return({
            'name':self.name,
            'date': self.date,
            'region': self.region,
            'clouds': self.clouds,
            'text_description': self.text_description,
            'pressure': self.pressure,
            'humidity': self.humidity,
            'temp': self.temp,
            'rain_1h':self.rain_1h,
            'snow_1h': self.snow_1h,
            'wind_deg': self.wind_deg,
            'wind_speed': self.wind_speed,
            'sunrise': self.sunrise,
            'sunset': self.sunset,
        })


    @staticmethod
    def from_dict_to_class(obj:dict, rain=0, snow=0):
        if 'rain' in obj: rain = obj['rain']
        if 'snow' in obj: snow=obj["snow"]
        sunrise =  time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["sys"]["sunrise"]))
        sunset =  time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["sys"]["sunset"]))
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["dt"]))
        return MeteoData(
            name = obj["name"],
            date = original_dt,
            region = obj["region"],
            clouds = obj["clouds"]["all"],
            text_description = obj["weather"][0]["description"],
            pressure= obj["main"]["pressure"],
            humidity= obj["main"]["humidity"],
            temp = obj["main"]["temp"],
            rain_1h = rain,
            snow_1h = snow,
            wind_deg= obj["wind"]["deg"],
            wind_speed= obj["wind"]["speed"],
            sunset = sunset,
            sunrise= sunrise
        )


def check_all_the_features(file=List[dict]):
    """ print out all the possible features found the API."""
    res = {}
    for station in file:
        for key in station:
            if key not in res:
                res[key] = station[key]
            else:
                pass
            if type(station[key]) == dict:
                for detail in station[key]:
                    if detail not in res[key]:
                        res[key][detail] = station[key][detail]
    pprint(res)


