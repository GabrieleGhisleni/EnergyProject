FROM python:3.9

WORKDIR /src
RUN mkdir -p Volumes
RUN mkdir -p Volumes/django
RUN mkdir -p Volumes/extra_files
RUN mkdir -p Volumes/extra_files/load
RUN mkdir -p Volumes/extra_files/energy

ADD Code /src/Code
ADD Display /src/Display
ADD EnergyDjango /src/EnergyDjango
ADD Models /src/Models
ADD manage.py /src/
ADD requirements.txt /src/
ADD Documentation /src/Documentation

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install nano
RUN export TERM=xterm

ENV PYTHONUNBUFFERED=1
ENV PYTHONPAT /src/

