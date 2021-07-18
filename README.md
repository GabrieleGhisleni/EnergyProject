# Energy Project - Big Data Technologies

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)
[![JavaScript Style Guide: Good Parts](https://img.shields.io/badge/code%20style-goodparts-brightgreen.svg?style=flat)](https://github.com/dwyl/goodparts "JavaScript The Good Parts")

[Create Issue -](https://github.com/GabrieleGhisleni/EnergyProject/issues/new)
[Fork](https://github.com/GabrieleGhisleni/EnergyProject/fork)

The goal of this project is to predict the quantity of energy (from renewable sources) that can be produced in an hour and in a day in 
Italy. The code is available in this [Git repository], where you can also find the [Docker Image]. 

We stress the fact
that the application is meant to be run by using the mentioned 
Docker image, and the following file focuses on explaining how.

### Table of Contents

| Argument | Description |
| --------------|---------------|
| [How to run the application](#how-to-run-the-application) | Description of how to run the application using our DBs and brokers.|
| [Change the services](#change-the-services) | Guide for switching from our DBs and brokers to yours.|  
| [Arguments available](#arguments-available) | Brief description of the arguments that can be passed to the docker-compose.yml|

### Index

 1. [How to run the application](#how-to-run-the-application)  
    1.1 [Directory structure](#directory-structure)   
    1.2 [Docker-compose.yml](#docker-compose.yml)  
    1.3 [Environmental variables](#environmental-variables)   
    1.4 [First deployment](#first-run)
2. [Change services](#change-the-services)  
   2.1 [Change MySql Database](#change-mysql-database)      
       2.1.1 [Transfer service](#transfer-service)   
   2.2 [Pass files from Terna to MySql](#upload-new-data-from-terna-download-center)    
   2.3 [Change Mqtt Broker](#change-mqtt-broker)  
   2.4 [Train models service](#train-models)  
   2.5 [OpenWeather key](#openWeather-secret-api-keys)  
3. [Parameters available](#parameters-available)     
    3.1 [Services based on mqtt_managers.py](#services-based-on-mqtt_managers.py)  
    3.2 [Services based on models_manager.py](#services-based-on-models_manager.py)  
    3.3 [Services based on meteo_managers.py](#services-based-on-meteo_managers.py)     
        3.3.1 [External files from Terna](#pass-external-file-from-terna)    
    3.4 [Services based on meteo_collector.py](#services-based-on-meteo_collector.py)   
 

<br/><br/>

In the first paragraph we will show how to run the application for the very first time using our DBs and our 
mosquitto broker, in the second one we will illustrate the arguments that can be passed to the scripts. Lastly, we 
will explain how to detach our services and replace them with yours (in particular your mysql DB). 

## How to run the application

> First, we will show how to run the application using the services we defined, such as our Amazon RDS MySql database 
 and our AWS IoT-Core broker, which are both hosted on Amazon AWS. 
**Then we will explain how to change those services and replace them with yours.**

It is required a basic understanding of how to use [docker]. 
In any case, the first step would be pulling the [Docker Image] attached to this github page. To do so, run the following command:

```sh
docker pull docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
```

### Directory structure
We suggest creating a fresh directory where the following structure should be replicated:

```
## Directory's tree
FreshFolder
|-- docker-compose.yml
|-- extra-services.yml
|-- energy.env
|-- Volumes
|   |-- django
|   |-- mysql
|   |-- redis 
|   |-- extra_files
|   |   |-- load
|   |   |-- energy
|   |-- mosquitto
|   |   |-- config
|   |   |      |-- mosquitto.conf
```

The following command in Windows replicates that directories structure.
>`mkdir energy\Volumes\django && mkdir energy\Volumes\mysql 
 && mkdir energy\Volumes\redis && mkdir energy\Volumes\mosquitto\config &&  
 mkdir energy\Volumes\extra_files\load && mkdir energy\Volumes\extra_files\energy`

This command creates the empty files (in Windows):

> `cd energy && echo > docker-compose.yml && echo > extra-services.yml && echo > energy.env && echo > Volumes\mosquitto\config\mosquitto.conf
 `

If you are using a different operating system that does not support this command follow 
these steps:

 1. Create an empty folder.
 2. Create, inside this folder, a docker-compose.yml, a extra-services.yml and an energy.env file.
 3. Create a sub-directory called "Volumes" with four more sub-directories: 
    "mosquitto", "mysql", "django", "redis",  and let those empty.
 4. Create a sub-directory inside 'Volumes' called 'extra_files' with two empty folder inside
    'energy' and 'load'
 5. Create a file called mosquitto.conf in the mosquitto/config folder. Then paste the following lines inside this mosquitto.conf file (you can also find the 
    [mosquitto.conf] here):
    
```sh
## mosquitto.conf
allow_anonymous true
listener 1883
persistence true
persistence_location /mosquitto/data/
retain_available true
```


#### Docker-compose.yml
To run the code with our services it is necessary to now create the [docker-compose.yml] (direct link
to the file) as follows:

```sh
## docker-compose.yml
version: '3.9'
services:
  redis:
    image: redis:latest
    container_name: redis
    ports:
    - '6379:6379'
    volumes:
    - ./Volumes/redis:/data
    logging:
        driver: none
  mqtt:
    image: eclipse-mosquitto
    container_name: mqtt
    volumes:
    - ./Volumes/mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf
    ports:
    - "1883:1883"
    logging:
        driver: none
  mysql:
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    env_file:
      - energy.env
    ports:
    - 3307:3306
    logging:
        driver: none
  # Web App
  web_app:
    image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
    tty: false
    command: bash -c "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
    container_name: energyDjango
    env_file:
      - energy.env
    depends_on:
      - redis
      - mysql
    ports:
    - "8000:8000"
    volumes:
    - ./Volumes/django:/src/Volumes/django


  # Services based on mqtt_managers
  load_receiver:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: load_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic load"
      depends_on:
        - redis
        - mqtt
        - mysql
      env_file:
        - energy.env

  forecast_meteo_receiver:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name:  forecast_meteo_receiver
      command: bash -c "python -u Code/mqtt_manager.py --broker aws --topic forecast"
      depends_on:
        - redis
        - mqtt
        - mysql
      env_file:
        - energy.env

  energy_receiver:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: energy_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic energy"
      depends_on:
        - redis
        - mqtt
        - mysql
        - forecast_meteo_receiver
      env_file:
        - energy.env

  thermal_receiver:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: thermal_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic hydro_thermal"
      depends_on:
        - redis
        - mqtt
        - mysql
        - energy_receiver
      env_file:
        - energy.env

  storico_receiver:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: storico_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic storico"
      env_file:
        - energy.env
      depends_on:
        - redis
        - mqtt
        - mysql

  # meteo_collect based
  forecast_meteo_sender:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: forecast_meteo_sender
      command:  bash -c "sleep 5 && python Code/meteo_collector.py --broker aws"
      depends_on:
        - forecast_meteo_receiver
        - mqtt
      env_file:
        - energy.env

  # models_manager based
  load_sender:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: load_sender
      command:  bash -c "sleep 5 && python Code/models_manager.py --broker aws --sendload"
      depends_on:
        - load_receiver
        - mqtt
      env_file:
        - energy.env

  # meteo_managers based
  storico_sender:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: storico_sender
      command: bash -c "sleep 5 && python Code/meteo_managers.py --broker aws --storico"
      depends_on:
        - storico_receiver
        - mqtt
      env_file:
        - energy.env
```

We set the logs of mysql, mqtt, redis and django to none so to avoid display those messages and be able to follow
the messages from the scripts. Anyway if you want to see those just remove `logging: driver: none` in the [docker-compose.yml].

#### Environmental variables

The last step to make is creating the energy.env file containing all passwords and environmental variables that are 
passed to the code.  

As mentioned, it is always possible to change passwords and variables according to your services (e.g. to use your own databases).
Later on it can be found the exact procedure to follow to achieve that.

```sh
## energy.conf

# mysql_service
MYSQL_HOST="energy.c9vvjb7yh2ou.us-east-1.rds.amazonaws.com"
MYSQL_USER=admin
MYSQL_PASSWORD=Energy14202122
MYSQL_DATABASE=energy
MYSQL_ROOT_PASSWORD=Energy14202122

# redis_service
REDIS_HOST=redis

# mqtt_service
MQTT_HOST_LOCAL=mqtt
MQTT_HOST=a2lhrrugg0vndd-ats.iot.us-east-1.amazonaws.com
CA_ROOT_CERT_FILE="Code/aws_cert/root-CA.crt"
THING_CERT_FILE="Code/aws_cert/5e3ee0103b-certificate.pem.crt"
THING_PRIVATE_KEY="Code/aws_cert/5e3ee0103b-private.pem.key"

# django and openweathermap
OPEN_WEATHER_APPID = a054032d5e094190a9eba85b70421ff3
SECRET_KEY_ENERGY="django-insecure-3@f4136pszq%m3ljx=1!$8h)$71(496%i=_g-xb2+mhyk6+w!w"
PYTHONPATH=/src/
```

#### First deployment
Now the application can be run for the very first time! Open the CLI of your PC and go to the folder that was just 
created. Once you are there, type the following command:

C:\..\your_fresh_directory> `docker-compose up`

Follow the printing statement and click on the hyperlink displayed at the end!
When the process is done you will see this:

![Image](../master/Display/media/Done.JPG)

Clink on the hyperlink:

> Done! - Check the data on  http://127.0.0.1:8000/today-prediction/

This link will open your browser directly to your localhost where you'd find the application running! 
Various functionalities are available, such as today or tomorrow predictions, the browsable API (the description of how 
to use it is in that same page) and the rest of the application:

![Image](../master/Display/media/ap.png)


## Change the services

###  Change MySql Database

To change the mysql DB you have to modify the mysql service in the [docker-compose.yml] and the energy.env file as follows. 
You would need to insert into the brackets `< >` the data that you want to use as well.  

**Make sure that the folder "mysql" is still empty. If that's not the case, delete all the elements before starting 
this procedure. If any problem comes up while deleting, that might be due to the previous mysql instance container still running. 
If so, stop and remove it, then retry.**

```shell
## docker-compose.yml
# mysql_service
  mysql: # <- same to specify inside .env as MYSQL_HOST
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    environment:
    - MYSQL_USER=<your_new_user>  # same to specify inside .env AS MYSQL_USER
    - MYSQL_PASSWORD=<your_new_psw> # same to specify inside .env AS MYSQL_PASSWORD
    - MYSQL_ROOT_PASSWORD=<your_new_psw>  
    - MYSQL_DATABASE=energy
    ports:
    - 3307:3306
```
Before running the script modify also the energy.env file as follows:

```shell
## energy.env
# mysql_service
MYSQL_HOST=mysql # name of the mysql service
MYSQL_USER=<your_new_user> # parameter specified inside .yml
MYSQL_PASSWORD=<your_new_psw>   # parameter specified inside .yml
MYSQL_DATABASE=energy
```

#### Transfer service
**We also provide a service that can be used to create the correct tables inside your fresh database! Doing so, or at least transferring the tables of the database, 
is mandatory.**   

Specifying the argument `--partially_populate` (in the command of the transfer_service)
a part of the data we collected will be transferred to you (also recommended).

We decided to keep these services in a different file. If you have not done it yet, create a new file called 
[extra-services.yml] and insert the following code (remember to update it with your new names and passwords):

```shell
## extra-services.yml 
version: '3.9'
services:
  mysql: # <- same to specify inside .env as MYSQL_HOST
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    environment:
    - MYSQL_USER=<your_new_user>  # same to specify inside .env AS MYSQL_USER
    - MYSQL_PASSWORD=<your_new_psw> # same to specify inside .env AS MYSQL_PASSWORD
    - MYSQL_ROOT_PASSWORD=<your_new_psw>
    - MYSQL_DATABASE=energy
    ports:
    - 3307:3306

  transfer_service:
    image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
    container_name: transfer_service
    command: bash -c "sleep 45 && python Code/meteo_managers.py --create_tables --partially_populate"
    # we pass sleep 45 because the mysql must be ready so to be reachable from the script
    depends_on:
      - mysql
    env_file:
      - energy.env
```

So you are ready to run the service as:

C:\..\your_fresh_directory> ```docker-compose -f extra-services.yml up transfer_service```

Having done so, you can use all the services with your Dbs.

However, if you do not want to pass new data, remove the argument `--partially_populate` from the command of the transfer_service. 
Run the mysql service alone (the very first time this operation can take around 1 minute to prepare the Volumes) as:

C:\..\your_fresh_directory> ```docker-compose up -d mysql```

Wait 60 seconds. Then, with all Volumes ready, you are able to run: 

C:\..\your_fresh_directory> ```docker-compose up```

### Upload new data from Terna Download Center

Since the data regarding the overall Load as well as the generation from renewable
energies come from [Terna Download Center], we created a service that allow you to update your dbs with new
data coming from there.  (Have a look here
to check which data you can update and how [Pass external file from Terna](#pass-external-file-from-terna))


If you downloaded new data from the [download center] and you want to pass them to the scripts, you can 
do that in two different ways:

#### 1. Internal path:

Download the files and put them inside the folder Volumes/extra_files. In particular, if those data regard
the load put them inside the 'load' folder. Otherwise, inside the 'energy' folder.

Change the [extra-services.yml] adding this service:
   
```shell
## extra-services.yml
  add_internal_files_to_dbs:
    image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
    container_name: add_internal_files_to_dbs
    command: bash -c "python Code/meteo_managers.py --internal_energy_files --internal_load_files"
    volumes:
      - ./Volumes/extra_files/energy:/src/Volumes/extra_files/energy
      - ./Volumes/extra_files/load:/src/Volumes/extra_files/load
    depends_on:
      - mysql
    env_file:
      - energy.env
```

Then run:
C:\..\your_fresh_directory> ```docker-compose -f extra-services.yml up add_internal_files_to_dbs```

#### 2. External path

If you stored those data somewhere else and you want to pass them to the code, use this service specifying the 
url as a comma separated string (e.g. 'https:myfirstfile.csv,https:mysecondfile.csv, ... ')

```shell
## extra-services.yml
  add_external_files_to_dbs:
    image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
    container_name: add_external_files_to_dbs
    command: bash -c "python Code/meteo_managers.py
      --external_load_path  https/direct_link/to_yourload_file.csv, https/secondfile.csv
      --external_generation_path  https/direct_link/you_generation.csv
      "
    depends_on:
      - mysql
    env_file:
      - energy.env
```

Then run:
C:\..\your_fresh_directory> ```docker-compose -f extra-services.yml up add_external_files_to_dbs```

### Change Mqtt Broker

To be able to do this, **you must have configured the [mosquitto.conf]** file as shown before. It can be observed that we already provide the 
service for mosquitto in the docker-compose. To complete this step you should just change the broker parameter from 
`aws` to `localhost` in all the sections `command` of the [docker-compose.yml] as:

```
  command:  bash -c "python Code/meteo_collector.py --broker localhost"
```

**Be sure that all the services refer to the same broker.**

### Train models

To re-train the models you will need to add this service and specify which model to train from `["wind", "hydro", "load", 
"thermal", "geothermal", "biomass", "photovoltaic"]`. We also recommend keeping the `--aug` argument.   
**You must have collected some data before doing that, or having done the transfer service**.

In [extra-services.yml] add the following code specifying which model you want to train, or, in case you want 
to retrain them all, leave it as it is:

```shell
# extra-services.yml
  train_models:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
      container_name: train_models
      command:  bash -c "python Code/models_manager.py --model_to_train all --aug"
      depends_on:
        - mysql
      env_file:
        - energy.env
```

Run this one service with ```docker-compose -f extra-services.yml up train_models```

Then you have to commit the changes to the image as follows:

1. ``` docker ps -a``` search for the container named "train_models" and copy the ID.
2. `docker commit <IDcontainertrain_models> docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest`

Having done this operation, the new models will be available for other services to use.

### OpenWeather Secret API Keys

Go the [OpenWeather] and follow the instruction to get the free API keys.

## Parameters available

> We now make a brief overview of the
arguments that can be passed to the script through the docker-compose.


###  Services based on __*mqtt_managers.py*__
```
 -b, --broker, default='localhost', choices=['localhost', 'aws']
 -t, --topic, required=True, choices=['forecast', 'energy', 'hydro_thermal', 'load', 'storico']
 -r, --retain, action=store_true
 -ex, --expiration_time, default=24, type=int
```

- `retain` messages is available only while working with localhost!
- `expiration_time` refers to the time the predictions will be available on Redis.
- `broker` is the mqtt broker you connect to.
- `topic` refers to the particular topic to subscribe to.

### Services based on __*models_manager.py*__
```
    -l, --sendload, action=store_true, 
    -b, --broker, default='localhost', choices=['localhost', 'aws'])
    -m, --model_to_train, default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]                 
    -a, --aug, action=store_true
    -r, --rate, default=12, type=int
    -re, --retain, action='store_true'
```

- `sendload` is the principal function of this service, it is mainly used to send the prediction of the Load (2 days on). 
- `broker` is the mqtt broker you connect to.
- `rate` is the frequency of the Sendload expressed in hours.
- `model_to_train` is an argument that can be used to re-train the models 
  (make sure to collect some data before).
- `aug` is related to model_to_train and it's used to introduce some observations regarding the next month so to avoid problems 
(in particular when the month is ending).
- `retain` messages is available only while working with localhost!

### Services based on __*meteo_collector.py*__
```
    -b, --broker, required=True, type=str, choices=['localhost', 'aws'])
    -r, --rate, default=6, type=int
    -re, --retain, action='store_true'
```
- `broker` mqtt you subscribe to.
- `rate` is the frequency at which we send data expressed in hours.
- `retain` messages is available only while working with localhost!

### Services based on __*meteo_managers.py*__
```
    -c, --create_tables, action=store_true
    -p, --partially_populate, action=store_true
    -el, --external_load_path, default=None, type=str
    -eg, --external_generation_path, default=None, type=str
    -ie, --internal_energy_files, action='store_true'
    -il, --internal_load_files, action='store_true'
    -s, --storico, action=store_true
    -r, --rate, default=12, type=int
    -b, --broker, default='localhost', choices=['localhost', 'aws']
    -re, --retain, action='store_true'
```
We built a service allowing users to start their own DBs effectively. This service will create the tables automatically 
as they need to be, transferring there a small amount of the data we collected.

- `create_tables` create the tables with the correct format in the the Dbs.
- `partially_populate` transfer a small amount of data into your new Dbs.  
- `storico` store true value indicating the process of colleting current meteo and send to the mqtt broker.
- `rate` is the frequency at which we send data expressed in hours.
- `broker` mqtt you subscribe to.
- `retain` messages is available only while working with localhost!

The a proper usage of the following arguments read the documentation at [Pass external file from Terna](#pass-external-file-from-terna).
- `external_load_path` load files saved somewhere else and passed as a comma separated string as `http/drive/load.csv,https/github/load.xlsx` (reference [external path](#2-external-path))
- `external_generation_path` generation files save somewhere else and passed as before as a comma separated string (reference [external path](#2-external-path))
- `internal_energy_files` follow this procedure (reference [internal path](#1-internal-path)) and add this argument (store true) 
- `internal_load_files` follow this procedure (reference [internal path](#1-internal-path)) and add this argument (store true) 

#### Pass external file from Terna

We also allow passing new files that can be downloaded from [Terna Download Center]. 
First, there are two files that can be updated:

1. to get load data go to `Load -> Total Load`, downloadable as an Excel or a csv.
2. to get generation data, you'll need to collect two different files:
   1.  `Generation -> Energy Balance`, selecting all the possible energies in the field "type"
         *except for Net Foreign Exchange, Pumping Consumption, Self Consumption*.
   2.  `Generation -> Renewable Generation`, selecting only *Biomass*.
    
The generation data must come togheter! you can see how they look like at the following links:
- [Load data]
- [Biomass data], [Energy balance data]

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)
   [Load data]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/Documentation/Files_from_terna/load/load_07.csv>
   [Energy balance data]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/Documentation/Files_from_terna/generation/june-18.csv>
   [Biomass data]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/Documentation/Files_from_terna/generation/biomass-june-2021.csv>
   [docker]: <https://www.docker.com>
   [Git repository]: <https://github.com/GabrieleGhisleni/EnergyProject>
   [Docker Image]: <https://>
   [mosquitto.conf]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/Volumes/mosquitto/config/mosquitto.conf>
   [docker-compose.yml]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/docker-compose.yml>
   [Terna Download Center]: <https://www.terna.it/it/sistema-elettrico/transparency-report/download-center>
   [OpenWeather]: <https://openweathermap.org/>
   [extra-services.yml]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/extra-services.yml>
   [download center]: <https://www.terna.it/it/sistema-elettrico/transparency-report/download-center>