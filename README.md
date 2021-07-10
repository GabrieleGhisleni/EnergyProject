# Energy Project - Big Data Technologies

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)
[![JavaScript Style Guide: Good Parts](https://img.shields.io/badge/code%20style-goodparts-brightgreen.svg?style=flat)](https://github.com/dwyl/goodparts "JavaScript The Good Parts")

[Create Issue -](https://github.com/user/repository/issues/new)
[Fork](https://github.com/user/repository/fork)


This project aim to predict the possible imbalance on the italian network.
you can find all the code here [[git-repo-url]]

## How to run the application

> First we will show how to run the application using our services as our 
Amazon RDS MySql database and our Mosquitto broker that are both hosted on Amazon AWS. 
**After that we will explain how to change those and replace with your services.**

We except that you are able to use [docker], at least in its basic
usage. So starting from that you have to pull the image that are 
attached on this github page running the following command:

```sh
docker pull git+{bho}
```

We suggets to create a fresh directory where you have to replicate the
following structures. To be more clear inside the new folder that you created
you have to create a folder called 'Volumes' in which you have to create 
a 'mysql' folder that have to be empty and another folder called 'mosquitto'
where inside you have to put the mosquitto.conf (the file is below)

```
# Tree of directory
/newfolder/
|-- docker-compose.yml
|-- energy.env
|-- Volumes
|   |-- mysql 
|   |-- mosquitto
|   |   |-- mosquitto.conf
```

The mosquitto.conf is the following, you can also find it here[link to git]

```sh
# mosquitto.conf
allow_anonymous true
listener 1883
```

after have done that you have to create the following docker-compose.yml file

```sh
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
last but not least you have to create the following energy.env file.
As we said before first we will guide you running the application with our
services and then we will exaplin how to change the database (we also provide
a service that automatically create the necessary tables and provide you some
of the data that we collected)

```sh
# energy.conf

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

after have done so open a terminal and go to the folder that you made
and running the command to run the docker-compose

```
docker-compose up
```

Follow the printing statement and at the end click on the hyper link displayed

> Done! - Check the data on  http://127.0.0.1:8000/today-prediction/

### Arguments available

> Before illustrate how to change the services a brief introduction to the
argument that can be passed to the script trough the docker-compose.

1.  Services based on __*mqtt_managers.py*__
```
- -b, --broker, default='localhost', choices=['localhost', 'aws']
- -t, --topic, required=True, choices=['forecast', 'energy', 'thermal', 'load', 'all', 'storico']
```
2. Services based on __*meteo_managers.py*__
```
    -c, --create_tables, default=False, type=bool 
    -p, --partially_populate, default=False, type=bool
    -r, --rate, default='auto', choices=['crontab', 'auto']
```
--create_tables and --partially_populate belong to the service that is used to transfer 
the data into your database while the rate refers to to the rate of collecting meteo data
that will be upload on the dbs, by default s set to hour (each hour) but you can set 
differently

3. Services based on __*models_manager.py.py*__
```
    -l, --sendload, default=True, type=bool, 
    -b, --broker, default='localhost', choices=['localhost', 'aws'])
    -r, --rate, default='auto
    -a, --aug, default='yes'
    -m, --model_to_train, default=None, choices=['all', "wind", "hydro", "load", "thermal", "geothermal", "biomass", "photovoltaic"]                 

```

Here this script is used to principally send the load prediction to the mqtt broker which
can be choicen with the --broker argument, here as before you can set the a custom rate for 
sending the data. Then we have also two argument that chan be used to re train the model
(you have first to collect some data) and an argument --aug that is used to introduce some
observation of the next month so to avoid problems when the we the month change.

4. Services based on __*meteo_collector.py.py*__
```
    -b, --broker, required=True, type=str, choices=['localhost', 'aws'])
    -r, --rate, default='auto'
```

## Change the services

> 1. Change Mqtt Broker

To do this **you must have configured the mosquitto.conf** as shown before. 
As you can see we already provide the service of mosquitto in the docker-compose. 
To complete this step you just have to change in the docker-compose.yml 
all the section command, changing the parameter broker from 'aws' to 'localhost' as:

```
  command:  bash -c "python Code/meteo_collector.py --localhost aws"
```

2. Change MySql Database

To change that you have to modify the docker-compose.yml mysql and energy.env
as follows:

```shell
## docker-compose.yml
# mysql_service
  mysql: # <- name to specify as mysql_host
    image: mysql:latest
    container_name: mysql
    volumes:
    - ./Volumes/mysql:/var/lib/mysql
    environment:
    - MYSQL_USER = <your_new_user>  # same to specify inside .env
    - MYSQL_PASSWORD = <your_new_psw> # same to specify inside .env
    - MYSQL_ROOT_PASSWORD = <your_new_psw>  
    ports:
    - 3307:3306
```

```shell
## energy.env
# mysql_service
MYSQL_HOST = mysql # name of the mysql service
MYSQL_USER = <your_new_user> # parameter specified inside .yml
MYSQL_PASSWORD = <your_new_psw>   # parameter specified inside .yml
```

We also provide a service that can be used to create the right tables inside
youy fresh database and specifying the argument --partially_populate we also 
transfer you part of the data so you won't start from zero collecting the data.

```shell
  trasnfer_service:
    image: energy:latest
    container_name: transfer_service
    command: bash -c "sleep 45 && python Code/meteo_managers.py --create_tables True --partially_populate True --file_paths Documentation/Files_from_terna"
    depends_on:
      - mysql
    env_file:
      - energy.env
```

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)
   [docker]: <https://www.docker.com>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
