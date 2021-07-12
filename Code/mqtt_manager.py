import paho.mqtt.client as mqtt
import json, ssl
from Code.models_manager import *
import Code.meteo_managers as dbs

class MqttManager:
    def __init__(self, broker: str = 'localhost', path_models: str = 'Models/', ex_time: int = 24, retain: bool = False):
        def on_connect(client, userdata, flags, rc):
            if rc == 0: print(f"Connection OK! Waiting for messages!")
            else: print("Bad connection Returned code = ", rc)

        def on_message_custom(client, user_data, msg):
            if msg.topic == "Energy/Load/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                predictions = json.loads(msg.payload.decode())
                self.mysql.prediction_to_sql(predictions)
                self.redis.set_load(predictions)

            elif msg.topic == "Energy/Storico/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                msg = json.loads(msg.payload)
                meteos = pd.DataFrame.from_dict(msg)
                self.mysql.save_current_meteo(meteos)

            elif msg.topic == "Energy/ForecastMeteo/":
                print(f"Receving at {self.broker}/{msg.topic}")
                raw_msg = json.loads(msg.payload)
                res = process_forecast_mqtt(msg=raw_msg, path=self.path_model)
                self.custom_publish(data=res, topic="Energy/PredictionEnergy/")

            elif msg.topic == "Energy/PredictionEnergy/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                predictions = json.loads(msg.payload.decode())
                self.mysql.prediction_to_sql(predictions)
                self.redis.set_energy(predictions)
                thermal_res = preprocess_mqtt(predictions, path=self.path_model, src='thermal')
                hydro_res = preprocess_mqtt(predictions, path=self.path_model, src='hydro')
                self.custom_publish(data=[thermal_res.to_dict(), hydro_res.to_dict()], topic="Energy/PredictionThermal/")

            elif msg.topic == "Energy/PredictionThermal/":
                print(f"Receiving at {self.broker}/{msg.topic}")
                raw_msg = json.loads(msg.payload)
                values_thermal, dates_thermal = process_results(raw_msg[0])
                values_hydro, dates_hydro = process_results(raw_msg[1])
                self.mysql.preprocess_thermal_prediction_to_sql(values_thermal, dates_hydro)
                self.redis.set_src(values_thermal, dates_hydro, src='thermal')
                self.redis.set_src(values_hydro, dates_hydro, src='hydro')
                print("Done! - Check the data on  http://127.0.0.1:8000/today-prediction/ ")
                time.sleep(60)

        self.broker = broker if broker.lower() == 'localhost' else 'AWS-IoT-Core'
        self.path_model = path_models
        self.redis = dbs.RedisDB(hours_expiration=ex_time)
        self.mysql = dbs.MySqlDB()
        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = on_connect

        if self.broker == 'localhost':
            mqtt_local = os.environ.get('MQTT_HOST_LOCAL')
            local_port = os.getenv('MQTT_LOCAL_PORT', 1883)
            self.mqttc.connect(mqtt_local, local_port)
            print(f"Connecting to Localhost")
        else:
            ca_root = os.environ.get('CA_ROOT_CERT_FILE')
            cert = os.environ.get('THING_CERT_FILE')
            private = os.environ.get('THING_PRIVATE_KEY')
            aws_host, aws_port = os.environ.get('MQTT_HOST'), os.getenv('MQTT_AWS_PORT', 8883)
            cert_req, prot = ssl.CERT_REQUIRED, ssl.PROTOCOL_TLSv1_2
            self.mqttc.tls_set(ca_certs=ca_root, certfile=cert, keyfile=private, cert_reqs=cert_req, tls_version=prot)
            self.mqttc.connect(aws_host, aws_port, 60)
            print(f"Connecting to AWS IoT Core")

        self.mqttc.on_message = on_message_custom
        self.sleeps = 0 if self.broker == 'localhost' else 0.5
        self.retain = retain
        # remember if use aws remove retain = True or it wont work.

    def custom_publish(self, data, topic: str) -> None:
        print(f"Sending to {self.broker}/{topic} at: {time_()}")
        msg = json.dumps(data)
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
            else: to_sub = "Energy/Storico/"
            time.sleep(self.sleeps)
            print(f"Subscribing to {topic} --> Broker = {self.broker}")
            self.mqttc.subscribe(to_sub)
            self.mqttc.loop_forever()

def time_(): return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    topic_available = ['forecast', 'energy', 'thermal', 'load', 'all', 'storico']
    arg_parse = argparse.ArgumentParser(description="MQTT Manager!")
    arg_parse.add_argument('-b', '--broker', default='localhost', choices=['localhost', 'aws'])
    arg_parse.add_argument('-t', '--topic', required=True, choices=topic_available)
    arg_parse.add_argument('-r', '--retain', default=False, type=bool, help="Retain mqtt messages")
    arg_parse.add_argument('-ex', '--expiration_time', default=24, type=int, help="Expiration of redis store")
    arg_parse.add_argument('-p', '--path', default='Models/', help="""Path to find the models""")
    args = arg_parse.parse_args()

    mqtt_ = MqttManager(broker=args.broker, path_models=args.path, ex_time=args.expiration_time, retain=args.retain)
    mqtt_.subscriber(topic=args.topic)


if __name__ == "__main__":
    main()
