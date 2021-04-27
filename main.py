from get_meteo_data import *
from manager_meteo_data import *
from meteo_class import  *
from pprint import pprint




if __name__ == "__main__":
    print(datetime.datetime.now())
    get= GetMeteoData().fetching_current_meteo_json()
    pprint(MeteoCurrentData.from_dict_to_class(get[0]).from_class_to_dict())
    print(datetime.datetime.now())
    get = GetMeteoData().fetching_forecast_meteo()
    pprint(MeteoForecastData.from_dict_to_class(get[0]))
    print(datetime.datetime.now())
    get = GetMeteoData().fetching_solar_radiation()
    pprint(MeteoCurrentRadiationData.from_dict_to_class(get[0]).from_class_to_dict())
    print(datetime.datetime.now())