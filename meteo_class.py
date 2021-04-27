from pprint import pprint
from typing import List
from tqdm import tqdm
import typing, json, time



class MeteoCurrentData():
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
        return str(self.name + " " + str(self.date) + " class= "+str(type(self)))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is not MeteoCurrentData:
            raise TypeError("You are not comparing two MeteoCurrentData object!")
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
        return MeteoCurrentData(
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

class MeteoCurrentRadiationData():
    def __init__(self, name, date, cross_join, globalhorizontalirradiance, directnormalirradiance, diffusehorizontalirradiance,
                 globalhorizontalirradiance_2, directnormalirradiance_2, diffusehorizontalirradiance_2):
        ## General
        self.name = name
        self.date = date
        self.cross_join = cross_join
        ## Cloud Sky
        self.globalhorizontalirradiance = globalhorizontalirradiance
        self.directnormalirradiance = directnormalirradiance
        self.diffusehorizontalirradiance = diffusehorizontalirradiance
        ## Clear Sky
        self.globalhorizontalirradiance_2 = globalhorizontalirradiance_2
        self.directnormalirradiance_2 = directnormalirradiance_2
        self.diffusehorizontalirradiance_2 = diffusehorizontalirradiance_2

    def __str__(self):
        return str(self.name + " " + str(self.date)+ " class= "+str(type(self)))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is not MeteoCurrentRadiationData:
            raise TypeError("You are not comparing two MeteoCurrentRadiationData object!")
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
            'globalhorizontalirradiance': self.globalhorizontalirradiance,
            'directnormalirradiance': self.directnormalirradiance,
            'diffusehorizontalirradiance': self.diffusehorizontalirradiance,
            'globalhorizontalirradiance_2': self.globalhorizontalirradiance_2,
            'directnormalirradiance_2': self.directnormalirradiance_2,
            'diffusehorizontalirradiance_2':self.diffusehorizontalirradiance_2,
        })


    @staticmethod
    def from_dict_to_class(obj:dict):
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["list"][0]["dt"]))
        return MeteoCurrentRadiationData(
            name=obj["name"],
            date= obj["organized_data"],
            cross_join=obj["cross_join"],
            globalhorizontalirradiance= obj["list"][0]["radiation"]["ghi"],
            directnormalirradiance= obj["list"][0]["radiation"]["dni"],
            diffusehorizontalirradiance= obj["list"][0]["radiation"]["dhi"],
            globalhorizontalirradiance_2= obj["list"][0]["radiation"]["ghi_cs"],
            directnormalirradiance_2=obj["list"][0]["radiation"]["dni_cs"],
            diffusehorizontalirradiance_2= obj["list"][0]["radiation"]["dhi_cs"]
        )


class MeteoForecastData():
    def __init__(self, date, name, region, clouds, text_description,
                 pressure, humidity, temp, wind_deg, wind_speed, rain_1h=0, snow_1h=0):
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
        self.snow_1h = snow_1h
        self.wind_deg = wind_deg
        self.wind_speed = wind_speed

    def __str__(self):
        return str(self.name + " " + str(self.date) + " class= "+str(type(self)))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is not MeteoForecastData:
            raise TypeError("You are not comparing two MeteoCurrentData object!")
        else:
            return self.__str__() == other.__str__()

    @staticmethod
    def from_dict_to_class(obj: dict, rain=0, snow=0):
        res = []
        hours_48 = obj["hourly"]
        for hour in hours_48:
            if 'rain' in hour: rain = hour['rain']["1h"]
            if 'snow' in hour: snow = hour["snow"]["1h"]
            original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
            res.append(MeteoForecastData(
                name=obj["name"],
                date=original_dt,
                region=obj["region"],
                clouds=hour["clouds"],
                text_description=hour["weather"][0]["description"],
                pressure=hour["pressure"],
                humidity=hour["humidity"],
                temp=hour["temp"],
                rain_1h=rain,
                snow_1h=snow,
                wind_deg=hour["wind_deg"],
                wind_speed=hour["wind_speed"],
            ))
        return res


