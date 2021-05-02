from fetching_meteo import *
from managers_meteo import *
from meteo_classes import  *
from pprint import pprint
import argparse, sys, textwrap

def HOW_TO_CALL_THE_FUNCTION():
    """
    For each information how to call it, transform into the class and return back
    to dictionary. if want to see how they look likes just print the check!
    """
    ######################################################################################################
    # CURRENT METEO DATA
    print(datetime.datetime.now())
    current_meteo = GetMeteoData().fetching_current_meteo_json()
    check=(MeteoData.current_from_original_dict_to_class(current_meteo[0]).from_class_to_dict())
    print(datetime.datetime.now())
    ######################################################################################################
    # CURRENT SOLAR RADIATION
    print(datetime.datetime.now())
    current_solar = GetMeteoData().fetching_current_solar_radiation()
    check=(MeteoRadiationData.current_from_original_dict_to_class(current_solar[0]).current_from_class_to_dict())
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
def create_tmp_csv():
    meteo=JsonManagerCurrentMeteo().load()
    tmp = []
    for obs in meteo:
        tmp.append(MeteoData.current_from_original_dict_to_class(obs).from_class_to_dict())
    df = pd.DataFrame(tmp)
    df.to_csv("meteo.csv", index=False)
    radiation=JsonManagerCurrentRadiation().load()
    tmp = []
    for obs in radiation:
        tmp.append(MeteoRadiationData.current_from_original_dict_to_class(obs).current_from_class_to_dict())
    df = pd.DataFrame(tmp)
    df.to_csv("radiation.csv", index=False)

def main_cli():
    title = """------------------------>  Deal all the steps of the pipeline from here! <---------------------------"""
    parser = argparse.ArgumentParser(description=title, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ### must add argument, one for each distributed process.
    parser.add_argument('-m', "--start_manager", action='store_true',
                        help="Start colleting current meteo and radiation and updating the storico")
    parser.add_argument('-f', "--force_start", default='force',choices=['force','production'])
    args = parser.parse_args()
    if args.start_manager:
        if args.force_start == "Force":
            print(args.start_manager)


if __name__=="__main__":
    x = GetMeteoData().fetching_forecast_meteo()
    x = MeteoData.forecast_from_dict_to_class(x)
    ForecastData().update_forecast_meteo(x)