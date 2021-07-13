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
docker pull git+{bho}
```

We suggest to create a fresh directory where the following structure should be replicated:

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
In particular:
 1. Create an empty folder.
 2. Create, inside this folder, a docker-compose.yml and an energy.env file.
 3. Create a sub-directory called "Volumes" with two more sub-directory: 
    "mosquitto" and "mysql".
 4. Keep the mysql folder empty while creating a file called mosquitto.conf in the mosquitto folder. Then paste the following lines inside this mosquitto.conf file (you can also find the 
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
The last step is to create the energy.env file containing all passwords and environmental variables that are 
passed to the code.  
As mentioned, it is always possible to change passwords and variables according to your services (e.g. to use your own databases).

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

![Image](../master/Display/media/pred_t.PNG)

## Arguments available

> Before illustrating how to change the services according to the user's needs, we make a brief overview of the
arguments that can be passed to the script through the docker-compose.


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
We built a service allowing users to start their own DBs effectively. This service will create the tables automatically 
as they need to be, transferring there a small amount of the data we collected. --create_tables and 
--partially_populate belong to the service used to transfer the data into your database.

We also allow passing new files that can be downloaded from [Terna Download Center].  
It would be necessary to use --external_load_path and --external_generation_path as a list of strings where you stored these files.

There are two files that can be updated:
1. `Load -> Total Load`, it can be downloaded as an Excel or a csv.
2. Here you have to collect two different files:
   1.  `Generation -> Energy Balance`, select all the possible energies in the field "type"
         *except for Net Foreign Exchange, Pumping Consumption, Self Consumption*.
   2.  `Generation -> Renewable Generation`, then select only *Biomass*.
   
--rate argument refers to the rate at which we collect the "meteo data" that will be uploaded on the DBs (the history). The default
is "hourly", but it can be set differently. Be aware of the fact that the minimum rate is "hourly", so setting it lower would not 
give particular benefits.

3. Services based on __*models_manager.py*__
```
    -l, --sendload, default=True, type=bool, 
    -b, --broker, default='localhost', choices=['localhost', 'aws'])
    -r, --rate, default='auto
    
    -a, --aug, default='yes'
    -m, --model_to_train, default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]                 

```

The present script is mainly used to send predictions of the Load (for the next 2 days) to the mqtt broker that can be 
chosen with the --broker argument. As before, you can set a customized rate for sending the data. 

Moreover, two arguments can be used to retrain the models (remember to collect some data first). 
An argument --aug is used to introduce observations of the next month to avoid problems 
(in particular when the month is ending).

4. Services based on __*meteo_collector.py*__
```
    -b, --broker, required=True, type=str, choices=['localhost', 'aws'])
    -r, --rate, default='auto'
```

## Change the services

> 1. Change MySql Database

To change the mysql DB you have to modify the mysql service in the docker-compose.yml and the energy.env file as follows. You would need to insert
into the brackets `< >` the data that you want to use as well. **Make sure that the folder "mysql" is still empty.
If that's not the case, delete all the elements before starting this procedure.**

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
the argument --partially_populate a part of the data will be transferred to you.

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

If you downloaded new data from the "download center" and you want to pass it to the scripts, modify 
the `command` of the transfer_service as follows:

```shell
## docker-compose.yml -> transfer_service
command: bash -c "sleep 45 && python Code/meteo_managers.py \
--create_tables True --partially_populate True \
--external_load_path ['https://link-to-the-storage/<yourfile>.csv'] \
--external_generation_path [https://raw.githubusercontent.com/<yourfile>.csv]
```

> 2. Change Mqtt Broker

To do this **you must have configured the mosquitto.conf** file as shown before. It can be observed that we already provide the 
service for mosquitto in the docker-compose. To complete this step you should just change the broker parameter from 'aws' to 'localhost' in all the sections `command` of the docker-compose.yml
as:

```
  command:  bash -c "python Code/meteo_collector.py --localhost aws"
```

> 3. OpenWeather Secret API Keys

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
