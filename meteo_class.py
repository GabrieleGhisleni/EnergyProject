from pprint import pprint
from typing import List
from tqdm import tqdm
import typing, json, time

class MeteoData():
    def __init__(self, date, name, cross_join, region, clouds, text_description,
                 pressure, humidity, temp, wind_deg, wind_speed,
                 sunrise, sunset, rain_1h=0, snow_1h=0):
        ## General info
        self.date = date
        self.name = name
        self.cross_join = cross_join
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
            'cross_join': self.cross_join,
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
            cross_join=obj["cross_join"],
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

class MeteoRadiationData():
    def __init__(self, name, date, cross_join, GlobalHorizontalIrradiance, DirectNormalIrradiance, DiffuseHorizontalIrradiance,
                 GlobalHorizontalIrradiance_2, DirectNormalIrradiance_2, DiffuseHorizontalIrradiance_2):
        ## General
        self.name = name
        self.date = date
        self.cross_join = cross_join
        ## Cloud Sky
        self.GlobalHorizontalIrradiance = GlobalHorizontalIrradiance
        self.DirectNormalIrradiance = DirectNormalIrradiance
        self.DiffuseHorizontalIrradiance = DiffuseHorizontalIrradiance
        ## Clear Sky
        self.GlobalHorizontalIrradiance_2 = GlobalHorizontalIrradiance_2
        self.DirectNormalIrradiance_2 = DirectNormalIrradiance_2
        self.DiffuseHorizontalIrradiance_2 = DiffuseHorizontalIrradiance_2

    def __str__(self):
        return str(self.name + " " + str(self.date))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is not MeteoRadiationData:
            raise TypeError("You are not comparing two MeteoRadiationData object!")
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
            'cross_join': self.cross_join,
            'GlobalHorizontalIrradiance': self.GlobalHorizontalIrradiance,
            'DirectNormalIrradiance': self.DirectNormalIrradiance,
            'DiffuseHorizontalIrradiance': self.DiffuseHorizontalIrradiance,
            'GlobalHorizontalIrradiance_2': self.GlobalHorizontalIrradiance_2,
            'DirectNormalIrradiance_2': self.DirectNormalIrradiance_2,
            'DiffuseHorizontalIrradiance_2':self.DiffuseHorizontalIrradiance_2,
        })


    @staticmethod
    def from_dict_to_class(obj:dict):
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["list"][0]["dt"]))
        return MeteoRadiationData(
            name=obj["name"],
            date= obj["organized_data"],
            cross_join=obj["cross_join"],
            GlobalHorizontalIrradiance= obj["list"][0]["radiation"]["ghi"],
            DirectNormalIrradiance= obj["list"][0]["radiation"]["dni"],
            DiffuseHorizontalIrradiance= obj["list"][0]["radiation"]["dhi"],
            GlobalHorizontalIrradiance_2= obj["list"][0]["radiation"]["ghi_cs"],
            DirectNormalIrradiance_2=obj["list"][0]["radiation"]["dni_cs"],
            DiffuseHorizontalIrradiance_2= obj["list"][0]["radiation"]["dhi_cs"]
        )

