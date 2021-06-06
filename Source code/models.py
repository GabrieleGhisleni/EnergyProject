import datetime
import pandas as pd
import numpy as np
import time
import torch.nn.functional as F
from torch.utils.data import Dataset
import torch as T
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.tree import DecisionTreeRegressor
#from sklearn.compose import make_column_selector ! check
from sklearn.pipeline import make_pipeline
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
import joblib, os
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from typing import TypeVar, Tuple,List
from mqtt import *
from managers_meteo import *
from meteo_classes import *
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")
NumpyArray = TypeVar("numpy.ndarray")
###################################################################################################################

class GeoThermalModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/geothermal_linear.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_geothermal_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.humidity,temp,rain_1h,directnormalirradiance,globalhorizontalirradiance_2,
        energy_generation.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
        	WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
        	WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
        	WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
        END as str_month,
		CASE EXTRACT(HOUR FROM energy_meteo.date)
			WHEN '1' THEN  '01 AM'
			WHEN '2' THEN  '02 AM'
			WHEN '3' THEN  '03 AM'
			WHEN '4' THEN  '04 AM'
			WHEN '5' THEN  '05 AM'
			WHEN '6' THEN  '06 AM'
			WHEN '7' THEN  '07 AM'
			WHEN '8' THEN  '08 AM'
			WHEN '9' THEN  '09 AM'
			WHEN '10' THEN  '10 AM'
			WHEN '11' THEN  '11 AM'
			WHEN '12' THEN  '00 AM'
			WHEN '13' THEN  '13 PM'
			WHEN '14' THEN  '14 PM'
			WHEN '15' THEN  '15 PM'
			WHEN '16' THEN  '16 PM'
			WHEN '17' THEN  '17 PM'
			WHEN '18' THEN  '18 PM'
			WHEN '19' THEN  '19 PM'
			WHEN '20' THEN  '20 PM'
			WHEN '21' THEN  '21 PM'
			WHEN '22' THEN  '22 PM'
			WHEN '23' THEN  '23 PM'
			WHEN '0' THEN  '12 PM'
        END as str_hour
        FROM energy_generation
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_generation.date
        where energy_generation.energy_source = 'geothermal';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","rain_1h","temp", "directnormalirradiance","globalhorizontalirradiance_2",
                         "str_hour", "str_month"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour","str_month"]),
                                                  remainder='passthrough')
            model = LinearRegression()
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_geothermal_data()
            print(f"Training the GeoThermalModel --> on {len(pred)} observations")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/geothermal_linear.mod')


    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """
        new_obs = new_observation[["humidity","rain_1h","temp", "directnormalirradiance","globalhorizontalirradiance_2",
                         "str_hour", "str_month"]]
        today_prediction = self.pipeline.predict(new_obs)
        return today_prediction

class BiomassModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/biomass_forest.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_biomass_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.temp,rain_1h,globalhorizontalirradiance_2,directnormalirradiance_2,diffusehorizontalirradiance_2,
            energy_generation.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
        	WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
        	WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
        	WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
        END as str_month,
		CASE EXTRACT(HOUR FROM energy_meteo.date)
			WHEN '1' THEN  '01 AM'
			WHEN '2' THEN  '02 AM'
			WHEN '3' THEN  '03 AM'
			WHEN '4' THEN  '04 AM'
			WHEN '5' THEN  '05 AM'
			WHEN '6' THEN  '06 AM'
			WHEN '7' THEN  '07 AM'
			WHEN '8' THEN  '08 AM'
			WHEN '9' THEN  '09 AM'
			WHEN '10' THEN  '10 AM'
			WHEN '11' THEN  '11 AM'
			WHEN '12' THEN  '00 AM'
			WHEN '13' THEN  '13 PM'
			WHEN '14' THEN  '14 PM'
			WHEN '15' THEN  '15 PM'
			WHEN '16' THEN  '16 PM'
			WHEN '17' THEN  '17 PM'
			WHEN '18' THEN  '18 PM'
			WHEN '19' THEN  '19 PM'
			WHEN '20' THEN  '20 PM'
			WHEN '21' THEN  '21 PM'
			WHEN '22' THEN  '22 PM'
			WHEN '23' THEN  '23 PM'
			WHEN '0' THEN  '12 PM'
        END as str_hour
        FROM energy_generation
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_generation.date
        where energy_generation.energy_source = 'biomass';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["rain_1h","temp", "globalhorizontalirradiance_2","directnormalirradiance_2",
                         "diffusehorizontalirradiance_2","str_hour", "str_month"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour","str_month"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_biomass_data()
            print(f"Training the BiomassModel --> on {len(pred)} observations")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/biomass_forest.mod')

    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """
        new_obs = new_observation[["rain_1h","temp", "globalhorizontalirradiance_2","directnormalirradiance_2",
                         "diffusehorizontalirradiance_2","str_hour", "str_month"]]

        today_prediction = self.pipeline.predict(new_obs)
        return today_prediction

###################################################################################################################
class Net(T.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.hid1 = T.nn.Linear(5, 50)
        self.hid2 = T.nn.Linear(50, 10)
        self.hid4 = T.nn.Linear(10, 5)
        self.oupt = T.nn.Linear(5, 1)

    def forward(self, x):
        z = T.relu(self.hid1(x))
        z = T.relu(self.hid2(z))
        z = T.relu(self.hid4(z))
        z = self.oupt(z)
        return z

class DataLoader(Dataset):
    def __init__(self, src_file):
        device = T.device("cuda" if T.cuda.is_available() else "cpu")
        all_xy = src_file
        tmp_x = all_xy.loc[:, ["directnormalirradiance", "diffusehorizontalirradiance",
                               "globalhorizontalirradiance_2", "directnormalirradiance_2",
                               "diffusehorizontalirradiance_2"]]

        tmp_y = all_xy.loc[:, ["generation"]].values.reshape(-1, 1)
        self.x_data = T.tensor(tmp_x.values, dtype=T.float32).to(device)
        self.y_data = T.tensor(tmp_y, dtype=T.float32).to(device)

    def __len__(self):  return len(self.x_data)

    def __getitem__(self, idx):
        preds = self.x_data[idx, :]
        price = self.y_data[idx, :]
        return (preds, price)

class PhotovoltaicModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/photovoltaic_NN.tth"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        self.device = T.device("cuda" if T.cuda.is_available() else "cpu")
        if os.path.exists(path):
            self.model = Net()
            self.model.load_state_dict(T.load(path)["load_state_dict"])
        else:
            print(f"Do not found an already existing model at {path}")

    def train(self, net, train_ds, bacht_size=24, epochs=500, lrn_rate=0.0001):
        bacht_size = bacht_size
        train_ldr = T.utils.data.DataLoader(train_ds, batch_size=bacht_size, shuffle=True)
        net.to(self.device)
        epochs = epochs
        ep_log_interval = 50
        lrn_rate = lrn_rate
        loss_func = T.nn.MSELoss()
        optimizer = T.optim.Adam(net.parameters(), lr=lrn_rate)
        print("\nbat_size = %3d " % bacht_size)
        print("loss = " + str(loss_func))
        print("optimizer = Adam")
        print("max_epochs = %3d " % epochs)
        print("lrn_rate = %0.4f " % lrn_rate)
        print("\nStarting training with saved checkpoints")
        net.train()
        for epoch in tqdm(range(0, epochs), position=0, leave=True):
            epoch_loss = 0
            for (batch_idx, batch) in enumerate(train_ldr):
                (X, Y) = batch  # (predictors, targets)
                optimizer.zero_grad()  # prepare gradients
                oupt = net(X)  # predicted prices
                loss_val = loss_func(oupt, Y)  # avg per item in batch
                epoch_loss += loss_val.item()  # accumulate avgs
                loss_val.backward()  # compute gradients
                optimizer.step()  # update wts
            if epoch % ep_log_interval == 0:
                print("epoch = %4d   loss = %0.4f" % (epoch, epoch_loss))
                T.save({'epoch': epoch,
                    'load_state_dict': net.state_dict(),
                    'optimizer_state': optimizer.state_dict()}, "../Models/photovoltaic_NN.tth")


        print("Done")



    def get_photovoltaic_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.humidity,temp,rain_1h,snow_1h,wind_deg,directnormalirradiance,
            diffusehorizontalirradiance,globalhorizontalirradiance_2,directnormalirradiance_2,diffusehorizontalirradiance_2,
            energy_generation.generation
            FROM energy_generation
            INNER JOIN energy_meteo
            ON energy_meteo.date = energy_generation.date
            where energy_generation.energy_source = 'photovoltaic';"""

        df = pd.read_sql_query(query, con=self.engine)
        return df


    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        print()
        input_result = input('''This is a Neural Network, if you have not a GPU it will take a lot of time are you sure to train? [yes/no]''')
        if input_result.lower() == 'yes' or input_result.lower() == "y":
            model = Net()
            data = self.get_photovoltaic_data()
            torch_dataset = DataLoader(data)
            self.train(model, train_ds=torch_dataset, bacht_size=24, epochs=10000, lrn_rate=0.0001)


    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """
        new_obs = new_observation[["directnormalirradiance", "diffusehorizontalirradiance",
                                   "globalhorizontalirradiance_2","directnormalirradiance_2",
                                    "diffusehorizontalirradiance_2"]]
        res = []
        for i, row in new_obs.iterrows():
            tensor_row = T.tensor(row.values, dtype=T.float32).to(self.device)
            with T.no_grad():
                pred = self.model(tensor_row)
                pred_p = abs(pred.to(self.device).tolist()[0])
                res.append(np.round(pred_p,4))
        return res

###################################################################################################################

class WindModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/wind_forest.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_wind_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.humidity,wind_deg,wind_speed,diffusehorizontalirradiance_2, energy_generation.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
                WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
                WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
                WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
            END as str_month     
            FROM energy_generation
            INNER JOIN energy_meteo
            ON energy_meteo.date = energy_generation.date
            where energy_generation.energy_source = 'wind';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","wind_deg", "wind_speed","diffusehorizontalirradiance_2", "str_month"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_month"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_wind_data()
            print(f"Training the WindModel --> on {len(pred)} observations")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/wind_forest.mod')


    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """
        new_obs = new_observation[["humidity","wind_deg", "wind_speed",
                                   "diffusehorizontalirradiance_2", "str_month"]]
        today_prediction = self.pipeline.predict(new_obs)
        return today_prediction

###################################################################################################################

class HydroModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/hydro_r_forest.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_hydro_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.humidity,temp,rain_1h,directnormalirradiance,globalhorizontalirradiance_2, energy_generation.generation,
        CASE EXTRACT(HOUR FROM energy_meteo.date)
			WHEN '1' THEN  '01 AM'
			WHEN '2' THEN  '02 AM'
			WHEN '3' THEN  '03 AM'
			WHEN '4' THEN  '04 AM'
			WHEN '5' THEN  '05 AM'
			WHEN '6' THEN  '06 AM'
			WHEN '7' THEN  '07 AM'
			WHEN '8' THEN  '08 AM'
			WHEN '9' THEN  '09 AM'
			WHEN '10' THEN  '10 AM'
			WHEN '11' THEN  '11 AM'
			WHEN '12' THEN  '00 AM'
			WHEN '13' THEN  '13 PM'
			WHEN '14' THEN  '14 PM'
			WHEN '15' THEN  '15 PM'
			WHEN '16' THEN  '16 PM'
			WHEN '17' THEN  '17 PM'
			WHEN '18' THEN  '18 PM'
			WHEN '19' THEN  '19 PM'
			WHEN '20' THEN  '20 PM'
			WHEN '21' THEN  '21 PM'
			WHEN '22' THEN  '22 PM'
			WHEN '23' THEN  '23 PM'
			WHEN '0' THEN  '12 PM'
        END as str_hour
        FROM energy_generation
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_generation.date
        where energy_generation.energy_source = 'hydro';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","temp", "rain_1h","directnormalirradiance", "globalhorizontalirradiance_2","str_hour"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_hydro_data()
            print(f"Training the HydroModel --> on {len(pred)} observations")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/hydro_r_forest.mod')



    def custom_predict(self, new_observation: PandasDataFrame) -> NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """
        new_obs = new_observation[["humidity","temp", "rain_1h",
                                   "directnormalirradiance", "globalhorizontalirradiance_2","str_hour"]]
        today_prediction = self.pipeline.predict(new_obs)
        return today_prediction

###################################################################################################################

class ThermalModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/thermal_forest.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_thermal_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query_rest = f"""SELECT date, SUM(generation) AS Sum_of_rest_GW
                        FROM energy_generation 
                        where energy_source != 'thermal'
                        GROUP BY date;"""

        query_thermal = """
        SELECT holiday, total_load, generation, energy_load.`date`,
                    CASE EXTRACT(MONTH FROM energy_load.`date`)
                                        WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
                                        WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
                                        WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
                    END as str_month    
                    FROM energy_load
                    INNER JOIN energy_generation
                    ON energy_load.date = energy_generation.date
                                        where energy_source = 'thermal';"""
        df_rest = pd.read_sql_query(query_rest, con=self.engine)
        df_thermal = pd.read_sql_query(query_thermal, con=self.engine)
        final = pd.merge(df_rest, df_thermal, on='date')
        #df.to_csv("aggregate_only.csv")
        predictors = final[["holiday","total_load", "Sum_of_rest_GW","str_month"]]
        target = final[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["holiday", "str_month"]),
                                                  remainder='passthrough')
            model = GradientBoostingRegressor(random_state=42)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_thermal_data()
            print(f"Training the TermalModel --> on {len(pred)} observations")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/thermal_forest.mod')



    def pre_process_for_thermal(self, predictions:dict):
        tmp = []
        predictions = predictions
        for key in predictions:
            sum_of_rest, load = 0, 0
            holiday = check_holiday_day(key)
            str_month = datetime.datetime.strptime(key, "%Y/%m/%d %H:%M:%S").strftime("%B").lower()
            for energy in predictions[key]:
                if energy == 'load':  load = predictions[key][energy]
                else: sum_of_rest += predictions[key][energy]
            tmp.append([holiday, sum_of_rest, load, str_month, key])
        df = pd.DataFrame(tmp).rename(
            columns={0: 'holiday', 1: 'Sum_of_rest_GW', 2: 'total_load', 3: 'str_month', 4: 'date'})
        return df

    def custom_predict(self,new_observation) -> NumpyArray:
        """
        HOLY FUCK
        """
        new_obs = new_observation[["holiday","total_load", "Sum_of_rest_GW","str_month"]]
        today_prediction = self.pipeline.predict(new_obs)
        return today_prediction

###################################################################################################################

class LoadModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="../Models/load_forest.mod"):
        self.engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")


    def __get_training_data(self, table_name="energy_load")->List[PandasDataFrame]:
        """
        Get the data from the sql database and return those as dataframe to
        be used only for fitting the model! it is an internal function so not
        calleble from outside.
        """
        self.engine.connect()
        query = f"""SELECT total_load, holiday,date,
        CASE EXTRACT(MONTH FROM date)
        	WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
        	WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
        	WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
        END as str_month,
        CASE EXTRACT(HOUR FROM date)
        	WHEN '1' THEN  '1'	WHEN '2' THEN  '2'	WHEN '3' THEN  '3'	WHEN '4' THEN  '4'
        	WHEN '5' THEN  '5'	WHEN '6' THEN  '6'	WHEN '7' THEN  '7'	WHEN '8' THEN  '8'
        	WHEN '9' THEN  '9'	WHEN '10' THEN  '10'	WHEN '11' THEN  '11'	WHEN '12' THEN  '12'
        	WHEN '13' THEN  '13'	WHEN '14' THEN  '14'	WHEN '15' THEN  '15'	WHEN '16' THEN  '16'
        	WHEN '17' THEN  '17'	WHEN '18' THEN  '18'	WHEN '19' THEN  '19'	WHEN '20' THEN  '20'
        	WHEN '21' THEN  '21'	WHEN '22' THEN  '22'	WHEN '23' THEN  '23'	WHEN '0' THEN  '0'    
        END as str_hour
        from {table_name}
        WHERE EXTRACT(MINUTE FROM date) ="00";"""
        df = pd.read_sql_query(query, self.engine)
        predictors = df[["holiday","str_hour","str_month"]]
        target = df[["total_load"]]
        return (predictors,target)

    def custom_fit_model(self, force="force")->None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':

            pre_process = make_column_transformer((OneHotEncoder(),
                                                        ["holiday", "str_hour", "str_month"]),
                                                       remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.__get_training_data()
            print(f"Training the LoadModel --> on {len(pred)} observations")
            print("Extracted the data from sql --> Fitting")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, '../Models/load_forest.mod')


    def custom_predict(self, new_observation:PandasDataFrame)->NumpyArray:
        """
        Function that given a pandas dataframe having three columns as 'holiday',
        'str_hour' and 'str_month' preprocess the dataframe perfoming the encoding
        operation and predict the result.
        """

        new_observation.drop(columns=['date'], inplace=True)
        today_prediction = self.pipeline.predict(new_observation)
        return today_prediction

    def plot_prediction(self, date:PandasDataFrame)->None:
        """
        Given a PandasDataFrame obtained with create_load_to_predict
        it plot the result as a line plot!
        """
        data = date["date"].iloc[0]
        if data == str(dt.datetime.today().date()): data= 'Today'
        if data == str(dt.datetime.today().date()+dt.timedelta(days=1)): data= 'Tomorrow'
        predictions = self.custom_predict(date)
        hours = range(0, 24)
        plt.plot(hours, predictions)
        plt.title(f"Results of the prediction for {data}:")
        plt.show()

###################################################################################################################

def create_load_to_predict(dates:List[str])->PandasDataFrame:
    """
    Auxiliary function to get the requested data.
    Given the date which could be 'today', 'tomorrow' or a date in
    "%Y-"%m"-%d" it returns a pandas data frame having the rights
    columns to be processed by the model: 'holiday' if the day is an
    holiday day, 24 observation (one per hour) and the month name.
    """
    italian_holiday = {"01-01", "06-01", "25-04", "01-05",
                       "02-06", "15-08", "01-10", "08-12", "25-12", "26-12"}
    easter = {'2041-22-04', '2028-17-04', '2049-26-04', '2046-26-03', '2037-6-04', '2035-26-03',
              '2036-14-04', '2034-10-04', '2045-10-04', '2039-11-04', '2032-29-03', '2030-22-04',
              '2042-7-04', '2021-5-04', '2040-2-04', '2024-01-04', '2025-21-04', '2029-2-04',
              '2038-26-04', '2027-29-03', '2044-18-04', '2033-18-04', '2031-14-04', '2023-10-04',
              '2050-11-04', '2048-6-04', '2022-18-04', '2047-15-04', '2043-30-03', '2026-6-04'}

    hours = [datetime.datetime.strptime(date,  "%Y/%m/%d %H:%M:%S").strftime("%H") for date in dates]
    res = []
    for date in dates:
        holiday = 'no'
        if date.split(" ")[0] in easter or date.split(" ")[0][4:] in italian_holiday: holiday='yes'
        d =  datetime.datetime.strptime(date,  "%Y/%m/%d %H:%M:%S")
        if d.strftime("%A")=='Sunday':holiday='sunday'
        if d.strftime("%A") == 'Saturday': holiday = 'saturday'
        res.append([holiday, str(date), str(int(d.strftime("%H"))), d.strftime("%B").lower()])

    df_today = pd.DataFrame(res)
    df_today.rename(columns={0: "holiday", 1: "date", 2: "str_hour", 3: "str_month"}, inplace=True)
    return df_today

def create_load_to_predict_old(day="today")->PandasDataFrame:
    """
    Auxiliary function to get the requested data.
    Given the date which could be 'today', 'tomorrow' or a date in
    "%Y-"%m"-%d" it returns a pandas data frame having the rights
    columns to be processed by the model: 'holiday' if the day is an
    holiday day, 24 observation (one per hour) and the month name.
    """
    italian_holiday = {"01-01", "06-01", "25-04", "01-05",
                       "02-06", "15-08", "01-10", "08-12", "25-12", "26-12"}
    easter = {'2041-22-04', '2028-17-04', '2049-26-04', '2046-26-03', '2037-6-04', '2035-26-03',
              '2036-14-04', '2034-10-04', '2045-10-04', '2039-11-04', '2032-29-03', '2030-22-04',
              '2042-7-04', '2021-5-04', '2040-2-04', '2024-01-04', '2025-21-04', '2029-2-04',
              '2038-26-04', '2027-29-03', '2044-18-04', '2033-18-04', '2031-14-04', '2023-10-04',
              '2050-11-04', '2048-6-04', '2022-18-04', '2047-15-04', '2043-30-03', '2026-6-04'}
    if day == "today":
        today = dt.datetime.today().date()
        tomorrow = today + dt.timedelta(days=1)
        holiday_today = 'no'
        if today.strftime('%A')=="Sunday": holiday_today = "sunday"
        if today.strftime('%A')=="Saturday": holiday_today = "saturday"
        if today in easter: holiday_today="holiday"
        if today.strftime('%d-%m') in italian_holiday: holiday_today="holiday"
        today_res = [[holiday_today, str(today), str(hour), today.strftime("%B").lower()] for hour in range(0,24)]
        df_today = pd.DataFrame(today_res)
        df_today.rename(columns={0:"holiday", 1:"date", 2:"str_hour",3:"str_month"}, inplace=True)
        return df_today
    elif day == "tomorrow":
        tomorrow = dt.datetime.today().date() + dt.timedelta(days=1)
        holiday_tomorrow="no"
        if tomorrow.strftime('%A')=="Sunday": holiday_tomorrow = "sunday"
        if tomorrow.strftime('%A')=="Saturday": holiday_tomorrow = "saturday"
        if tomorrow in easter: holiday_tomorrow="holiday"
        if tomorrow.strftime('%d-%m') in italian_holiday: holiday_tomorrow="holiday"
        tomorrow_res = [[holiday_tomorrow, str(tomorrow), str(hour), tomorrow.strftime("%B").lower()] for hour in range(0,24)]
        df_tomorrow = pd.DataFrame(tomorrow_res)
        df_tomorrow.rename(columns={0:"holiday", 1:"date", 2:"str_hour",3:"str_month"}, inplace=True)
        return df_tomorrow
    else:
        try:
            day = dt.datetime.strptime(day, "%Y-%m-%d")
            holiday = 'no'
            if day.strftime('%A') == "Sunday": holiday = "sunday"
            if day.strftime('%A') == "Saturday": holiday = "saturday"
            if day in easter: holiday = "holiday"
            if day.strftime('%d-%m') in italian_holiday: holiday = "holiday"
            day_res = [[holiday, str(day), str(hour), day.strftime("%B").lower()] for hour in range(0, 24)]
            df_day = pd.DataFrame(day_res)
            df_day.rename(columns={0:"holiday", 1:"date", 2:"str_hour",3:"str_month"}, inplace=True)
            return df_day
        except Exception:
            print("Accept only format '%Y-%m-%d'")

def check_holiday_day(day_string_format):
    italian_holiday = {"01-01", "06-01", "25-04", "01-05",
                       "02-06", "15-08", "01-10", "08-12", "25-12", "26-12"}
    easter = {'2041-22-04', '2028-17-04', '2049-26-04', '2046-26-03', '2037-6-04', '2035-26-03',
              '2036-14-04', '2034-10-04', '2045-10-04', '2039-11-04', '2032-29-03', '2030-22-04',
              '2042-7-04', '2021-5-04', '2040-2-04', '2024-01-04', '2025-21-04', '2029-2-04',
              '2038-26-04', '2027-29-03', '2044-18-04', '2033-18-04', '2031-14-04', '2023-10-04',
              '2050-11-04', '2048-6-04', '2022-18-04', '2047-15-04', '2043-30-03', '2026-6-04'}

    day = datetime.datetime.strptime(day_string_format, "%Y/%m/%d %H:%M:%S")
    holiday_today = 'no'
    if day.strftime('%A')=="Sunday": holiday_today = "sunday"
    if day.strftime('%A')=="Saturday": holiday_today = "saturday"
    if day in easter: holiday_today="holiday"
    if day.strftime('%d-%m') in italian_holiday: holiday_today="holiday"
    return holiday_today

def prepare_forecast_to_send()->None:
    meteo_forecast = MeteoData.forecast_from_dict_to_class(
        city=GetMeteoData().fetching_forecast_meteo())
    radiation_forecast = MeteoRadiationData.forecast_from_dict_to_class(
        city=GetMeteoData().fetching_forecast_solar_radiation())

    forecaster = ForecastData()
    meteo = forecaster.update_forecast_meteo(forecast_meteo=meteo_forecast)
    rad = forecaster.update_forecast_radiation(forecast_radiations=radiation_forecast)
    new_obs = forecaster.merge_forecast(radiations_df=rad, meteo_df=meteo)
    MqttManager().publish_forecast(new_obs)


def train_all():
    PhotovoltaicModel().custom_fit_model()

    HydroModel().custom_fit_model()
    LoadModel().custom_fit_model()
    ThermalModel().custom_fit_model()
    PhotovoltaicModel().custom_fit_model()
    BiomassModel().custom_fit_model()
    GeoThermalModel().custom_fit_model()
    WindModel().custom_fit_model()

###################################################################################################################
if __name__ == "__main__":
    #train_all()
    prepare_forecast_to_send()
    ####