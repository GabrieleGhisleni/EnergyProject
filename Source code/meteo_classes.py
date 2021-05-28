from pprint import pprint
from typing import List, Optional, Type
from tqdm import tqdm
import typing, json, time
import pandas as pd
###################################################################################################################

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
    def current_from_preprocess_dict_to_class(obj:dict):
        """
        This function has to be applied on a single call from the forecast radiation.
        So for each city one call.
        """
        return MeteoRadiationData(
            name=obj["name"],
            date= obj["date"],
            cross_join=obj["cross_join"],
            region= obj["region"],
            globalhorizontalirradiance= obj["globalhorizontalirradiance"],
            directnormalirradiance= obj["directnormalirradiance"],
            diffusehorizontalirradiance= obj["diffusehorizontalirradiance"],
            globalhorizontalirradiance_2= obj["globalhorizontalirradiance_2"],
            directnormalirradiance_2=obj["directnormalirradiance_2"],
            diffusehorizontalirradiance_2= obj["diffusehorizontalirradiance_2"])

    @staticmethod
    def current_from_original_dict_to_class(obj:dict):
        """
        This function has to be applied on a single call from the forecast radiation.
        So for each city one call.
        """
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
    def forecast_from_dict_to_class(city: List[dict]):
        """
        obj is the forecast meteo for one city!
        This function has to be applied on a single call from the forecast meteo.
        So for each city one call and it will return a list of dict, each dict will have
        the forecast meteo for that city and the next 48 hour.
        """
        tmp = []
        for obj in city:
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
            tmp.append(res)

        return tmp

###################################################################################################################
class MeteoData():
    """
    class created to handle the meteo data!
    """
    def __init__(self, date, name,clouds, pressure, humidity,
                 temp, wind_deg, wind_speed,rain_1h=0, snow_1h=0,cross_join=None):
        ## General info
        self.date = date
        self.name = name
        self.cross_join = cross_join #use only in current to cross_join with solar
        ## Meteo general description
        self.clouds = clouds
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
            'clouds': self.clouds,
            'pressure': self.pressure,
            'humidity': self.humidity,
            'temp': self.temp,
            'rain_1h':self.rain_1h,
            'snow_1h': self.snow_1h,
            'wind_deg': self.wind_deg,
            'wind_speed': self.wind_speed
        })


    @staticmethod
    def current_from_original_dict_to_class(obj:dict, rain=0, snow=0):
        """
        This function has to be applied on a single call from the current data.
        So for each city one call and it will return an object MeteoCurrentData.
        """
        if 'rain' in obj: rain = obj['rain']["1h"]
        if 'snow' in obj: snow=obj["snow"]['1h']
        original_dt = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(obj["dt"]))
        return MeteoData(
            name = obj["name"],
            date = original_dt,
            clouds = obj["clouds"]["all"],
            cross_join=obj["cross_join"],
            pressure= obj["main"]["pressure"],
            humidity= obj["main"]["humidity"],
            temp = obj["main"]["temp"],
            rain_1h = rain,
            snow_1h = snow,
            wind_deg= obj["wind"]["deg"],
            wind_speed= obj["wind"]["speed"])

    @staticmethod
    def current_from_preprocess_dict_to_class(obj:dict, rain=0, snow=0):
        """
        This function has to be applied on a single call from the current data.
        So for each city one call and it will return an object MeteoCurrentData.
        """
        if 'rain' in obj: rain = obj['rain_1h']
        if 'snow' in obj: snow=obj["snow_1h"]
        return MeteoData(
            name = obj["name"],
            date = obj["date"],
            clouds = obj["clouds"],
            cross_join=obj["cross_join"],
            pressure= obj["pressure"],
            humidity= obj["humidity"],
            temp = obj["temp"],
            rain_1h = rain,
            snow_1h = snow,
            wind_deg= obj["wind_deg"],
            wind_speed= obj["wind_speed"])

    @staticmethod
    def forecast_from_dict_to_class(city: List[dict], rain=0, snow=0):
        """
        obj is the forecast meteo for one city!
        This function has to be applied on a single call from the forecast meteo.
        So for each city one call and it will return a list of dict, each dict will have
        the forecast meteo for that city and the next 48 hour.
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

###################################################################################################################
class ForecastData():
    def update_forecast_radiation(self, forecast_radiations:List[MeteoRadiationData]):
        """
        require the List obtained from MeteoRadiationData.forecast_from_dict_to_class()
        """
        tmp = []
        for city in forecast_radiations:
            for obs in city:
                tmp.append(obs.current_from_class_to_dict())
        df=pd.DataFrame(tmp)
        df.sort_values(by="date", ascending=False, inplace=True)
        # df.to_csv("forecast_solar_radiation.csv", index=False)
        return df

    def update_forecast_meteo(self, forecast_meteo:List[MeteoData]):
        res = []
        for city in forecast_meteo:
            for hour in city:
                obj = hour.from_class_to_dict()
                res.append(obj)
        df = pd.DataFrame(res)
        df.sort_values(by="date", inplace=True)
        # df.to_csv("forecast_meteo.csv", index=False)
        return df

    def merge_forecast(self,radiations_df, meteo_df):
        """
        This function will return the forecast for the next 48 hours!
        """
        final = pd.merge(meteo_df, radiations_df[
            ['name', 'date', 'globalhorizontalirradiance', 'directnormalirradiance',
             'diffusehorizontalirradiance', 'globalhorizontalirradiance_2',
             'directnormalirradiance_2', 'diffusehorizontalirradiance_2']],
                         on=["date", "name"], how='left')

        final.drop(columns=["cross_join"], inplace=True)
        #final.to_csv("new_forecast_obs.csv", index=False)
        final["date"] = pd.to_datetime(final["date"], format='%d/%m/%Y %H:%M:%S %p')
        final["str_hour"] = final["date"].dt.strftime("%H")
        final["str_month"] = final["date"].dt.strftime("%B")
        final["str_month"] = final["str_month"].str.lower()
        def AM_PM(str_hour):
            if int(str_hour)>=13:  str_hour = str(24-13)+"PM"
            elif int(str_hour)== 0: str_hour = "12PM"
            elif int(str_hour) < 10:  str_hour = str_hour[-1]+"AM"
            else:  str_hour = str_hour + "AM"
            return str_hour
        final["str_hour"] = final["str_hour"].apply(AM_PM)
        #final.to_csv("to_check_forecast.csv", index=False)
        final = final.sort_values(by="date")
        final["date"] = final["date"].dt.strftime('%Y/%m/%d %H:%M:%S')
        return final

if __name__ == "__main__":
    ""