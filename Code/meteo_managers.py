import json, os, datetime, argparse, redis, sqlalchemy, time
from typing import List, Tuple
import pandas as pd; import datetime as dt, requests
from pandas import DataFrame as PandasDataFrame
from pandas import Series as PandasSeries
from numpy import array as NumpyArray
from Code.meteo_class import MeteoData
import Code.meteo_collector as collector
import Code.mqtt_manager as c_mqtt


class RedisDB:
    """
    class created to handle the files with Redis database.
    Since we use redis only to display data we set an expiration
    time on the observation. by default they will be available
    for 24 hours than they will expire.
    """
    def __init__(self, hours_expiration: int = 24):
        self.host = os.environ.get('REDIS_HOST')
        self.port = os.getenv('REDIS_PORT', 6379)
        self.time_expire = (60*60) * hours_expiration
        self.redis = redis.StrictRedis(host=self.host, port=self.port, charset="utf-8", decode_responses=True)

    def set_load(self, data: dict) -> None:
        """
        takes the load predictions and store them into the db. the prediction
        that are already present will be replaced by the latest, this data also
        have an expiration time that is defined we the class is initialized.
        """
        for key in data:
            for value in data[key]:
                str_hours = str(key).replace("-", "/")
                key_db = f"{str(str_hours)}:{str(value)}"
                value_db = data[key][value]
                self.redis.setex(name=key_db, time=self.time_expire, value=value_db)

    def set_energy(self, data: dict) -> None:
        """
        takes the renewable energy predictions (thermal excluded)and store them into the db.
         the prediction that are already present will be replaced by the latest, this data also
        have an expiration time that is defined we the class is initialized.
        """
        for hour in data:
            for energy in data[hour]:
                key_db = f"{hour}:{energy}"
                value_db = data[hour][energy]
                self.redis.setex(name=key_db, time=self.time_expire, value=value_db)

    def set_src(self, data: NumpyArray, hours: NumpyArray, src: str) -> None:
        """
        takes the thermal predictions and store them into the db. the prediction
        that are already present will be replaced by the latest, this data also
        have an expiration time that is defined we the class is initialized.
        """
        if len(data) != len(hours): print(f"Len differ between data and timestamp, {len(data)},{len(hours)}")
        else:
            for iel in range(len(data)):
                key_db = f"{hours[iel]}:{src}"
                value_db = data[iel]
                self.redis.setex(name=key_db, time=self.time_expire, value=value_db)

    def get_loads(self, dates: NumpyArray) -> dict:
        """
        Retrive the load in the dates that are passed from the Redis db.
        """
        res = dict(generation={})
        for date in dates:
            value = self.redis.get(f"{date}:load")
            if value: res['generation'][date] = float(value)
            else: return res
        return res

    def get_data(self, day: str = 'today') -> dict:
        """
        takes the all the predictions that will be displayed in the application.
        We decided that all the predictions must be alligned for the next 48 hours
        so we used temporary flag to stop the procedure when we miss the prediction
        of particular source.
        """
        if day == 'today':  day = dt.datetime.today().strftime("%Y-%m-%d")
        elif day == 'tomorrow': day = (dt.datetime.today()+dt.timedelta(days=1)).strftime("%Y-%m-%d")
        day_long = pd.date_range(day, periods=24, freq='H').tolist()
        day_long.reverse()
        hours_today = [i.strftime("%Y/%m/%d %H:%M:%S") for i in day_long]
        load, thermal, wind, hydro, photovoltaic, geothermal, biomass, dates = [], [], [], [], [], [], [], []
        for hours in hours_today:
            flag_1 = self.redis.exists(f"{hours}:thermal")
            flag_2 = self.redis.exists(f"{hours}:load")
            flag_3 = self.redis.exists(f"{hours}:wind")
            if flag_1 and flag_2 and flag_3:
                load.append(float(self.redis.get(f"{hours}:load")))
                thermal.append(float(self.redis.get(f"{hours}:thermal")))
                wind.append(float(self.redis.get(f"{hours}:wind")))
                hydro.append(float(self.redis.get(f"{hours}:hydro")))
                photovoltaic.append(float(self.redis.get(f"{hours}:photovoltaic")))
                geothermal.append(float(self.redis.get(f"{hours}:geothermal")))
                biomass.append(float(self.redis.get(f"{hours}:biomass")))
                dates.append(hours)
            else: break
        load.reverse(), thermal.reverse(), wind.reverse(), hydro.reverse(), photovoltaic.reverse()
        geothermal.reverse(), biomass.reverse(), dates.reverse()
        return(dict(load=load, thermal=thermal, wind=wind, hydro=hydro, photovoltaic=photovoltaic,
                     geothermal=geothermal, biomass=biomass, dates=dates))

class MySqlDB:
    """
    Class created to handle the files with MySQL database.
    """
    def __init__(self):
        mysql_host = os.environ.get('MYSQL_HOST')
        mysql_user = os.environ.get('MYSQL_USER')
        mysql_psw = os.environ.get('MYSQL_PASSWORD')
        self.engine = sqlalchemy.create_engine(f"mysql+pymysql://{mysql_user}:{mysql_psw}@{mysql_host}/energy")
        self.engine.connect()

    def save_meteo(self, meteos: PandasDataFrame, forecast: bool = False) -> None:
        """
        takes the new meteo observation that are used to create the historic
         already processed and update the db.
        """
        if forecast: meteos.to_sql("forecast_meteo", con=self.engine, if_exists='append', index=False)
        else: meteos.to_sql("energy_meteo", con=self.engine, if_exists='append', index=False)

    def prediction_to_sql(self, predictions: dict) -> None:
        """
        Takes the energy predictions that arrive from the  Mqtt broker,
        process it and upload them into the db.
        """
        predictions = predictions
        df = pd.DataFrame.from_dict(predictions, orient='index')
        df.reset_index(inplace=True, drop=False)
        df.rename(columns={'index': 'date'}, inplace=True)
        res = []
        for source in df.columns:
            if str(source) != 'date' and str(source) != 'index':
                tmp = df[['date', source]].copy()
                tmp['energy'] = source
                tmp.rename(columns={source: 'generation'}, inplace=True)
                res.append(tmp)
        (pd.concat(res)).to_sql("prediction_energy",  con=self.engine, if_exists='append', index=False)

    def query_from_sql_to_pandas(self, query: str, dates: str = False) -> PandasDataFrame:
        """
        Fancy function that given a query it return the result as
        a Pandas DataFrame, if the query return none the data frame
        will be empty.
        """
        if dates: return pd.read_sql_query(query, self.engine, parse_dates=[dates])
        else: return pd.read_sql_query(query, self.engine)

    def preprocess_thermal_prediction_to_sql(self, pred: NumpyArray, dates: NumpyArray) -> None:
        """
         Takes the thermal predictions that arrive from the  Mqtt broker,
         process it and upload them into the db.
         """
        df = pd.DataFrame(pred, dates)
        df["date"] = df.index
        df["energy"] = "thermal"
        df.rename(columns={0: 'generation'}, inplace=True)
        df.to_sql("prediction_energy",  con=self.engine, if_exists='append', index=False)

class MySqlModels(MySqlDB):
    """
    Child class of MySqlDB, it is used to retrive the data that must be passed
    as training data to fit the models.
    """
    def __init__(self):
        super().__init__()

    def get_training_data(self, source: str, aug: str = 'yes') -> Tuple[PandasDataFrame, PandasSeries]:
        """
        Retrive the data that are used for the HydroModel, PhotovoltaicModel, BiomassModel,
        GeoThermalModel and WindModel and return them as already processed dataframe.
        We also allow to slightly augment the data that are returned, this is because we transform
        the month as a categorical variable and if we try to predict a month that the model never seen
        it will complain telling that it never saw that particular categorical variable.
        """
        query = f"""SELECT energy_meteo.clouds, pressure, humidity, temp, rain_1h, snow_1h, wind_deg, wind_speed, energy_generation.generation,
                    CASE EXTRACT(HOUR FROM energy_meteo.date)
                        WHEN '1' THEN  '01 AM'	WHEN '2' THEN  '02 AM' WHEN '3' THEN  '03 AM' WHEN '4' THEN  '04 AM'
                        WHEN '5' THEN  '05 AM' WHEN '6' THEN  '06 AM' WHEN '7' THEN  '07 AM' WHEN '8' THEN  '08 AM'
                        WHEN '9' THEN  '09 AM' WHEN '10' THEN  '10 AM' WHEN '11' THEN  '11 AM'	WHEN '12' THEN  '00 AM'
                        WHEN '13' THEN  '13 PM'	WHEN '14' THEN  '14 PM'	WHEN '15' THEN  '15 PM'	WHEN '16' THEN  '16 PM'
                        WHEN '17' THEN  '17 PM'	WHEN '18' THEN  '18 PM'	WHEN '19' THEN  '19 PM'	WHEN '20' THEN  '20 PM'
                        WHEN '21' THEN  '21 PM'	WHEN '22' THEN  '22 PM'	WHEN '23' THEN  '23 PM'	WHEN '0' THEN  '12 PM'
                    END as str_hour,
                    CASE EXTRACT(MONTH FROM energy_meteo.date)
                        WHEN '1' THEN 'january' WHEN 2 THEN 'february' WHEN '3' THEN 'march' WHEN '4' THEN 'april'
                        WHEN '5' THEN 'may' WHEN '6' THEN 'june' WHEN '7' THEN 'july' WHEN '8' THEN 'august'
                        WHEN '9' THEN 'september' WHEN '10' THEN 'october' WHEN '11' THEN 'november' WHEN '12' THEN 'december'
                    END as str_month
                    FROM energy_generation
                    INNER JOIN energy_meteo
                    ON energy_meteo.date = energy_generation.date
                    where energy_generation.energy_source = '{source}';"""

        df = self.query_from_sql_to_pandas(query=query)
        if aug:
            actual_month = dt.datetime.now().strftime("%B").lower()
            monthinteger = (dt.datetime.now().month) + 1
            month = dt.date(1, monthinteger, 1).strftime('%B').lower()
            month_plus_one = df[df['str_month'] == 'june' ].copy()
            month_plus_one['str_month'] = month_plus_one.str_month.apply(lambda x: month)
            df = df.append(month_plus_one, ignore_index=True)
            monthinteger = (dt.datetime.now().month)
            month_plus_one = df[df['str_month'] == 'june' ].copy()
            month_plus_one['str_month'] = month_plus_one.str_month.apply(lambda x: 'july')
            df = df.append(month_plus_one, ignore_index=True)
        predictors = df.drop('generation', axis=1)
        target = df.loc[:, ['generation']]
        return predictors, target

    def get_training_hydro_or_thermal_data(self, src: str) -> Tuple[PandasDataFrame, PandasSeries]:
        """
        Retrive the data that are used for the ThermalModel and return them as already processed dataframe.
        """
        query_rest = """SELECT date, SUM(generation) AS Sum_of_rest_GW FROM energy_generation
                        where energy_source != 'thermal' and energy_source != 'hydro'  GROUP BY date;"""
        query_thermal = f""" SELECT holiday, total_load, generation, energy_load.`date`,
                            CASE EXTRACT(MONTH FROM energy_load.`date`)
                                WHEN '1' THEN 'january' WHEN 2 THEN 'february' WHEN '3' THEN 'march' WHEN '4' THEN 'april'
                                WHEN '5' THEN 'may' WHEN '6' THEN 'june' WHEN '7' THEN 'july' WHEN '8' THEN 'august'
                                WHEN '9' THEN 'september' WHEN '10' THEN 'october' WHEN '11' THEN 'november' WHEN '12' THEN 'december'
                            END as str_month
                            FROM energy_load
                            INNER JOIN energy_generation
                            ON energy_load.date = energy_generation.date  where energy_source = '{src}';"""

        df_rest = self.query_from_sql_to_pandas(query=query_rest)
        df_thermal = self.query_from_sql_to_pandas(query=query_thermal)
        final = pd.merge(df_rest, df_thermal, on='date')
        predictors = final[["holiday", "total_load", "Sum_of_rest_GW", "str_month"]]
        target = final.loc[:, ['generation']]
        return predictors, target


    def get_training_load_data(self, whole: str = None) -> Tuple[PandasDataFrame, PandasSeries]:
        """
        Retrive the data that are used for the LoadModel and return them as already processed dataframe.
        """
        query = f"""SELECT total_load, holiday,date,
                    CASE EXTRACT(MONTH FROM date)
                        WHEN '1' THEN 'january' WHEN 2 THEN 'february' WHEN '3' THEN 'march' WHEN '4' THEN 'april'
                        WHEN '5' THEN 'may' WHEN '6' THEN 'june' WHEN '7' THEN 'july' WHEN '8' THEN 'august'
                        WHEN '9' THEN 'september' WHEN '10' THEN 'october' WHEN '11' THEN 'november' WHEN '12' THEN 'december'
                    END as str_month,
                    CASE EXTRACT(HOUR FROM date)
                        WHEN '1' THEN  '1'	WHEN '2' THEN  '2'	WHEN '3' THEN  '3'	WHEN '4' THEN  '4'
                        WHEN '5' THEN  '5'	WHEN '6' THEN  '6'	WHEN '7' THEN  '7'	WHEN '8' THEN  '8'
                        WHEN '9' THEN  '9'	WHEN '10' THEN  '10'	WHEN '11' THEN  '11'	WHEN '12' THEN  '12'
                        WHEN '13' THEN  '13'	WHEN '14' THEN  '14'	WHEN '15' THEN  '15'	WHEN '16' THEN  '16'
                        WHEN '17' THEN  '17'	WHEN '18' THEN  '18'	WHEN '19' THEN  '19'	WHEN '20' THEN  '20'
                        WHEN '21' THEN  '21'	WHEN '22' THEN  '22'	WHEN '23' THEN  '23'	WHEN '0' THEN  '0'
                    END as str_hour
                    from energy.energy_load"""
        df = self.query_from_sql_to_pandas(query)
        if whole: return df
        else:
            predictors = df[["holiday", "str_hour", "str_month"]]
            target = df.loc[:, ['total_load']]
            return predictors, target


class MySqlTransfer(MySqlDB):
    """
    Child class of MySqlDB, it is used to build the transfer service that allow
    to replicate rapidly the tables that we used and  transfer part of the data
    that we collect to a new dataset.
    """
    def __init__(self, path_folder: str = 'Documentation/Files_from_terna'):
        super().__init__()
        self.path_folder = path_folder
        self.path_extra = '/src/Volumes/extra_files'

    def create_tables(self) -> None:
        """
        Function that create the tables as we did.
        """
        print('Creating Tables for the new DB')
        s = " ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"
        queries = [
            f"""CREATE TABLE `energy_meteo` (`idenergy_meteo` int NOT NULL AUTO_INCREMENT,`date` datetime NOT NULL,
                `clouds` float NOT NULL,`pressure` float NOT NULL,`humidity` float NOT NULL,`rain_1h` float NOT NULL,
                `snow_1h` float NOT NULL,`wind_deg` float NOT NULL, `temp` float NOT NULL, `wind_speed` float NOT NULL,
                PRIMARY KEY (`idenergy_meteo`), UNIQUE KEY `idenergy_meteo_UNIQUE` (`idenergy_meteo`)) {s}""",

            f"""CREATE TABLE `energy_generation` (`idenergy_generation` int NOT NULL AUTO_INCREMENT,`date` datetime NOT NULL,
                `energy_source` varchar(45) NOT NULL, `generation` float NOT NULL,PRIMARY KEY (`idenergy_generation`)){s}""",

            f"""CREATE TABLE `energy_load` (`idenergy_load` int NOT NULL AUTO_INCREMENT, `date` datetime NOT NULL,
                `holiday` varchar(45) NOT NULL, `total_load` float NOT NULL, PRIMARY KEY (`idenergy_load`)) {s}""",

            f"""CREATE TABLE `prediction_energy` (`idprediction_energy` int NOT NULL AUTO_INCREMENT,  `date` datetime NOT NULL,
                `energy` varchar(45) NOT NULL,  `generation` float DEFAULT NULL,  PRIMARY KEY (`idprediction_energy`)){s}""",

            f"""CREATE TABLE `forecast_meteo` (`idforecast_meteo` int NOT NULL AUTO_INCREMENT,`date` datetime NOT NULL,
                `clouds` float NOT NULL,`pressure` float NOT NULL,`humidity` float NOT NULL,`rain_1h` float NOT NULL,
                `snow_1h` float NOT NULL,`wind_deg` float NOT NULL, `temp` float NOT NULL, `wind_speed` float NOT NULL,
                PRIMARY KEY (`idforecast_meteo`), UNIQUE KEY `idforecast_meteo_UNIQUE` (`idforecast_meteo`)) {s}"""]

        for query in queries:
            try: self.engine.execute(query)
            except Exception as e:
                index = str(e).find("[")
                if index != -1: print(f" {query.split(' ')[2]} Failed because of {str(e)[:index].strip()}")
                else: print(f" {query.split(' ')[2]} Failed because of {e}")

    def generation_from_terna(self, external_path: List[str] = None, extra_files: bool = False) -> None:
        """
        Takes the files inside Documentation, process them and upload the data into
        the db. we also allow to pass an external file that can be added to the list.
        """
        paths, where = f"{self.path_folder}/generation/", False
        print(f"Updating Generation to the new DB")
        #paths = [paths + i for i in os.listdir(paths)]
        if external_path:
            paths = external_path
            where = True
        if extra_files:
            extra_energy = f"{self.path_extra}/energy/"
            paths = [extra_energy + i for i in os.listdir(extra_energy)]
        out = []
        for path in paths:
            if not where and not os.path.exists(path):  print(f"{path} is not a valid path!")
            elif where and not requests.get(path).ok: print(f"{path} is not a valid url {requests.get(path).status_code}")
            else:
                df = None
                try: df = pd.read_csv(path)
                except Exception: pass
                try: df = pd.read_excel(path, skiprows=[0], header=1)
                except Exception: pass
                if isinstance(df, PandasDataFrame):
                    df.rename(columns={'Energy Balance [GWh]': 'Renewable Generation [GWh]'}, inplace=True)
                    out.append(df)
        if out:
            final = pd.concat(out)
            if not final.empty:
                final.Date = pd.to_datetime(final.Date)
                final.sort_values(by=['Date'], inplace=True)
                final.reset_index(inplace=True, drop=True)
                final.rename(columns={'Date': "date", 'Energy Source': 'energy_source',
                                      'Renewable Generation [GWh]': 'generation'}, inplace=True)
                final.to_sql('energy_generation', con=self.engine, if_exists='append', index=False)
                # faster creating one big df and pass to mysql rather than pass each df to mysql.
                # since there are few data we can hadle that.
                print(f"Finished updating Generation")
            else: print('empty files')
        else: print('We are able to hadle none of your files')

    def load_from_terna(self, external_path: List[str] = None, extra_files: bool = False) -> None:
        """
        Takes the files inside Documentation, process them and upload the data into
        the db. we also allow to pass an external file that can be added to the list.
        """
        paths, where = f"{self.path_folder}/load/", False
        print(f"Updating Load to the new DB")
        paths_to_file = [paths+i for i in os.listdir(paths)]
        if external_path:
            paths_to_file = external_path
            where = True
        if extra_files:
            extra_load = f"{self.path_extra}/load/"
            paths_to_file = [extra_load + i for i in os.listdir(extra_load)]
        holiday = HolidayDetector().create_backward_calendar()
        for path in paths_to_file:
            if not where and not os.path.exists(path):  print(f"{path} is not a valid path!")
            elif where and not requests.get(path).ok: print(f"{path} is not a valid url {requests.get(path).status_code}")
            else:
                current = None
                try: current = pd.read_excel(path, skiprows=[1], header=[1])
                except Exception: pass
                try: current = pd.read_csv(path)
                except Exception: pass
                if isinstance(current, PandasDataFrame):
                    current = current[current["Bidding zone"] == "Italy"]
                    current.drop(columns=["Forecast Total load [MW]", "Bidding zone"], inplace=True)
                    try: current["Date"] = pd.to_datetime(current["Date"], format="%d/%m/%Y %H:%M:%S %p")
                    except Exception: pass
                    try: current["Date"] = pd.to_datetime(current["Date"], format="%Y/%m/%d %H:%M:%S")
                    except Exception: pass
                    current = current.loc[current['Date'].dt.strftime("%M") == '00', :]
                    current["cross_date"] = current["Date"].dt.strftime("%Y-%m-%d")
                    current["Date"] = current["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
                    current = current.merge(holiday, how="inner", on="cross_date")
                    current.drop(columns=["cross_date"], inplace=True)
                    current.rename(columns={'Total Load [MW]': "total_load", 'Date': 'date', 'Holiday': 'holiday'}, inplace=True)
                    current["total_load"] = current["total_load"]/1000
                    current.to_sql('energy_load', con=self.engine, if_exists='append', index=False)
                else: print(f'Unable to process {path}')
        print(f"Finished updating Load")

    def from_json_to_db(self) -> None:
        """
        Takes the storico in json format that we prepared, it process
        those data and add it into the new db.
        """
        path = f"{self.path_folder}/storico_meteo_r.json"
        print(f"Updating MeteoData to the new DB")
        meteos,res = JsonManagerCurrentMeteo(path).load_unprocess(),[]
        for city in meteos: res.append(city.from_class_to_dict())
        res = shrink_mean(res)
        res.to_sql("energy_meteo", con=self.engine, if_exists='append', index=False)
        print(f"Finished updating MeteoData: {len(res)}")



class JsonManagerCurrentMeteo:
    """
    Manager created to deal the JSON operation as save and load for
    current meteo data. Used for the first collection of the storico.
    """
    def __init__(self, path: str = None):
        self.path = path

    def load_unprocess(self) -> List[MeteoData]:
        """
        Load from the json when none of the data have been pre-processed.
        """
        if os.path.exists(self.path):
            with open(self.path, "r") as file: storico = json.load(file)
            return [MeteoData.current_from_original_dict_to_class(obj) for obj in storico]
        else: print(f"Do not find the right path!")

    def load(self) -> List[MeteoData]:
        """
        Load from the json when the data have been pre-processed.
        """
        if os.path.exists(self.path):
            with open(self.path, "r") as file:  storico = json.load(file)
            return [MeteoData.current_from_preprocess_dict_to_class(obj) for obj in storico]
        else: print(f"Do not find the right path!")

    def first_update(self, current_meteo: List[MeteoData]) -> None:
        """
        Create the json file and update it for the first time!
        """
        print("File not found, created 'storico_meteo.json' and first update")
        obs = [MeteoData.from_class_to_dict(obj) for obj in current_meteo]
        with open("storico_meteo.json", "w") as file:
            json.dump(obs, file, indent=4)
            self.path = "storico_meteo.json"

    def update(self, current_meteo: List[MeteoData]) -> None:
        """
        Update the Storico.json.
        """
        if os.path.exists(self.path):
            storico = self.load()
            update = storico + current_meteo
            with open(self.path, "w") as file: json.dump([MeteoData.from_class_to_dict(obj) for obj in update], file, indent=4)
        else:  self.first_update(current_meteo)


class HolidayDetector:
    """
    Class created to deal the italian holiday since they are very important
    for predicting the thermal and the load on the net.
    """
    def __init__(self):
        self.it_holiday = {"01-01", "06-01", "25-04", "01-05", "02-06",
                           "15-08", "01-10", "08-12", "25-12", "26-12"}

    def easter_day(self, year: int) -> str:
        """
        Given a year it return the day of the Easter.
        """
        special_years = ['1954', '1981', '2049', '2076']
        specyr_sub = 7
        a, b, c = year % 19, year % 4, year % 7
        d = (19 * a + 24) % 30
        e = ((2 * b) + (4 * c) + (6 * d) + 5) % 7
        if year in special_years: dateofeaster = (22 + d + e) - specyr_sub
        else: dateofeaster = 22 + d + e
        if dateofeaster > 31:
            if (dateofeaster - 31) >= 10: return "{}-04".format(dateofeaster - 31)
            else:
                dateofeaster = "0" + str(dateofeaster - 31)
                return "{}-04".format(dateofeaster)
        else: return "{}-03".format(dateofeaster)

    def easter_plus_one(self, day: str) -> str:
        """
        Given the day of Easter which is on sunday it return
        the Easter Monday.
        """
        if day.startswith("31"): return "01-04"
        else:
            _day = (int(day.split("-")[0]) + 1)
            _month = day.split("-")[1]
            if _day < 10: _day = f"0{_day}"
            return f"{str(_day)}-{_month}"

    def create_backward_calendar(self) -> PandasDataFrame:
        """
        Create a calendar of the past 5 years spotting all the holidays,
        saturdays and sundays.
        """
        def check_day(day):
            if day == 'Saturday': return 'saturday'
            elif day == 'Sunday': return 'sunday'
            else: return 'no'
        df = pd.DataFrame()
        tmp = pd.date_range('2015-01-01', '2025-01-01', freq='D').to_series()
        df["day"] = tmp.dt.day_name()
        df["Month"] = tmp.dt.month_name()
        df.reset_index(inplace=True)
        df['holiday'] = df.day.apply(check_day)
        tmp_easter = []
        for year in range(2015, 2025):
            date = self.easter_day(year)
            date = self.easter_plus_one(date)
            tmp_easter.append((str(year) + "-" + date))
        for pasqua in tmp_easter:  df.loc[df["index"] == pasqua, "holiday"] = 'holiday'
        tmp = []
        for row in df["index"].dt.strftime('%d-%m'):
            if row in self.it_holiday: tmp.append("Yes")
            else: tmp.append("No")
        tmp = pd.Series(tmp)
        df.loc[tmp ==' Yes', "holiday"] = 'holiday'
        df.columns = ["cross_date", "DayName", "Month", "Holiday"]
        df.drop(columns=["DayName", "Month"], inplace=True)
        df.cross_date = df['cross_date'].dt.strftime("%Y-%m-%d")
        return df

    def check_holiday_day(self, day_string_format: str) -> str:
        """
        Check if the day is a saturday, a sunday or an holiday.
        """
        year, day = dt.datetime.now().year, day_string_format
        easter_day = self.easter_day(year)
        easter_day_plus_one = self.easter_plus_one(easter_day)
        easter_day = f"{year}-{easter_day}"
        easter_day_plus_one = f"{year}-{easter_day_plus_one}"
        try: day = datetime.datetime.strptime(day_string_format, "%Y/%m/%d %H:%M:%S")
        except Exception: pass
        try: day = datetime.datetime.strptime(day_string_format, "%Y/%m/%d")
        except Exception: pass
        holiday_today = 'no'
        if day.strftime('%A') == "Sunday": holiday_today = "sunday"
        if day.strftime('%A') == "Saturday": holiday_today = "saturday"
        if day.strftime('%Y-%d-%m') == easter_day or day.strftime('%Y-%d-%m') == easter_day_plus_one: holiday_today = "holiday"
        if day.strftime('%d-%m') in self.it_holiday: holiday_today = "holiday"
        return holiday_today

    def prepare_load_to_predict(self, days: int = 3) -> Tuple[PandasDataFrame, PandasSeries]:
        """
        Since the load is enterely based on the holiday, the month and the hour we can built
        those data, this function do that.
        """
        now = dt.datetime.now().strftime("%H")
        today = dt.datetime.now().strftime("%Y/%m/%d")
        month = dt.datetime.now().strftime("%B").lower()
        preds, i = [], 0
        for iel in range(23, int(now) - 1, -1):
            preds.append([self.check_holiday_day(today), f"{today} {iel if iel > 9 else '0' + str(iel)}:00:00", str(iel), month])
        today = (dt.datetime.now() + dt.timedelta(days=1))
        today_s = today.strftime('%Y/%m/%d')
        month = dt.datetime.now().strftime("%B").lower()
        while len(preds) < (days * 24):
            preds.append([self.check_holiday_day(today_s), f"{today_s} {i if i > 9 else '0' + str(i)}:00:00", str(i), month])
            i += 1
            if i == 24:
                month = dt.datetime.now().strftime("%B").lower()
                today_s = (today + dt.timedelta(days=1)).strftime("%Y/%m/%d")
                today = today + dt.timedelta(days=1)
                i = 0
        df = pd.DataFrame(preds)
        df.rename(columns={0: "holiday", 1: "date", 2: "str_hour", 3: "str_month"}, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by='date', inplace=True)
        return df, df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")


def shrink_mean(data: List[dict]) -> PandasDataFrame:
    """
    It takes the 20 dictionary of preprocess MeteoData and it shrink it
    to the mean, so to have one value representing the italian weather.
    """
    df = pd.DataFrame(data)
    res = df.groupby('cross_join').mean().reset_index()
    res["cross_join"] = pd.to_datetime(res["cross_join"], format='%d/%m/%Y %H:%M %p')
    res.sort_values(by='cross_join', inplace=True)
    res["cross_join"] = res["cross_join"].dt.strftime('%Y/%m/%d %H:%M:%S')
    res.rename(columns={'cross_join': 'date'}, inplace=True)
    return res

def populate(dbs: MySqlTransfer) -> None:
    dbs.load_from_terna()
    dbs.generation_from_terna()
    dbs.from_json_to_db()

def add_internal_file(dbs: MySqlTransfer, extra_load: bool = False, extra_energy: bool = False) -> None:
    if extra_load: dbs.load_from_terna(extra_files=extra_load)
    if extra_energy: dbs.generation_from_terna(extra_files=extra_energy)

def add_external_files(dbs: MySqlTransfer, external_load: str = False, external_energy: str = False) -> None:
    if external_load: dbs.load_from_terna(external_path=external_load.split(","))
    if external_energy: dbs.generation_from_terna(external_path=external_energy.split(","))

def collecting_storico(rate: int = 12, broker: str = 'localhost', retain: bool = False) -> None:
    hours_to_sleep = (60*60) * rate
    while True:
        now = datetime.datetime.now()
        print(f'Uploading MySQL database at {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        day = dt.datetime.now().strftime("%d/%m/%Y")
        hour = dt.time(dt.datetime.now().hour).strftime("%H:%S %p")
        modified_cross_join = day + " " + hour
        meteos = collector.GetMeteoData().fetching_current_meteo_json()
        meteos = [MeteoData.current_from_original_dict_to_class(meteo) for meteo in meteos]
        for obs in meteos: obs.cross_join = modified_cross_join
        meteos = shrink_mean([i.from_class_to_dict() for i in meteos])
        broker_mqtt = c_mqtt.MqttGeneralClass(broker=broker, retain=retain, client_name='StoricoSender')
        broker_mqtt.custom_publish(data=meteos.to_dict(), topic="Energy/Storico/")
        time.sleep(hours_to_sleep)

def main():
    arg_parser = argparse.ArgumentParser(description="Data Collector Meteo")
    arg_parser.add_argument('-c', '--create_tables', action='store_true')
    arg_parser.add_argument('-p', '--partially_populate', action='store_true')
    arg_parser.add_argument('-il', '--internal_load_files', action='store_true')
    arg_parser.add_argument('-ie', '--internal_energy_files', action='store_true')
    arg_parser.add_argument('-re', '--retain', action='store_true')
    arg_parser.add_argument('-s', '--storico', action='store_true')
    arg_parser.add_argument('-r', '--rate', default=12, type=int, help="Rate expressed in hours")
    arg_parser.add_argument('-b', '--broker', default='localhost', choices=['localhost', 'aws'])
    arg_parser.add_argument('-el', '--external_load_path', type=str, help="External path to load")
    arg_parser.add_argument('-eg', '--external_generation_path', type=str, help="External path to generation")
    args = arg_parser.parse_args()

    if args.storico:
        collecting_storico(rate=args.rate, broker=args.broker, retain=args.retain)
    else:
        transfer = MySqlTransfer()
        if args.create_tables: transfer.create_tables()
        if args.partially_populate: populate(transfer)
        if args.internal_load_files: add_internal_file(transfer, extra_load=True)
        if args.internal_energy_files: add_internal_file(transfer, extra_energy=True)
        if args.external_load_path: add_external_files(transfer, external_load=args.external_load_path)
        if args.external_generation_path: add_external_files(transfer, external_energy=args.external_generation_path)
        print('Done!')


if __name__ == "__main__":
    main()
