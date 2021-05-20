from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
#from sklearn.compose import make_column_selector ! check
from sklearn.pipeline import make_pipeline
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
import joblib, os
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from typing import TypeVar, Tuple,List
from mqtt import *
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")
NumpyArray = TypeVar("numpy.ndarray")

class GeoThermalModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/geothermal_linear.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]} <--- ")
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
        energy_production.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
        	WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
        	WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
        	WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
        END as str_month,
		CASE EXTRACT(HOUR FROM energy_meteo.date)
			WHEN '1' THEN  '1AM'
			WHEN '2' THEN  '2AM'
			WHEN '3' THEN  '3AM'
			WHEN '4' THEN  '4AM'
			WHEN '5' THEN  '5AM'
			WHEN '6' THEN  '6AM'
			WHEN '7' THEN  '7AM'
			WHEN '8' THEN  '8AM'
			WHEN '9' THEN  '9AM'
			WHEN '10' THEN  '10AM'
			WHEN '11' THEN  '11AM'
			WHEN '12' THEN  '12PM'
			WHEN '13' THEN  '1PM'
			WHEN '14' THEN  '2PM'
			WHEN '15' THEN  '3PM'
			WHEN '16' THEN  '4PM'
			WHEN '17' THEN  '5PM'
			WHEN '18' THEN  '6PM'
			WHEN '19' THEN  '7PM'
			WHEN '20' THEN  '8PM'
			WHEN '21' THEN  '9PM'
			WHEN '22' THEN  '10PM'
			WHEN '23' THEN  '11PM'
			WHEN '0' THEN  '12AM'
        END as str_hour
        FROM energy_production
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_production.date
        where energy_production.energy_source = 'geothermal';"""
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
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour","str_month"]),
                                                  remainder='passthrough')
            model = LinearRegression()
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_geothermal_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/geothermal_linear.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")

class BiomassModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/biomass_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]} <--- ")
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
            energy_production.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
        	WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
        	WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
        	WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
        END as str_month,
		CASE EXTRACT(HOUR FROM energy_meteo.date)
			WHEN '1' THEN  '1AM'
			WHEN '2' THEN  '2AM'
			WHEN '3' THEN  '3AM'
			WHEN '4' THEN  '4AM'
			WHEN '5' THEN  '5AM'
			WHEN '6' THEN  '6AM'
			WHEN '7' THEN  '7AM'
			WHEN '8' THEN  '8AM'
			WHEN '9' THEN  '9AM'
			WHEN '10' THEN  '10AM'
			WHEN '11' THEN  '11AM'
			WHEN '12' THEN  '12PM'
			WHEN '13' THEN  '1PM'
			WHEN '14' THEN  '2PM'
			WHEN '15' THEN  '3PM'
			WHEN '16' THEN  '4PM'
			WHEN '17' THEN  '5PM'
			WHEN '18' THEN  '6PM'
			WHEN '19' THEN  '7PM'
			WHEN '20' THEN  '8PM'
			WHEN '21' THEN  '9PM'
			WHEN '22' THEN  '10PM'
			WHEN '23' THEN  '11PM'
			WHEN '0' THEN  '12AM'
        END as str_hour
        FROM energy_production
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_production.date
        where energy_production.energy_source = 'biomass';"""
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
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour","str_month"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_biomass_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/biomass_forest.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")

class PhotovoltaicModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/photovoltaic_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]}<--- ")
            self.pipeline = joblib.load(path)
        else:
            print(f"Do not found an already existing model at {path}")

    def get_photovoltaid_data(self):
        """
        Since the thermal is higly correlated with the load we have to extract
        the data from the thermal table and inner join them with the load table and
        add also the str_name of the month which is an important variable to kept
        explicit!
        """
        self.engine.connect()
        query = f"""SELECT energy_meteo.humidity,temp,rain_1h,snow_1h,wind_deg,directnormalirradiance,
            diffusehorizontalirradiance,globalhorizontalirradiance_2,directnormalirradiance_2,diffusehorizontalirradiance_2,
            energy_production.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
                WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
                WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
                WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
            END as str_month,
		    CASE EXTRACT(HOUR FROM energy_meteo.date)
                WHEN '1' THEN  '1AM'
                WHEN '2' THEN  '2AM'
                WHEN '3' THEN  '3AM'
                WHEN '4' THEN  '4AM'
                WHEN '5' THEN  '5AM'
                WHEN '6' THEN  '6AM'
                WHEN '7' THEN  '7AM'
                WHEN '8' THEN  '8AM'
                WHEN '9' THEN  '9AM'
                WHEN '10' THEN  '10AM'
                WHEN '11' THEN  '11AM'
                WHEN '12' THEN  '12PM'
                WHEN '13' THEN  '1PM'
                WHEN '14' THEN  '2PM'
                WHEN '15' THEN  '3PM'
                WHEN '16' THEN  '4PM'
                WHEN '17' THEN  '5PM'
                WHEN '18' THEN  '6PM'
                WHEN '19' THEN  '7PM'
                WHEN '20' THEN  '8PM'
                WHEN '21' THEN  '9PM'
                WHEN '22' THEN  '10PM'
                WHEN '23' THEN  '11PM'
                WHEN '0' THEN  '12AM'
            END as str_hour
            FROM energy_production
            INNER JOIN energy_meteo
            ON energy_meteo.date = energy_production.date
            where energy_production.energy_source = 'photovoltaic';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","temp", "rain_1h","snow_1h", "wind_deg","directnormalirradiance",
                         "diffusehorizontalirradiance","globalhorizontalirradiance_2","directnormalirradiance_2",
                         "diffusehorizontalirradiance_2","str_month","str_hour"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_month","str_hour"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_photovoltaid_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/photovoltaic_forest.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")


class WindModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/wind_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]}<--- ")
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
        query = f"""SELECT energy_meteo.humidity,wind_deg,wind_speed,diffusehorizontalirradiance_2, energy_production.generation,
            CASE EXTRACT(MONTH FROM energy_meteo.date)
                WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
                WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
                WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
            END as str_month     
            FROM energy_production
            INNER JOIN energy_meteo
            ON energy_meteo.date = energy_production.date
            where energy_production.energy_source = 'wind';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","wind_deg", "wind_speed","diffusehorizontalirradiance_2", "str_month"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_month"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_wind_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/wind_forest.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")


class HydroModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/hydro_r_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]}<--- ")
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
        query = f"""SELECT energy_meteo.humidity,temp,rain_1h,directnormalirradiance,globalhorizontalirradiance_2, energy_production.generation,
        CASE EXTRACT(HOUR FROM energy_meteo.date)
            WHEN '1' THEN  '1AM'
            WHEN '2' THEN  '2AM'
            WHEN '3' THEN  '3AM'
            WHEN '4' THEN  '4AM'
            WHEN '5' THEN  '5AM'
            WHEN '6' THEN  '6AM'
            WHEN '7' THEN  '7AM'
            WHEN '8' THEN  '8AM'
            WHEN '9' THEN  '9AM'
            WHEN '10' THEN  '10AM'
            WHEN '11' THEN  '11AM'
            WHEN '12' THEN  '12PM'
            WHEN '13' THEN  '1PM'
            WHEN '14' THEN  '2PM'
            WHEN '15' THEN  '3PM'
            WHEN '16' THEN  '4PM'
            WHEN '17' THEN  '5PM'
            WHEN '18' THEN  '6PM'
            WHEN '19' THEN  '7PM'
            WHEN '20' THEN  '8PM'
            WHEN '21' THEN  '9PM'
            WHEN '22' THEN  '10PM'
            WHEN '23' THEN  '11PM'
            WHEN '0' THEN  '12AM'
        END as str_hour
        FROM energy_production
        INNER JOIN energy_meteo
        ON energy_meteo.date = energy_production.date
        where energy_production.energy_source = 'hydro';"""
        df = pd.read_sql_query(query, con=self.engine)
        predictors = df[["humidity","temp", "rain_1h","directnormalirradiance", "globalhorizontalirradiance_2","str_hour"]]
        target = df[["generation"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["str_hour"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.get_hydro_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/hydro_r_forest.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")


class ThermalModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/thermal_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready {path.split('/')[-1]}<--- ")
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
        query = f"""SELECT holiday, total_load, thermal_GW, Sum_of_rest_GW, energy_load.`date`,
                    CASE EXTRACT(MONTH FROM energy_load.`date`)
                                        WHEN  '1' THEN  'january'	WHEN 2 THEN  'february' WHEN '3' THEN  'march'	WHEN '4' THEN  'april'
                                        WHEN '5' THEN  'may'	WHEN '6' THEN  'june'	WHEN '7' THEN  'july'	WHEN '8' THEN  'august'
                                        WHEN '9' THEN  'september'	WHEN '10' THEN  'october'	WHEN '11' THEN  'november'	WHEN '12' THEN  'december'
                    END as str_month    
                    FROM energy_load
                    INNER JOIN energy_thermal
                    ON energy_load.date = energy_thermal.date;"""
        df = pd.read_sql_query(query, con=self.engine)
        #df.to_csv("aggregate_only.csv")
        predictors = df[["holiday","total_load", "Sum_of_rest_GW","str_month"]]
        target = df[["thermal_GW"]]
        return (predictors,target)

    def custom_fit_model(self, force="force") -> None:
        """
        It took all the database and trains the model!
        """
        if force == 'force':
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                   ["holiday", "str_month"]),
                                                  remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.__get_thermal_data()
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/thermal_forest.mod')
            print(
                f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")

        def custom_predict(self, generation_prediction:PandasDataFrame, load_prediction:PandasDataFrame) -> NumpyArray:
            """
            HOLY FUCK
            """
            ""



class LoadModel():
    """
    When created the class look up in the specified path for an existing model.
    In case there isn't first fit the model with fit_model!
    """
    def __init__(self, path:str="Models/load_forest.mod"):
        self.engine =  create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
        if os.path.exists(path):
            print(f" --> Model loaded and ready at {path.split('/')[-1]} <--- ")
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
            print(f"--> Training the model, start at {dt.datetime.now()} <--")
            pre_process = make_column_transformer((OneHotEncoder(),
                                                        ["holiday", "str_hour", "str_month"]),
                                                       remainder='passthrough')
            model = RandomForestRegressor(random_state=42, criterion='mse', bootstrap=True)
            self.pipeline = make_pipeline(pre_process, model)
            pred, target = self.__get_training_data()
            print("Extracted the data from sql --> Fitting")
            self.pipeline.fit(pred, target.values.ravel())
            joblib.dump(self.pipeline, 'Models/load_forest.mod')
            print(f"--> Training the model, finished at {dt.datetime.now()}, trained on {len(pred)} observations <--")

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

def create_load_to_predict(day="today")->PandasDataFrame:
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

def pre_process_prediction_today(predictions:List[float])->PandasDataFrame:
    tmp = {}
    for i in range(0,24):
        if i<10:
            tmp[(dt.datetime.now().strftime("%Y-%m-%d")+f" 0{str(i)}:00")] = predictions[i]
        else:
            tmp[((dt.datetime.now().strftime("%Y-%m-%d") + f" {str(i)}:00"))] = predictions[i]
    return tmp

def pre_process_prediction_tomorrow(predictions:List[float])->PandasDataFrame:
    tmp = {}
    for i in range(0,24):
        if i<10:
            tmp[((dt.datetime.now()+dt.timedelta(days=1)).strftime("%Y-%m-%d")+f" 0{str(i)}:00")] = predictions[i]
        else:
            tmp[((dt.datetime.now()+dt.timedelta(days=1)).strftime("%Y-%m-%d")+f" {str(i)}:00")] = predictions[i]
    return tmp

def pre_process_prediction_custom(predictions:List[float])->PandasDataFrame:
    # da implementaer#
    tmp = {}
    for i in range(0,24):
        if i<10:
            tmp[((dt.datetime.now()+dt.timedelta(days=1)).strftime("%Y-%m-%d")+f" 0{str(i)}:00")] = predictions[i]
        else:
            tmp[((dt.datetime.now()+dt.timedelta(days=1)).strftime("%Y-%m-%d")+f" {str(i)}:00")]= predictions[i]
    return (pd.DataFrame(predictions,tmp))

def send_to_mqtt_load_prediction(force="yes"):
    """
    Function that take the prediction for the load of today and tomorrow
    and push this information into the mosquitto broker!
    """
    forest = LoadModel()
    today_pred = forest.custom_predict(create_load_to_predict('today'))
    tomorrow_pred = forest.custom_predict(create_load_to_predict('tomorrow'))
    today_processed = (pre_process_prediction_today(today_pred))
    tomorrow_processed = (pre_process_prediction_tomorrow(tomorrow_pred))
    tmp = [today_processed]
    tmp.append(tomorrow_processed)
    MqttManager().publish_load_prediction(tmp)

if __name__ == "__main__":
    ""
    # HydroModel().custom_fit_model()
    # WindModel().custom_fit_model()
    # PhotovoltaicModel().custom_fit_model()
    # BiomassModel().custom_fit_model()
    # GeoThermalModel().custom_fit_model()
    # LoadModel().custom_fit_model()