import paho.mqtt.client as mqtt
from typing import TypeVar, List
import json, datetime, ssl, time
import numpy as np
import pandas as pd
from managers_meteo import ManagerTernaSql
from models import *
from KEYS.config import (CA_ROOT_CERT_FILE, THING_CERT_FILE, THING_PRIVATE_KEY,
                         MQTT_PORT, MQTT_KEEPALIVE_INTERVAL, MQTT_HOST)

class MqttManager():
    """
    Class created to handle the interaction with the mosquitto broker.
    """
    def __init__(self):
        def on_publish_custom(client, userdata, mid): print("Message Published...", mid)

        def on_message_custom(client, user_data, msg):
            if msg.topic == "Energy/PredictionEnergy/":
                print(f"Receving at topic {msg.topic}")
                predictions = json.loads(msg.payload.decode())
                SqlManager = ManagerTernaSql()
                SqlManager.prediction_to_sql(predictions)
                Thermal = ThermalModel()
                termal_data = Thermal.pre_process_for_thermal(predictions)
                termal_prediction = Thermal.custom_predict(termal_data)
                to_send = pd.DataFrame( termal_prediction, termal_data["date"].unique())
                MqttManager().publish_thermal(to_send)




            elif msg.topic == "Energy/PredictionThermal/":
                print(f"Receving at topic {msg.topic}")
                new_obs = pd.DataFrame.from_dict(json.loads(msg.payload))
                SqlManager = ManagerTernaSql()
                new_obs["date"]= new_obs.index
                new_obs['date'] = pd.to_datetime(new_obs['date'])
                new_obs["date"] = new_obs["date"].dt.strftime("%Y/%m/%d %H:%M:%S")
                SqlManager.preprocess_thermal_prediction_to_sql(new_obs['0'].values,new_obs['date'])
                print("Done")


            elif msg.topic == "Energy/ForecastMeteo/":
                print(f"Receving at topic {msg.topic}")
                df = json.loads(msg.payload)
                new_obs = pd.DataFrame.from_dict(df)
                hours_of_prediction = new_obs["date"].unique()
                ts = pd.to_datetime(hours_of_prediction)
                hours_of_prediction = ts.strftime('%Y/%m/%d %H:%M:%S').tolist()
                load_to_predict= create_load_to_predict(hours_of_prediction)
                load_tot = LoadModel().custom_predict(load_to_predict)
                hydro_prediction = HydroModel().custom_predict(new_obs)
                geothermal_prediction = GeoThermalModel().custom_predict(new_obs)
                wind_prediction = WindModel().custom_predict(new_obs)
                photovoltaic_prediction = PhotovoltaicModel().custom_predict(new_obs)
                biomass_prediction = BiomassModel().custom_predict(new_obs)
                res = {}

                for ih in range(len(hours_of_prediction)):
                    res[hours_of_prediction[ih]] = {
                        'hydro': hydro_prediction[ih],
                        'geothermal': geothermal_prediction[ih],
                        'wind': wind_prediction[ih],
                        'photovoltaic': photovoltaic_prediction[ih],
                        'biomass': biomass_prediction[ih],
                        'load': load_tot[int(hours_of_prediction[ih].split(" ")[1].split(":")[0])]
                    }
                MqttManager().publish_prediction(res)

        self.mqttc = mqtt.Client()
        self.mqttc.connect('localhost', 1883)
        #
        # self.mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY,
        #                    cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        # self.mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)


        self.mqttc.on_message = on_message_custom
        self.mqttc.on_publish = on_publish_custom

        # remember if use aws remove retain = True or it wont work.


    def publish_thermal(self, predictions):
        topic = "Energy/PredictionThermal/"
        msg = json.dumps(predictions.to_dict())
        time.sleep(10)
        self.mqttc.publish(topic = topic, payload= msg,  qos=1, retain = True)
        time.sleep(10)
        print(f"Sending to {topic} at: ", datetime.datetime.now())



    def publish_prediction(self,predictions)->None:
        topic = "Energy/PredictionEnergy/"
        msg = json.dumps(predictions)
        time.sleep(10)
        self.mqttc.publish(topic = topic, payload= msg,  qos=1, retain = True)
        time.sleep(10)
        print(f"Sending to {topic} at: ", datetime.datetime.now())




    def publish_forecast(self, forecast)->None:
        topic = "Energy/ForecastMeteo/"
        msg = json.dumps(forecast.to_dict())
        time.sleep(10)
        self.mqttc.publish(topic = topic, payload= msg,  qos=1, retain = True)
        time.sleep(10)
        print(f"Sending to {topic} at: ", datetime.datetime.now())



    def subscriber(self)->None:
        print("Subscribing to all the topics!")
        self.mqttc.subscribe("Energy/ForecastMeteo/")
        self.mqttc.subscribe("Energy/PredictionEnergy/")
        self.mqttc.subscribe("Energy/PredictionThermal/")
        self.mqttc.loop_forever()





###################################################################################################################
if __name__ == "__main__":
    MqttManager().subscriber()
