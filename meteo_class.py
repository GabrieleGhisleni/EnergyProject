from pprint import pprint
from typing import List, Optional, Type
from tqdm import tqdm
import typing, json, time


class MeteoRadiationData():
    """
    class created to handle the current radiation data.
    """
    def __init__(self, name, date, region,  globalhorizontalirradiance, directnormalirradiance, diffusehorizontalirradiance,
                 globalhorizontalirradiance_2, directnormalirradiance_2, diffusehorizontalirradiance_2, cross_join=None):
        ## General
        self.name = name
        self.date = date
        self.cross_join = cross_join
        self.region = region
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
        if other is not MeteoRadiationData:
            raise TypeError("You are not comparing two MeteoRadiationData object!")
        else:
            return self.__str__() == other.__str__()

    def print_all(self):
        return str(self.current_from_class_to_dict())

    def __iter__(self):
        for key,value in self.current_from_class_to_dict().items():
            yield key,value

    def current_from_class_to_dict(self):
        return({
            'name':self.name,
            'date': self.date,
            'region': self.region,
            'cross_join': self.cross_join,
            'globalhorizontalirradiance': self.globalhorizontalirradiance,
            'directnormalirradiance': self.directnormalirradiance,
            'diffusehorizontalirradiance': self.diffusehorizontalirradiance,
            'globalhorizontalirradiance_2': self.globalhorizontalirradiance_2,
            'directnormalirradiance_2': self.directnormalirradiance_2,
            'diffusehorizontalirradiance_2':self.diffusehorizontalirradiance_2,
        })



    @staticmethod
    def current_from_dict_to_class(obj:dict):
        """
        This function has to be applied on a single call from the forecast radiation.
        So for each city one call.
        """
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["list"][0]["dt"]))
        return MeteoRadiationData(
            name=obj["name"],
            date= obj["organized_data"],
            cross_join=obj["cross_join"],
            region= obj["region"],
            globalhorizontalirradiance= obj["list"][0]["radiation"]["ghi"],
            directnormalirradiance= obj["list"][0]["radiation"]["dni"],
            diffusehorizontalirradiance= obj["list"][0]["radiation"]["dhi"],
            globalhorizontalirradiance_2= obj["list"][0]["radiation"]["ghi_cs"],
            directnormalirradiance_2=obj["list"][0]["radiation"]["dni_cs"],
            diffusehorizontalirradiance_2= obj["list"][0]["radiation"]["dhi_cs"])

    @staticmethod
    def forecast_from_dict_to_class(obj: dict, rain=0, snow=0):
        """
        obj is the forecast meteo for one city!
        This function has to be applied on a single call from the forecast meteo.
        So for each city one call and it will return a list of dict, each dict will have
        the forecast meteo for that city and the next 48 hour.
        """
        res = []
        hours_3dayplus = obj["list"]
        for hour in hours_3dayplus:
            res.append(MeteoRadiationData(
                name=obj["name"],
                date=hour["date"],
                region=obj["region"],
                globalhorizontalirradiance= hour["radiation"]["ghi"],
                directnormalirradiance= hour["radiation"]["dni"],
                diffusehorizontalirradiance=hour["radiation"]["dhi"],
                globalhorizontalirradiance_2=hour["radiation"]["ghi_cs"],
                directnormalirradiance_2= hour["radiation"]["ghi_cs"],
                diffusehorizontalirradiance_2=hour["radiation"]["ghi_cs"],
            ))
        return res


class MeteoData():
    """
    class created to handle the meteo data.
    """
    def __init__(self, date, name, region, clouds, text_description,
                 pressure, humidity, temp, wind_deg, wind_speed,
                  rain_1h=0, snow_1h=0,cross_join=None):
        ## General info
        self.date = date
        self.name = name
        self.cross_join = cross_join #use only in current to cross_join with solar
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

    def __str__(self):
        return str(self.name + " " + str(self.date) + " class= "+str(type(self)))

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
            'wind_speed': self.wind_speed
        })


    @staticmethod
    def current_from_dict_to_class(obj:dict, rain=0, snow=0):
        """
        This function has to be applied on a single call from the current data.
        So for each city one call and it will return an object MeteoCurrentData.
        """
        if 'rain' in obj: rain = obj['rain']
        if 'snow' in obj: snow=obj["snow"]
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
            wind_speed= obj["wind"]["speed"])

    @staticmethod
    def forecast_from_dict_to_class(obj: dict, rain=0, snow=0):
        """
        obj is the forecast meteo for one city!
        This function has to be applied on a single call from the forecast meteo.
        So for each city one call and it will return a list of dict, each dict will have
        the forecast meteo for that city and the next 48 hour.
        """
        res = []
        hours_48 = obj["hourly"]
        for hour in hours_48:
            if 'rain' in hour: rain = hour['rain']["1h"]
            if 'snow' in hour: snow = hour["snow"]["1h"]
            original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
            res.append(MeteoData(
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

if __name__ == "__main__":
    print("i'm fine")