import json, time, datetime,os
from typing import List
from get_meteo_data import *

class JsonManagerMeteo():
    def load(self)->List[dict]:
        if os.path.exists('storico_meteo.json'):
            with open("storico_meteo.json", "r") as file:
                storico = json.load(file)
                file.close()
            return storico
        else:
            self.first_update()
            return self.load()

    def first_update(self):
        print("File not found, created 'storico_meteo.json' and first update")
        obs = (GetMeteoData().fetching_current_meteo_json())
        with open("storico_meteo.json", "w") as file:
            json.dump(obs, file, indent=4)

    def update(self)->None:
        storico = self.load()
        new_obs = (GetMeteoData().fetching_current_meteo_json())
        update = storico + new_obs # must optimize this process
        with open("storico_meteo.json", "w") as file:
            json.dump(update, file, indent=4)

def into_the_loop():
    manager = JsonManagerMeteo()
    while True:
        if str(datetime.datetime.now().time().minute).endswith('0')\
            or str(datetime.datetime.now().time().minute).endswith('5'):
                manager.update()
                time.sleep(290)

if __name__ == "__main__":
    into_the_loop()
