from get_meteo_data import *
from manager_meteo_data import *
from meteo_class import  *
from pprint import pprint

def HOW_TO_CALL_THE_FUNCTION():
    """
    For each information how to call it, transform into the class and return back
    to dictionary. if want to see how they look likes just print the check!
    """
    ######################################################################################################
    # CURRENT METEO DATA
    print(datetime.datetime.now())
    current_meteo = GetMeteoData().fetching_current_meteo_json()
    check=(MeteoData.current_from_dict_to_class(current_meteo[0]).from_class_to_dict())
    print(datetime.datetime.now())
    ######################################################################################################
    # CURRENT SOLAR RADIATION
    print(datetime.datetime.now())
    current_solar = GetMeteoData().fetching_current_solar_radiation()
    check=(MeteoRadiationData.current_from_dict_to_class(current_solar[0]).current_from_class_to_dict())
    print(datetime.datetime.now())
    ######################################################################################################
    # FORECAST METEO DATA
    print(datetime.datetime.now())
    forecast_meteo = GetMeteoData().fetching_forecast_meteo()
    for city in forecast_meteo:
        check= MeteoData.forecast_from_dict_to_class(city)
    print(datetime.datetime.now())
    ######################################################################################################
    # FORECAST SOLAR RADIATION
    print(datetime.datetime.now())
    forecast_solar = GetMeteoData().fetching_forecast_solar_radiation()
    for data in forecast_solar:
        city = MeteoRadiationData.forecast_from_dict_to_class(data)
        for obs in city:
            check = obs.current_from_class_to_dict()
    print(datetime.datetime.now())
    ######################################################################################################

if __name__ == "__main__":
    print("im fine!")