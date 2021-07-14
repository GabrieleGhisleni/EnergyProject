# Energy Project - Big Data Technologies

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)
[![JavaScript Style Guide: Good Parts](https://img.shields.io/badge/code%20style-goodparts-brightgreen.svg?style=flat)](https://github.com/dwyl/goodparts "JavaScript The Good Parts")

[Create Issue -](https://github.com/GabrieleGhisleni/EnergyProject/issues/new)
[Fork](https://github.com/GabrieleGhisleni/EnergyProject/fork)

The goal is to predict the quantity of energy from renewable sources that can be produced in an hour and in a day in 
Italy. All the code is available in this [Git repository], where you can also find the [Docker Image].

### Table of Contents

| Argument | Description |
| --------------|---------------|
| [How to run the application](#how-to-run-the-application) | Description of how to run the application using our DBs and brokers.|
| [Arguments available](#arguments-available) | Brief description of the arguments that can be passed to the docker-compose.yml|
| [Change the services](#change-the-services) | Guide for switching from our DBs and brokers to yours.|  


While in the first paragraph we will show how to run the application for the very first time using our DBs and our 
mosquitto broker, in the second one we will illustrate the arguments that can be passed to the scripts. Lastly, we 
will explain how to detach our services and replace them with yours (in particular your mysql DB). 

## How to run the application

> First, we will show how to run the application using the services we defined, such as our Amazon RDS MySql database and our Mosquitto 
broker, which are both hosted on Amazon AWS.  
**Then we will explain how to change those services and replace them with yours.**

It is required a basic understanding of how to use [docker]. 
In any case, the first step would be pulling the [Docker Image] attached to this github page, running the following command:

```sh
docker pull docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
```

We suggest to create a fresh directory where the following structure should be replicated:

```
## Directory's tree
FreshFolder
|-- docker-compose.yml
|-- energy.env
|-- Volumes
|   |-- django
|   |-- mysql
|   |-- redis 
|   |-- mosquitto
|   |   |-- config
|   |   |      |-- mosquitto.conf
```
In particular:
 1. Create an empty folder.
 2. Create, inside this folder, a docker-compose.yml and an energy.env file.
 3. Create a sub-directory called "Volumes" with four more sub-directory: 
    "mosquitto", "mysql", "django", "redis" and let those empty.
 4. Creating a file called mosquitto.conf in the mosquitto/config folder. Then paste the following lines inside this mosquitto.conf file (you can also find the 
    [mosquitto.conf] here):
    
```sh
## mosquitto.conf
allow_anonymous true
listener 1883
```


To run the code with our services it is necessary to now create the [docker-compose.yml] as follows:

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

  mqtt:
    image: eclipse-mosquitto
    container_name: mqtt
    volumes:
    - ./Volumes/mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf
    ports:
    - "1883:1883"

  mysql:
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    env_file:
      - energy.env
    ports:
    - 3307:3306

  # Web App
  web_app:
    image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
    tty: false
    command: bash -c "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
    container_name: energyDjango
    env_file:
      - energy.env
    depends_on:
      - redis
    ports:
    - "8000:8000"
    volumes:
    - ./Volumes/django:/src/Volumes/django

  # Services base on mqtt_managers
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
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic thermal"
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
      command:  bash -c "python Code/meteo_collector.py --broker aws"
      depends_on:
        - forecast_meteo_receiver
        - mqtt
      env_file:
        - energy.env

  # models_manager based
  load_sender:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy
      container_name: load_sender
      command:  bash -c "python Code/models_manager.py --broker aws --sendload"
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
The last step is to create the energy.env file containing all passwords and environmental variables that are 
passed to the code.  
As mentioned, it is always possible to change passwords and variables according to your services (e.g. to use your own databases).
Later on there will be the exact procedure to follow.

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

Now the application can be run for the very first time! Open the CLI of your PC and go to the folder that was just 
created. Once you are there, type the on of following command:

C:\..\your_fresh_directory> `docker-compose up`

Follow the printing statement and click on the hyperlink displayed at the end!
When the process is done you will see this:

![Image](../master/Display/media/Done.JPG)

Clink on the hyperlink:

> Done! - Check the data on  http://127.0.0.1:8000/today-prediction/

This link will open your browser directly to your localhost where you'd find the application running! 
Various functionalities are available, such as today or tomorrow predictions, the browsable API (the description of how 
to use it is in that same page) and the rest of the application:

![Image](../master/Display/media/pred_t.PNG)

## Arguments available

> Before illustrating how to change the services according to the user's needs, we make a brief overview of the
arguments that can be passed to the script through the docker-compose.


1.  Services based on __*mqtt_managers.py*__
```
 -b, --broker, default='localhost', choices=['localhost', 'aws']
 -t, --topic, required=True, choices=['forecast', 'energy', 'thermal', 'load', 'all', 'storico']
 -r, --retain, action=store_true
 -ex, --expiration_time, default=24, type=int
```

- Retain is available only when works with localhost!
- Expiration time refers to the expiration time that the predictions will be available Redis.
- Broker is the mqtt broker to connect.
- Topic refers to the particular topic to subscribe.

2. Services based on __*models_manager.py*__
```
    -l, --sendload, action=store_true, 
    -b, --broker, default='localhost', choices=['localhost', 'aws'])
    -m, --model_to_train, default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]                 
    -a, --aug, action=store_true
    -r, --rate, default=12, type=int
```

- Sendload is the principal function of this service, it is used to principally send the prediction of the Load (2 days on). 
- Broker is the mqtt broker to connect
- Rate is the frequency of the Sendload expressed in hours
- Model_to_train is an argument that can be used in case you want to train again the models 
  (make you that you collect some data before)
- Aug is related to model_to_train and is used to introduce some observation of the next month so to avoid problems 
(in particual when the month is ending).
  
3. Services based on __*meteo_managers.py*__
```
    -c, --create_tables, action=store_true
    -p, --partially_populate, action=store_true
    -el, --external_load_path, default=None, type=str
    -eg, --external_generation_path, default=None, type=str
    -s, --storico, action=store_true
    -r, --rate, default=12, type=int
    -b, --broker, default='localhost', choices=['localhost', 'aws']
```
We built a service allowing users to start their own DBs effectively. This service will create the tables automatically 
as they need to be, transferring there a small amount of the data we collected.
In the next section we will explain in details how to do that.

- Create_tables and Partially_populate populate belong to the service that is used to transfer the data into your database.

We also allow passing new files that can be downloaded from [Terna Download Center].  

- External_load_path and External_generation_path are path that points to additional files. 
  
Make sure to follow the procedure indicate below if you want to add files. 
if there are more than one just pass a string and use comma to separate files as:

`
 --external_generation_path github/../biomass.csv,drive/mydrive/load.xlsx
`

There are two files that can be updated:
1. `Load -> Total Load`, it can be downloaded as an Excel or a csv.
2. Here you have to collect two different files:
   1.  `Generation -> Energy Balance`, select all the possible energies in the field "type"
         *except for Net Foreign Exchange, Pumping Consumption, Self Consumption*.
   2.  `Generation -> Renewable Generation`, then select only *Biomass*.
   
- Rate argument refers to the rate at which we collect the "meteo data" that will be uploaded on the DBs (the history). The default
is "hourly", but it can be set differently. Be aware of the fact that the minimum rate is "hourly", so setting it lower would not 
give particular benefits.
  
- Storico is the the arguments that indicate the procedure of starting collecting data (store_true).

4. Services based on __*meteo_collector.py*__
```
    -b, --broker, required=True, type=str, choices=['localhost', 'aws'])
    -r, --rate, default=6, type=int
```
- Broker mqtt to subscribe
- Rate is the frequencies of sending data expressed in hours.

## Change the services

> 1. Change MySql Database

To change the mysql DB you have to modify the mysql service in the docker-compose.yml and the energy.env file as follows. 
You would need to insert into the brackets `< >` the data that you want to use as well.  

**Make sure that the folder "mysql" is still empty. If that's not the case, delete all the elements before starting 
this procedure. If there is some problem deleting check if there is an instance container associated with and in case remove it**

```shell
## docker-compose.yml
# mysql_service
  mysql: # <- same to specify inside .env as MYSQL_HOST
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    environment:
    - MYSQL_USER = <your_new_user>  # same to specify inside .env AS MYSQL_USER
    - MYSQL_PASSWORD = <your_new_psw> # same to specify inside .env AS MYSQL_PASSWORD
    - MYSQL_ROOT_PASSWORD = <your_new_psw>  
    ports:
    - 3307:3306
```

**We also provide a service that can be used to create the correct tables inside your fresh database! is it highly 
recommended at least to transfer the tables of the database**, specifying also the argument --partially_populate 
a part of the data will be transferred to you (also recommended).

```shell
 #Make sure that the volumes folder of mysql is empty!
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

Before run the script modify also the energy.env file as follow:

```shell
## energy.env
# mysql_service
MYSQL_HOST=<mysql> # name of the mysql service
MYSQL_USER=<your_new_user> # parameter specified inside .yml
MYSQL_PASSWORD=<your_new_psw>   # parameter specified inside .yml
MYSQL_DATABASE=energy
```

If you downloaded new data from the "download center" and you want to pass it to the scripts, modify 
the `command` of the transfer_service as follows:

```shell
## docker-compose.yml -> transfer_service
command: bash -c "sleep 45 && python Code/meteo_managers.py \
--create_tables True --partially_populate True \
--external_load_path ['https://link-to-the-storage/<yourfile>.csv'] \
--external_generation_path [https://raw.githubusercontent.com/<yourfile>.csv]
```

Otherwhise run the command:

C:\..\your_fresh_directory> ```docker-compose up transfer_service```

After have done that remeber to **remove the trasnfer_service from the docker-compose or comment it so to avoid 
upload multiple time the same data**.

Instead if you do not want that the tables are generated neither the data are passed follow this: run the mysql 
service alone, (the very first time it took around 1 minute to prepare the volumes) as:

C:\..\your_fresh_directory> ```docker-compose up mysql```

it takes around 40 seconds, it finishes when the following message id displayed:

> /usr/sbin/mysqld: ready for connections. Version: '8.0.25'  socket: '/va
r/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.

then you are able to run 

C:\..\your_fresh_directory> ```docker-compose up```

> 2. Change Mqtt Broker

To do this **you must have configured the mosquitto.conf** file as shown before. It can be observed that we already provide the 
service for mosquitto in the docker-compose. To complete this step you should just change the broker parameter from 'aws' to 'localhost' in all the sections `command` of the docker-compose.yml
as:

```
  command:  bash -c "python Code/meteo_collector.py --broker localhost"
```

**Be sure that all the services refer to the same broker.**

> 3. Re-train the models

Add this service and specify the model that you want to train from ['all', "wind", "hydro", "load", 
"thermal", "geothermal", "biomass", "photovoltaic"]. we also recommend to let --aug equal to True.

```shell
  train_models:
      image: docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest
      container_name: train_models
      command:  bash -c "python Code/models_manager.py --model_to_train all --aug"
      depends_on:
        - mysql
      env_file:
        - energy.env
```

Run this only service with ```docker-compose up train_models```

Then you have to commit the change to the image as follow:

1. ``` docker ps -a``` search for the container having as name trained_models and copy the ID.
2. `docker commit <IDcontainertrain_models> docker.pkg.github.com/gabrieleghisleni/energyproject/energy:latest`

Doing this operation the fresh models will be available for also the others services.

> 4. OpenWeather Secret API Keys

Go the [OpenWeather] and follow the instruction to get the free API keys.

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)
   [docker]: <https://www.docker.com>
   [Git repository]: <https://github.com/GabrieleGhisleni/EnergyProject>
   [Docker Image]: <https://>
   [mosquitto.conf]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/Volumes/mosquitto/config/mosquitto.conf>
   [docker-compose.yml]: <https://github.com/GabrieleGhisleni/EnergyProject/blob/master/docker-compose.yaml>
   [Terna Download Center]: <https://www.terna.it/it/sistema-elettrico/transparency-report/download-center>
   [OpenWeather]: <https://openweathermap.org/>
   [How to run the application]: <##first> 
   [Arguments available]: <##second>
   [Change the services]: <##third>
