import requests, time, datetime, os, argparse
from typing import List
import Code.meteo_class as meteo_class
import Code.mqtt_manager as c_mqtt

class GetMeteoData:
    """
    class created to handle the raw data from the OpenWeather Map API.
    """
    def __init__(self):
        self.key = os.environ.get('OPEN_WEATHER_APPID')
        self.it_regions = {'Bari': {'lat': 41.1177, 'lon': 16.8512},
                           'Bologna': {'lat': 44.4667, 'lon': 11.4333},
                           'Catanzaro': {'lat': 38.8908, 'lon': 16.5987},
                           'Firenze': {'lat': 43.7667, 'lon': 11.25},
                           "L'Aquila": {'lat': 42.365, 'lon': 13.3935},
                           'Milano': {'lat': 45.4643, 'lon': 9.1895},
                           'Naples': {'lat': 40.8333, 'lon': 14.25},
                           'Potenza': {'lat': 40.6443, 'lon': 15.8086},
                           'Palermo': {'lat': 37.8167, 'lon': 13.5833},
                           'Turin': {'lat': 45.1333, 'lon': 7.3667},
                           'Ancona': {'lat': 43.55, 'lon': 13.1667},
                           'Campobasso': {'lat': 41.6333, 'lon': 14.5833},
                           'Genova': {'lat': 44.5, 'lon': 9.0667},
                           'Perugia': {'lat': 43.05, 'lon': 12.55},
                           'Rome': {'lat': 41.8947, 'lon': 12.4839},
                           'Sardinia': {'lat': 40, 'lon': 9},
                           'Trento': {'lat': 46.0679, 'lon': 11.1211},
                           'Trieste': {'lat': 45.6486, 'lon': 13.78},
                           "Valle d'Aosta": {'lat': 45.7667, 'lon': 7.4167},
                           'Venice': {'lat': 45.4386, 'lon': 12.3267}}

    def fetching_current_meteo_json(self) -> List[dict]:
        """
        fetch all the current meteo data from the regions, return a list of is_dict aka json
        it collect the data from the API as dictionary and insert them all into a list
        so the function return a list of dictionary, each dictionary is a registration
        for a particular capoluogo
        """
        res = []
        cross_join_detail = datetime.datetime.now().strftime("%d/%m/%Y %H:%M %p")
        current_time = False
        for regione in self.it_regions:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?appid={self.key}&units=metric&q={regione},it"
                response = requests.request("GET", url)
                if not response.ok: print("Something wrong with the respunsus ok API" + str(response) + "at " + regione)
                else:
                    tmp = response.json()
                    if not current_time: current_time = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(tmp["dt"]))
                    tmp["region"] = regione
                    tmp["organized_data"] = current_time
                    tmp["cross_join"] = cross_join_detail
                    res.append(tmp)
            except Exception as e: print("\n --> Fatal error with the requests connection <--", str(e))
        return res

    def fetching_forecast_meteo(self) -> List[dict]:
        """
        fetch all the forecast solar radiation data from the regions, return a list of  is_dict
        it collect the data from the API as dictionary and insert them all into a list
        so the function return a list of dictionary, each dictionary is a registration
        for a particular capoluogo.
        """
        res = []
        for citta in self.it_regions:
            try:
                lat = self.it_regions[citta]['lat']
                lon = self.it_regions[citta]['lon']
                url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,current,daily,alerts&appid={self.key}"
                response = requests.request("GET", url)
                if not response.ok: print("Something wrong with the respunsus ok API" + str(response) + "at " + citta)
                else:
                    tmp = response.json()
                    tmp["name"] = citta
                    for hour in tmp["hourly"]: hour["orario"] = time.strftime("%d/%m/%Y %H:%M:%S %p", time.localtime(hour["dt"]))
                    res.append(tmp)
            except Exception as e: print("\n --> Fatal error with the requests connection <--", str(e))
        return res

def prepare_forecast_to_send(broker: str = 'localhost') -> None:
    """
    Fetch the raw forecast API data, process it using the proper
    class and then send it to the mqtt broker for the next steps.
    """
    print(f"Sending raw forecast meteo data at MQTT-{broker}")
    predictions_raw = GetMeteoData().fetching_forecast_meteo()
    meteo_forecast = meteo_class.MeteoData.forecast_from_dict_to_class(city=predictions_raw)
    meteos_df = meteo_class.MeteoData.update_forecast_meteo(forecast_meteo=meteo_forecast)
    c_mqtt.MqttManager(broker).custom_publish(data=meteos_df.to_dict(), topic="Energy/ForecastMeteo/")

def main():
    arg_parser = argparse.ArgumentParser(description="Forecast collector!")
    arg_parser.add_argument("-b", "--broker", required=True, type=str,  help="MQTT Broker", choices=['localhost', 'aws'])
    arg_parser.add_argument('-r', '--rate', default=6, type=int, help="Frequencies express in hours")
    args = arg_parser.parse_args()

    while True:
        prepare_forecast_to_send(broker=args.broker)
        time.sleep(args.rate * (60*60))


if __name__ == "__main__":
    main()
