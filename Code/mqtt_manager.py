import paho.mqtt.client as mqtt
import json, ssl
from Code.models_manager import *
import Code.meteo_managers as dbs

class MqttManager:
    """
    Class created to handle the interaction with the mosquitto broker.
    """
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/'):
        self.broker = broker if broker.lower() == 'localhost' else 'AWS-IoT-Core'
        self.path_model = path_models
        self.redis = dbs.RedisDB()
        self.mysql = dbs.MySqlDB()

        def on_connect(client, userdata, flags, rc):
            if rc == 0: print(f"Connection OK! Waiting for messages!")
            else: print("Bad connection Returned code = ", rc)

        def on_message_custom(client, user_data, msg):
            if msg.topic == "Energy/PredictionEnergy/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                predictions = json.loads(msg.payload.decode())
                self.mysql.prediction_to_sql(predictions)
                self.redis.set_energy(predictions)
                res = process_thermal_mqtt(predictions, self.path_model)
                self.publish(data=res, is_dict=True, topic="Energy/PredictionThermal/")

            elif msg.topic == "Energy/Load/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                predictions = json.loads(msg.payload.decode())
                self.mysql.prediction_to_sql(predictions)
                self.redis.set_load(predictions)

            elif msg.topic == "Energy/PredictionThermal/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                raw_msg = json.loads(msg.payload)
                values, dates = process_results(raw_msg)
                self.mysql.preprocess_thermal_prediction_to_sql(values, dates)
                self.redis.set_thermal(values, dates)
                print("Done! - Check the data on  http://127.0.0.1:8000/today-prediction/ ")
                time.sleep(15)

            elif msg.topic == "Energy/Storico/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                msg = json.loads(msg.payload)
                meteos = pd.DataFrame.from_dict(msg)
                self.mysql.save_current_meteo(meteos)

            elif msg.topic == "Energy/ForecastMeteo/":
                print(f"Receving at {self.broker}/{msg.topic}")
                raw_msg = json.loads(msg.payload)
                res = process_forecast_mqtt(msg=raw_msg, path=self.path_model)
                self.publish(data=res, is_dict=False, topic="Energy/PredictionEnergy/")

        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = on_connect

        if self.broker == 'localhost':
            mqtt_local = os.environ.get('MQTT_HOST_LOCAL')
            local_port = os.getenv('MQTT_LOCAL_PORT', 1883)
            self.mqttc.connect(mqtt_local, local_port)
        else:
            ca_root = os.environ.get('CA_ROOT_CERT_FILE')
            cert = os.environ.get('THING_CERT_FILE')
            private = os.environ.get('THING_PRIVATE_KEY')
            aws_host = os.environ.get('MQTT_HOST')
            aws_port = os.getenv('MQTT_AWS_PORT', 8883)
            self.mqttc.tls_set(ca_root, certfile=cert, keyfile=private,
                               cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
            self.mqttc.connect(aws_host, aws_port, 60)
            print(f"Connecting to AWS IoT Core")

        self.mqttc.on_message = on_message_custom
        self.sleeps = 0 if self.broker == 'localhost' else 0.5
        self.retain = True if self.broker == 'localhost' else False
        # remember if use aws remove retain = True or it wont work.

    def publish(self, data, topic: str, is_dict: bool = False) -> None:
        print(f"Sending to {self.broker}/{topic} at: {time_()}")
        if is_dict:  msg = json.dumps(data.to_dict())
        else: msg = json.dumps(data)
        time.sleep(self.sleeps)
        self.mqttc.publish(topic=topic, payload=msg,  qos=1, retain=self.retain)
        time.sleep(self.sleeps)

    def subscriber(self, topic: str = 'all') -> None:
        if topic == 'all':
            print(f"Subscribing to all the topics --> Broker = {self.broker}")
            time.sleep(self.sleeps)
            self.mqttc.subscribe("Energy/Storico/")
            self.mqttc.subscribe("Energy/Load/")
            self.mqttc.subscribe("Energy/ForecastMeteo/")
            self.mqttc.subscribe("Energy/PredictionEnergy/")
            self.mqttc.subscribe("Energy/PredictionThermal/")
            self.mqttc.loop_forever()
        else:
            if topic == 'forecast': to_sub = "Energy/ForecastMeteo/"
            elif topic == 'energy': to_sub = "Energy/PredictionEnergy/"
            elif topic == 'thermal': to_sub = "Energy/PredictionThermal/"
            elif topic == 'load': to_sub = "Energy/Load/"
            elif topic == 'storico': to_sub = "Energy/Storico/"
            else:
                text_error = f"'{topic}' is an invalid choice! [forecast, energy, thermal, all, load]"
                raise ValueError(text_error)
            time.sleep(self.sleeps)
            print(f"Subscribing to {topic} --> Broker = {self.broker}")
            self.mqttc.subscribe(to_sub)
            self.mqttc.loop_forever()

def time_(): return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    arg_parse = argparse.ArgumentParser(description="MQTT Manager!")
    arg_parse.add_argument('-b', '--broker', default='localhost', choices=['localhost', 'aws'])
    arg_parse.add_argument('-p', '--path', default='Models/', help="""Path to find the models""")
    arg_parse.add_argument('-t', '--topic', required=True, choices=['forecast', 'energy', 'thermal', 'load', 'all', 'storico'],
                           help="""
                           Since we made this project as decoupled as possible here you can basically assign 
                           each step of the processing pipeline to a different 'machine' specifying the topic in which \
                           have to be subscribed. According to the subscription each piece will perform different tasks. \
                           IMPORTANT: if you are running for test purpose you can specify 'all' so it will do all the operation\
                           in one process, otherwise specify the topic and run different process in this order [forecast, energy, thermal]\
                           -IF you are running with different process and using as broker aws you must run at the same time because we
                           cannot use retain option.""")
    args = arg_parse.parse_args()
    if args.broker != 'localhost' and args.broker != 'aws': print(f"Not valid broker - {args.broker}"), exit()
    if args.topic not in ['all', 'load', 'thermal', 'energy','forecast', 'storico']: print(f"Not valid topic - {args.topic}"), exit()
    MqttManager(broker=args.broker, path_models=args.path).subscriber(topic=args.topic)


if __name__ == "__main__":
    main()