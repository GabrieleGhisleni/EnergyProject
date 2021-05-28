import paho.mqtt.client as mqtt
from typing import TypeVar, List
import json, datetime
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")
from managers_meteo import ManagerTernaSql
from models import *
###################################################################################################################

class MqttManager():
    """
    Class created to handle the interaction with the mosquitto broker.
    """
    def __init__(self):
        self.client = mqtt.Client()
        self.client.connect("localhost", port=1883)

    def publish_prediction(self,predictions:List[dict])->None:
        """
        Takes as argument a list of dictionary obtained with the pre-process
        function of the prediction of the days.
        """
        self.client.publish("Energy/prediction_energy/", json.dumps(predictions), qos=1, retain=True)
        print("update at:", datetime.datetime.now())

    def subscriber_load_prediction(self)->None:
        """
        Take the load predictions from the broker and drop it into
        the SQL databases.
        """
        def on_message(client, user_data, msg):
            predictions = json.loads(msg.payload.decode())
            SqlManager = ManagerTernaSql()
            SqlManager.prediction_to_sql(predictions)
            #When receive the other prediction make the predictions about thermal!
            Thermal = ThermalModel()
            termal_data = Thermal.pre_process_for_thermal(predictions)
            termal_prediction = Thermal.custom_predict(termal_data)
            SqlManager.preprocess_thermal_prediction_to_sql(termal_prediction,
                                                            termal_data["date"].unique())
        self.client.subscribe("Energy/prediction_energy/")
        self.client.on_message = on_message

        self.client.loop_forever()

###################################################################################################################
if __name__ == "__main__":
    MqttManager().subscriber_load_prediction()