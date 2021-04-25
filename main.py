from get_meteo_data import *
from manager_meteo_data import *
from meteo_class import  *

if __name__ == "__main__":
    datas = JsonManagerMeteo().load()
    for data in datas:
        x=MeteoData.from_dict_to_class(data)
    print(x)