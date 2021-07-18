from __future__ import annotations
from typing import List
import time
import pandas as pd
from pandas import DataFrame as PandasDataFrame

class MeteoData:
    """
    Class created to deal and organize the raw data coming from
    the GetMeteoData class which handle the API requests.
    It requires some parameters that are all found inside
    the response of the API. Since it could be the case that
    rain or snow is not present we preventatively set it to 0.
    We also create a cross_join attribute that will be used
    to merge those data with the generation data from Terna.
    """
    def __init__(self, date, name, clouds, pressure, humidity, temp, wind_deg, wind_speed, rain_1h=0, snow_1h=0, cross_join=None):
        self.date = date
        self.name = name
        self.cross_join = cross_join
        self.clouds = clouds
        self.pressure = pressure
        self.humidity = humidity
        self.temp = temp
        self.rain_1h = rain_1h
        self.snow_1h = snow_1h
        self.wind_deg = wind_deg
        self.wind_speed = wind_speed

    def __str__(self):
        return str(self.name + " " + str(self.cross_join) + " class= "+str(type(self)))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, MeteoData): raise TypeError("You are not comparing two MeteoData object!")
        else: return self.__str__() == other.__str__()

    def __iter__(self):
        for key, value in self.from_class_to_dict().items():
            yield key, value

    def print_all(self) -> str:
        return str(self.from_class_to_dict())

    def from_class_to_dict(self) -> dict:
        """
        Take an object and return a well defined dictionary.
        """
        return({
            'name': self.name,
            'date': self.date,
            'cross_join': self.cross_join,
            'clouds': self.clouds,
            'pressure': self.pressure,
            'humidity': self.humidity,
            'temp': self.temp,
            'rain_1h': self.rain_1h,
            'snow_1h': self.snow_1h,
            'wind_deg': self.wind_deg,
            'wind_speed': self.wind_speed
        })

    @staticmethod
    def current_from_original_dict_to_class(obj: dict, rain: int = 0, snow: int = 0) -> MeteoData:
        """
        It takes the dictionary as it arrives from the current weather API
        it turns it into an object of the class MeteoData.
        """
        if 'rain' in obj: rain = obj['rain']["1h"]
        if 'snow' in obj: snow = obj["snow"]['1h']
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["dt"]))
        if ":01" in obj["cross_join"] or ":59" in obj["cross_join"]:
            o_c = obj["cross_join"]
            cross_join = o_c.split(" ")[0]+" " + o_c.split(" ")[1].split(":")[0] + ":" + "00 " + o_c.split(" ")[2]
        else: cross_join = obj["cross_join"]
        return MeteoData(
            name=obj["name"],
            date=original_dt,
            clouds=obj["clouds"]["all"],
            cross_join=cross_join,
            pressure=obj["main"]["pressure"],
            humidity=obj["main"]["humidity"],
            temp=obj["main"]["temp"],
            rain_1h=rain,
            snow_1h=snow,
            wind_deg=obj["wind"]["deg"],
            wind_speed=obj["wind"]["speed"])

    @staticmethod
    def current_from_preprocess_dict_to_class(obj: dict, rain: int = 0, snow: int = 0) -> MeteoData:
        """
        It takes the dictionary that as already been processed
        and turns it again into an object of the class MeteoData.
        """
        if 'rain' in obj: rain = obj['rain_1h']
        if 'snow' in obj: snow = obj["snow_1h"]
        return MeteoData(
            name=obj["name"],
            date=obj["date"],
            clouds=obj["clouds"],
            cross_join=obj["cross_join"],
            pressure=obj["pressure"],
            humidity=obj["humidity"],
            temp=obj["temp"],
            rain_1h=rain,
            snow_1h=snow,
            wind_deg=obj["wind_deg"],
            wind_speed=obj["wind_speed"])

    @staticmethod
    def forecast_from_dict_to_class(city: List[dict], rain: int = 0, snow: int = 0) -> List[List[MeteoData]]:
        """
        It takes the raw data from the Forecast API call, which are encoded
        as a list of dictionary (one list represent one city, containing 48 obs)
        and return a list of list of MeteoData.
        """
        tmp = []
        for obj in city:
            res = []
            hours_48 = obj["hourly"]
            for hour in hours_48:
                if 'rain' in hour: rain = hour['rain']["1h"]
                if 'snow' in hour: snow = hour["snow"]["1h"]
                original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
                res.append(MeteoData(
                    name=obj["name"],
                    date=original_dt,
                    clouds=hour["clouds"],
                    pressure=hour["pressure"],
                    humidity=hour["humidity"],
                    temp=hour["temp"],
                    rain_1h=rain,
                    snow_1h=snow,
                    wind_deg=hour["wind_deg"],
                    wind_speed=hour["wind_speed"],
                ))
            tmp.append(res)
        return tmp

    @staticmethod
    def update_forecast_meteo(forecast_meteo: List[List[MeteoData]]) -> PandasDataFrame:
        """
        Helper functions that takes the preprocess forecast weather as
        a list of list of MeteoData and prepare a PandasDataFrame to
        be passed in the next steps of the pipelines.
        """
        res = []
        for city in forecast_meteo:
            for hour in city:
                obj = hour.from_class_to_dict()
                res.append(obj)
        df = pd.DataFrame(res)
        df.sort_values(by="date", inplace=True)
        res = df.groupby('date').mean().reset_index()
        dates = pd.to_datetime(res["date"], format='%d/%m/%Y %H:%M:%S %p')
        res["str_hour"] = dates.dt.strftime("%H %p")
        res["str_month"] = dates.dt.strftime("%B")
        res["str_month"] = res["str_month"].str.lower()
        res = res.sort_values(by="date")
        res["date"] = dates.dt.strftime('%Y/%m/%d %H:%M:%S')
        return res
