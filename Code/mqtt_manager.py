import paho.mqtt.client as mqtt
import json, ssl
from Code.models_manager import *
import Code.meteo_managers as dbs


class MqttGeneralClass:
    """
    Skeleton class used for dealing the Mqtt clients.
    """
    def __init__(self, client_name: str, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        def on_connect(client, userdata, flags, rc):
            if rc == 0: print(f"{self.client_name} is connected to {self.broker}! Waiting for messages!")
            else: print(f"{self.client_name} is not able to connect at {self.broker}! code={rc}")

        self.broker = broker if broker.lower() == 'localhost' else 'AWS-IoT-Core'
        self.path_model = path_models
        self.client_name = client_name
        self.mqttc = mqtt.Client(self.client_name)
        self.connect(self.mqttc, self.broker)
        self.mqttc.on_connect = on_connect
        self.sleeps = 0 if self.broker == 'localhost' else 0.5
        self.retain = retain
        self.redis = dbs.RedisDB(hours_expiration=ex_time)
        self.mysql = dbs.MySqlDB()

    def connect(self, client, host):
        if host == 'localhost': client.connect(os.environ.get('MQTT_HOST_LOCAL'), os.getenv('MQTT_LOCAL_PORT', 1883))
        else:
            client.tls_set(ca_certs=os.environ.get('CA_ROOT_CERT_FILE'),
                           certfile=os.environ.get('THING_CERT_FILE'),
                           keyfile= os.environ.get('THING_PRIVATE_KEY'),
                           cert_reqs=ssl.CERT_REQUIRED,
                           tls_version=ssl.PROTOCOL_TLSv1_2)
            client.connect(os.environ.get('MQTT_HOST'), os.getenv('MQTT_AWS_PORT', 8883), 60)

    def custom_publish(self, data, topic: str) -> None:
        print(f"{self.client_name} is sending to {self.broker}/{topic}. time: {time_()}")
        msg = json.dumps(data)
        time.sleep(self.sleeps)
        self.mqttc.publish(topic=topic, payload=msg,  qos=1, retain=self.retain)
        time.sleep(self.sleeps)

    def subscribe(self):
        self.mqttc.subscribe(self.topic)
        self.mqttc.loop_forever()


class ForecastClient(MqttGeneralClass):
    """
    Child class of MqttGeneralClass that handle the ForecastClient.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        super().__init__(broker=broker, path_models=path_models, ex_time=ex_time, retain=retain, client_name='ForecastClient')
        def on_message_forecast(client, user_data, msg):
            print(f"{self.client_name} is receiving at {self.broker}/{msg.topic}. time: {time_()}")
            raw_msg = json.loads(msg.payload)
            res, to_sql = process_forecast_mqtt(msg=raw_msg, path=self.path_model)
            self.custom_publish(data=res, topic="Energy/PredictionEnergy/")
            self.mysql.save_meteo(to_sql, forecast=True)
        self.mqttc.on_message = on_message_forecast
        self.topic = "Energy/ForecastMeteo/"


class EnergyClient(MqttGeneralClass):
    """
    Child class of MqttGeneralClass that handle the EnergyClient.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        super().__init__(broker=broker, path_models=path_models, ex_time=ex_time, retain=retain, client_name='EnergyPredictionClient')
        def on_message_energy(client, user_data, msg):
                print(f"{self.client_name} is receiving at {self.broker}/{msg.topic}. time: {time_()}")
                predictions = json.loads(msg.payload.decode())
                thermal_res = preprocess_mqtt(predictions, path=self.path_model, src='thermal')
                hydro_res = preprocess_mqtt(predictions, path=self.path_model, src='hydro')
                self.redis.set_energy(predictions)
                self.custom_publish(data=[thermal_res.to_dict(), hydro_res.to_dict()], topic="Energy/PredictionHydroThermal/")
                self.mysql.prediction_to_sql(predictions)
        self.mqttc.on_message = on_message_energy
        self.topic = "Energy/PredictionEnergy/"


class ThermalHydroClient(MqttGeneralClass):
    """
    Child class of MqttGeneralClass that handle the ThermalHydroClient.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        super().__init__(broker=broker, path_models=path_models, ex_time=ex_time, retain=retain, client_name='HydroThermalClient')
        def on_message_thermal_hydro(client, user_data, msg):
            print(f"{self.client_name} is receiving at {self.broker}/{msg.topic}. time: {time_()}")
            raw_msg = json.loads(msg.payload)
            values_thermal, dates_thermal = process_results(raw_msg[0])
            values_hydro, dates_hydro = process_results(raw_msg[1])
            self.redis.set_src(values_thermal, dates_hydro, src='thermal')
            self.redis.set_src(values_hydro, dates_hydro, src='hydro')
            print("Done! - Check the data on  http://127.0.0.1:8000/today-prediction/ ")
            self.mysql.preprocess_thermal_prediction_to_sql(values_thermal, dates_hydro)
            time.sleep(60)
        self.mqttc.on_message = on_message_thermal_hydro
        self.topic = "Energy/PredictionHydroThermal/"


class LoadClient(MqttGeneralClass):
    """
    Child class of MqttGeneralClass that handle the LoadClient.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        super().__init__(broker=broker, path_models=path_models, ex_time=ex_time, retain=retain, client_name='LoadClient')
        def on_message_load(client, user_data, msg):
            print(f"{self.client_name} is receiving at {self.broker}/{msg.topic}. time: {time_()}")
            predictions = json.loads(msg.payload.decode())
            self.mysql.prediction_to_sql(predictions)
            self.redis.set_load(predictions)
        self.mqttc.on_message = on_message_load
        self.topic = "Energy/Load/"


class StoricoClient(MqttGeneralClass):
    """
    Child class of MqttGeneralClass that handle the StoricoClient.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        super().__init__(broker=broker, path_models=path_models, ex_time=ex_time, retain=retain, client_name='StoricoClient')
        def on_message_storico(client, user_data, msg):
            print(f"{self.client_name} is receiving at {self.broker}/{msg.topic}. time: {time_()}")
            msg = json.loads(msg.payload)
            meteos = pd.DataFrame.from_dict(msg)
            self.mysql.save_meteo(meteos)
        self.mqttc.on_message = on_message_storico
        self.topic = "Energy/Storico/"


def time_(): return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    topic_available = ['forecast', 'energy', 'hydro_thermal', 'load', 'storico']
    arg_parse = argparse.ArgumentParser(description="MQTT Manager!")
    arg_parse.add_argument('-b', '--broker', default='localhost', choices=['localhost', 'aws'])
    arg_parse.add_argument('-t', '--topic', required=True, choices=topic_available)
    arg_parse.add_argument('-r', '--retain', action='store_true', help="Retain mqtt messages")
    arg_parse.add_argument('-ex', '--expiration_time', default=24, type=int, help="Expiration of redis store")
    arg_parse.add_argument('-p', '--path', default='Models/', help="""Path to find the models""")
    args = arg_parse.parse_args()

    if args.topic == 'forecast': client = ForecastClient(broker=args.broker, retain=args.retain, ex_time=args.expiration_time)
    elif args.topic == 'energy': client = EnergyClient(broker=args.broker, retain=args.retain, ex_time=args.expiration_time)
    elif args.topic == 'hydro_thermal': client = ThermalHydroClient(broker=args.broker, retain=args.retain, ex_time=args.expiration_time)
    elif args.topic == 'load': client = LoadClient(broker=args.broker, retain=args.retain, ex_time=args.expiration_time)
    else: client = StoricoClient(broker=args.broker, retain=args.retain, ex_time=args.expiration_time)
    client.subscribe()


if __name__ == "__main__":
    main()

