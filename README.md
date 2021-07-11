# Energy Project - Big Data Technologies

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)
[![JavaScript Style Guide: Good Parts](https://img.shields.io/badge/code%20style-goodparts-brightgreen.svg?style=flat)](https://github.com/dwyl/goodparts "JavaScript The Good Parts")

[Create Issue -](https://github.com/GabrieleGhisleni/EnergyProject/issues/new)
[Fork](https://github.com/GabrieleGhisleni/EnergyProject/fork)

The goal is to predict the quantity of energy from renewable sources that can be produced in an hour and in a day in 
Italy. All the code in this [Git repository], where you can also find the [Docker Image].

### Table of Contents

| Argument | Description |
| --------------|---------------|
| [How to run the application](#how-to-run-the-application) | Description of how run the application using our dbs and brokers.|
| [Arguments available](#arguments-available) | Brief description of the argument that can passed to the docker-compose.yml|
| [Change the services](#change-the-services) | Guide to change from our dbs and brokers to yours.|  


Where in the first paragraph we will show how to run the application for the very first time using our dbs and our 
mosquitto broker, in the second paragraph we will show the arguments that can be passed to the scripts and lastly we 
will explain how to detach our services and replace those with yours (in particular your mysql db). 

## How to run the application

> First we will show how to run the application using our services as our Amazon RDS MySql database and our Mosquitto 
broker that are both hosted on Amazon AWS.  
**Then we will exaplin how to change those services and replace them with yours.**

We except that you are able to use [docker], at least in its basic usage. So starting from that you have to pull 
the [Docker Image] that are attached on this github page running the following command:

```sh
docker pull git+{bho}
```

We suggets to create a fresh directory where you have to replicate the following structures. 

```
## Directory's tree
/newfolder/
|-- docker-compose.yml
|-- energy.env
|-- Volumes
|   |-- mysql 
|   |-- mosquitto
|   |   |-- mosquitto.conf
```
To be more clear:
 1. Create an empty folder.
 2. Create inside this folder a docker-compose.yml and energy.env files.
 3. Create a sub-directory called Volumes in which there are two more sub-directory: 
    mosquitto and mysql
 4. Keep the mysql folder empty while in the mosquitto folder create a file called 
    mosquitto.conf and paste inside this file the following lines (you can also find the 
    [mosquitto.conf] here):
    
```sh
## mosquitto.conf
allow_anonymous true
listener 1883
```

As we said we guide you first running the code with ours services so now create the [docker-compose.yml] as follows:

```sh
## docker-compose.yml
version: '3.9'
services:
  redis:
    image: redis:latest
    container_name: redis
    ports:
    - '6379:6379'

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

  web_app:
    image: energy:latest
    tty: false
    command: bash -c "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
    container_name: energyDjango
    env_file:
      - energy.env
    depends_on:
      - redis
    ports:
    - "8000:8000"

  load_receiver:
      image: energy:latest
      container_name: load_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic load"
      depends_on:
        - forecast_meteo_receiver
      env_file:
        - energy.env

  forecast_meteo_receiver:
      image: energy:latest
      container_name:  forecast_meteo_receiver
      command: bash -c "python -u Code/mqtt_manager.py --broker aws --topic forecast"
      depends_on:
        - redis
        - mqtt
        - mysql
      env_file:
        - energy.env

  energy_receiver:
      image: energy:latest
      container_name: energy_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic energy"
      depends_on:
        - forecast_meteo_receiver
      env_file:
        - energy.env

  thermal_receiver:
      image: energy:latest
      container_name: thermal_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic thermal"
      depends_on:
        - energy_receiver
      env_file:
        - energy.env

  storico_receiver:
      image: energy:latest
      container_name: storico_receiver
      command:  bash -c "python -u Code/mqtt_manager.py --broker aws --topic storico"
      env_file:
        - energy.env
      depends_on:
        - redis
        - mqtt
        - mysql

  forecast_meteo_sender:
      image: energy:latest
      container_name: forecast_meteo_sender
      command:  bash -c "python Code/meteo_collector.py --broker aws"
      depends_on:
        - forecast_meteo_receiver
      env_file:
        - energy.env

  load_sender:
      image: energy:latest
      container_name: load_sender
      command:  bash -c "python Code/models_manager.py --sendload True --broker localhost --path Models/"
      depends_on:
        - load_receiver
      env_file:
        - energy.env

  storico_sender:
      image: energy:latest
      container_name: storico_sender
      command: bash -c "sleep 5 && python Code/meteo_managers.py --broker localhost --rate crontab "
      depends_on:
        - storico_receiver
      env_file:
        - energy.env
```
Last step is to create the energy.env file which containes all the password and the enviromental variable that are 
passed to the code.  
After this first running we will change those according to your services (so to use your databases and so on).

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

Now you are able to run the application for the very first time! Open the CLI of your PC and go to the folder that you 
made. Once there type the following command:

C:\..\your_fresh_directory> `docker-compose up`

Follow the printing statement and at the end click on the hyper link displayed!
When the process is ended you will see displayed this:

![Image](../blob/master/Display/media/done.JPG)

Clink on the hyper link:

> Done! - Check the data on  http://127.0.0.1:8000/today-prediction/

This will open you browser directly to your localhost where yui will find the application running! you can have a look 
at the functionalities as the today, tomorrow prediction, the browserable API (the description of how 
to use that is in that page) and the rest of the application:

![Image](../blob/master/Display/media/appp.JPG)

## Arguments available

> Before illustrate how to change the services a brief introduction to the
argument that can be passed to the script trough the docker-compose.


1.  Services based on __*mqtt_managers.py*__
```
 -b, --broker, default='localhost', choices=['localhost', 'aws']
 -t, --topic, required=True, choices=['forecast', 'energy', 'thermal', 'load', 'all', 'storico']
```
2. Services based on __*meteo_managers.py*__
```
    -c, --create_tables, default=False, type=bool 
    -p, --partially_populate, default=False, type=bool
    -el, --external_load_path, default=[], type=list[str]
    -eg, --external_generation_path, default=[], type=list[str]
    
    -r, --rate, default='auto', choices=['crontab', 'auto']
    -b, --broker, default='localhost', choices=['localhost', 'aws']
```
We made a services that allow you to start you dbs in a proper ways. This service will create automatically the tables 
as they have to be and it will trasnfer a little amount of data that we collected. --create_tables and 
--partially_populate belong to the service that is used to transfer the data into your database.

We also allow to pass new files that you can download from [Terna Download Center].  
You have to use --external_load_path and --external_generation_path as a list of strings where you stored this files.

There are two files that you can update:
1. `Load -> Total Load`, you can download as excel or csv.
2. Here you have to collect two different files:
   1.  `Generation -> Energy Balance` select all the possible energies in the field type
         *except for Net Foreign Exchange, Pumping Consumption, Self Consumption*.
   2.  `Generation -> Renewable Generation` and select only *Biomass*.
   
--rate argument refers to to the rate of collecting meteo data that will be upload on the dbs (the historic), by default
is set hourly but you can set differently. Be aware, the minimun rate is hourly, if you set it lower you won't 
get benefits of that.

3. Services based on __*models_manager.py*__
```
    -l, --sendload, default=True, type=bool, 
    -b, --broker, default='localhost', choices=['localhost', 'aws'])
    -r, --rate, default='auto
    
    -a, --aug, default='yes'
    -m, --model_to_train, default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]                 

```

Here this script is used to principally send the prediction of the Load (2 days on) to the mqtt broker which can be 
choicen with the --broker argument, here as before you can set the a custom rate for sending the data. 

Then we have also two argument that chan be used to re train the models (you have first to collect some data) 
and an argument --aug that is used to introduce some observation of the next month so to avoid problems 
(in particual when the month is ending).

4. Services based on __*meteo_collector.py*__
```
    -b, --broker, required=True, type=str, choices=['localhost', 'aws'])
    -r, --rate, default='auto'
```

## Change the services

> 1. Change MySql Database

To change that you have to modify the docker-compose.yml mysql and energy.env as follows and inserting 
into the the brackets `< >` the data that you want to use. **make sure that the folder mysql is still empty
otherwhise delete all the elements before starting this procedure**

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
Modify the mysql_service section inside the energy.env file as:

```shell
## energy.env
# mysql_service
MYSQL_HOST = mysql # name of the mysql service
MYSQL_USER = <your_new_user> # parameter specified inside .yml
MYSQL_PASSWORD = <your_new_psw>   # parameter specified inside .yml
```

**We also provide a service that can be used to create the correct tables inside your fresh database**, specifying 
the argument --partially_populate we also transfer to you part of the data.

```shell
## docker-compose.yml
  trasnfer_service:
    image: energy:latest
    container_name: transfer_service
    command: bash -c "sleep 45 && python Code/meteo_managers.py --create_tables True --partially_populate True
    # we pass sleep 45 because the mysql must be ready so to be reachable from the script
    depends_on:
      - mysql
    env_file:
      - energy.env
```

If you also have downloaded new data from the download center and you want to pass it to the scripts modify 
the `command` of the trasnfer_service as follows:

```shell
## docker-compose.yml -> transfer_service
command: bash -c "sleep 45 && python Code/meteo_managers.py \
--create_tables True --partially_populate True \
--external_load_path ['https://link-to-the-storage/<yourfile>.csv'] \
--external_generation_path [https://raw.githubusercontent.com/<yourfile>.csv]
```

> 2. Change Mqtt Broker

To do this **you must have configured the mosquitto.conf** as shown before. As you can see we already provide the 
service of mosquitto in the docker-compose. To complete this step you just have to change in the docker-compose.yml 
all the section `command`, changing the parameter broker from 'aws' to 'localhost' as:

```
  command:  bash -c "python Code/meteo_collector.py --localhost aws"
```

> 3. OpenWeather Secret API Keys

Go the [OpenWeather] and follow the instricution to get the free API keys.

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
