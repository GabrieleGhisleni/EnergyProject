import time, joblib, os, argparse
import pandas as pd
import datetime as dt
from sklearn.ensemble import RandomForestRegressor, BaggingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from typing import Tuple
from pandas import DataFrame as PandasDataFrame
from numpy import array as NumpyArray
import Code.mqtt_manager as c_mqtt
import Code.meteo_managers as dbs


class EnergyModels:
    """
    Skeleton class used for all the energy models, included thermal and load.
    """
    def __init__(self):
        self.cat_variable = ['str_hour', 'str_month']

    def custom_fit_model(self, aug: str = 'yes') -> None:
        """
        Takes the model, fit and save it.
        """
        encoder = (OneHotEncoder(), self.cat_variable)
        pre_process = make_column_transformer(encoder, remainder='passthrough')
        sql_manager = dbs.MySqlModels()
        if self.source == 'thermal': pred, target = sql_manager.get_training_thermal_data()
        elif self.source == 'load': pred, target = sql_manager.get_training_load_data()
        else: pred, target = sql_manager.get_training_data(self.source, aug=aug)
        self.pipeline = make_pipeline(pre_process, self.model)
        self.pipeline.fit(pred, target.values.ravel())
        joblib.dump(self.pipeline, self.path)
        print(f"{self.source.capitalize()}Model fit on {len(target)} obs, stored at '{self.path}'")

    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Return prediction of the given model.
        """
        return self.pipeline.predict(new_observation.drop(columns=['date']))


class GeoThermalModel(EnergyModels):
    """
    Model used for deal the geothermal energy source.
    """
    def __init__(self, path: str = '../Models/'):
        super(GeoThermalModel, self).__init__()
        self.path, self.source = f"{path}geothermal.mod", 'geothermal'
        self.model = LinearRegression(fit_intercept=True, normalize=True)
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class WindModel(EnergyModels):
    """
    Model used for deal the wind energy source.
    """
    def __init__(self, path: str = '../Models/'):
        super(WindModel, self).__init__()
        self.path, self.source = f"{path}wind.mod", 'wind'
        self.model = RandomForestRegressor(n_estimators=100, criterion='mse', bootstrap=True)
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class PhotoVoltaicModel(EnergyModels):
    """
    Model used for deal the wind photovoltaic source.
    """
    def __init__(self, path: str = '../Models/'):
        super(PhotoVoltaicModel, self).__init__()
        self.path, self.source = f"{path}solar.mod", 'photovoltaic'
        self.model = BaggingRegressor(n_estimators=100, bootstrap=True)
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class BiomassModel(EnergyModels):
    """
    Model used for deal the biomass energy source.
    """
    def __init__(self, path: str = '../Models/'):
        super(BiomassModel, self).__init__()
        self.path, self.source = f"{path}biomass.mod", 'biomass'
        self.model = RandomForestRegressor(n_estimators=100, criterion='mse', bootstrap=True)
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class LoadModel(EnergyModels):
    """
    Model used for deal the load energy source.
    """
    def __init__(self, path: str = '../Models/'):
        self.path, self.source = f"{path}load.mod", 'load'
        self.model = BaggingRegressor(n_estimators=50, bootstrap=True)
        self.cat_variable = ["holiday", "str_hour", "str_month"]
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class HydroModel(EnergyModels):
    """
    Model used for deal the hydro energy source.
    """
    def __init__(self, path: str = '../Models/'):
        super(HydroModel, self).__init__()
        self.path, self.source = f"{path}hydro.mod", 'hydro'
        self.model = RandomForestRegressor(n_estimators=100, criterion='mse', bootstrap=True)
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")


class ThermalModel(EnergyModels):
    """
    Model used for deal the thermal energy source.
    """
    def __init__(self, path: str = '../Models/'):
        self.path, self.source = f"{path}thermal.mod", 'thermal'
        self.model = BaggingRegressor(n_estimators=30, bootstrap=True)
        self.cat_variable = ["holiday", "str_month"]
        if os.path.exists(self.path): self.pipeline = joblib.load(self.path)
        else: print(f"Do not found an already existing model at {self.path}")

    def pre_process(self, predictions: dict, loads: dict) -> PandasDataFrame:
        """
        Pre process the data that are passed to the thermal model.
        """
        tmp = []
        holiday_detector = dbs.HolidayDetector()
        for key in predictions:
            sum_of_rest, load = 0, 0
            holiday = holiday_detector.check_holiday_day(key)
            str_month = dt.datetime.strptime(key, "%Y/%m/%d %H:%M:%S").strftime("%B").lower()
            for energy in predictions[key]: sum_of_rest += predictions[key][energy]
            load = loads['generation'][key]
            tmp.append([holiday, sum_of_rest, load, str_month, key])
        colnames = {0: 'holiday', 1: 'Sum_of_rest_GW', 2: 'total_load', 3: 'str_month', 4: 'date'}
        return pd.DataFrame(tmp).rename(columns=colnames)


def train_models(model: str = 'all', path: str = "../Models/", aug: str = 'yes') -> None:
    """
    Function used to train the models.
    """
    tmp = dict(wind=WindModel(path),
               hydro=HydroModel(path),
               geothermal=GeoThermalModel(path),
               biomass=BiomassModel(path),
               photovoltaic=PhotoVoltaicModel(path),
               thermal=ThermalModel(path),
               load=LoadModel(path))
    if model == 'all': [tmp[model].custom_fit_model(aug=aug) for model in tmp]
    else: tmp[model].custom_fit_model(aug=aug)

def process_forecast_mqtt(msg: dict, path: str) -> dict:
    """
    Takes the already processed meteo forecast from the mqtt broker,
    perform the prediction and return them as a dict.
    """
    new_obs = pd.DataFrame.from_dict(msg)
    hours_of_prediction = new_obs["date"].unique()
    ts = pd.to_datetime(hours_of_prediction)
    hours_of_prediction = ts.strftime('%Y/%m/%d %H:%M:%S').tolist()
    hydro_prediction = HydroModel(path=path).custom_predict(new_obs)
    geothermal_prediction = GeoThermalModel(path=path).custom_predict(new_obs)
    wind_prediction = WindModel(path=path).custom_predict(new_obs)
    photovoltaic_prediction = PhotoVoltaicModel(path=path).custom_predict(new_obs)
    biomass_prediction = BiomassModel(path=path).custom_predict(new_obs)
    res = {}
    for ih in range(len(hours_of_prediction)):
        res[hours_of_prediction[ih]] = {
            'hydro': hydro_prediction[ih],
            'geothermal': geothermal_prediction[ih],
            'wind': wind_prediction[ih],
            'photovoltaic': photovoltaic_prediction[ih],
            'biomass': biomass_prediction[ih], }
    return res

def process_thermal_mqtt(predictions: dict, path: str) -> PandasDataFrame:
    """
    Takes the energy predictions from the mqtt broker, fetch the load
    and perform the prediction of thermal sorce.
    """
    thermal = ThermalModel(path=path)
    loads = dbs.RedisDB().get_loads(list(predictions.keys()))
    thermal_data = thermal.pre_process(predictions, loads)
    columns = ["holiday", "total_load", "Sum_of_rest_GW", "str_month", 'date']
    thermal_prediction = thermal.custom_predict(thermal_data[columns])
    return pd.DataFrame(thermal_prediction, thermal_data["date"].unique())

def process_results(msg: dict) -> Tuple[NumpyArray, NumpyArray]:
    """
    Takes the energy predictions from the mqtt broker, fetch the load
    and perform the prediction of thermal sorce.
    """
    new_obs = pd.DataFrame.from_dict(msg)
    new_obs["date"] = new_obs.index
    return new_obs['0'].values, (pd.to_datetime(new_obs['date']).dt.strftime("%Y/%m/%d %H:%M:%S"))

def predict_load(broker: str, path: str = None) -> None:
    """
    create the load observation perform the prediction and send
    them to the mqtt broker.
    """
    load_to_predict, dates = dbs.HolidayDetector().prepare_load_to_predict()
    load_tot, res = LoadModel(path=path).custom_predict(load_to_predict), {}
    for iday in range(len(dates)): res[dates[iday]] = dict(load=load_tot[iday])
    c_mqtt.MqttManager(broker=broker).publish(data=res, is_dict=False, topic="Energy/Load/")


def main():
    parser = argparse.ArgumentParser(description='Predictive Models')
    parser.add_argument('-m', '--model_to_train', default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"],
                        help=""" Pick the model that you want to train! All the trained models will be defaults, selected by us during the data exploration. """)
    parser.add_argument('-l', '--sendload', default=True, type=bool, help="Create the load prediction and send it to MQTT")
    parser.add_argument('-b', '--broker', default='localhost', choices=['localhost', 'aws'])
    parser.add_argument('-r', '--rate', default='auto', help="""Frequencies express in hours, if do not specified will use the best rate found up to now""")
    parser.add_argument('-p', '--path', default='Models/', help="""Path to find the models""")
    parser.add_argument('-a', '--aug', default='yes', help="""Slightly increase artificially the number of obs to avoid problems
                                                                when train the model near the end of the month""")
    parse = parser.parse_args()
    topic_available = ['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]
    if parse.model_to_train and parse.model_to_train not in topic_available: print(f"Model not found"), exit()
    elif parse.model_to_train: train_models(model=parse.model_to_train, path=parse.path)
    else:
        if parse.rate == 'auto': waiting_time = 60 * 60 * 12  # each 12 hours (do not depend on meteo)
        elif type(parse.rate) != int: raise ValueError('Required INT')
        else: waiting_time = parse.rate * 60 * 60
        while True:
            predict_load(broker=parse.broker, path=parse.path)
            time.sleep(waiting_time)


if __name__ == "__main__":
    main()
