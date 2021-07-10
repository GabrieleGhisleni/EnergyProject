FROM python:3.9

WORKDIR /src

ADD Code /src/Code
ADD Display /src/Display
ADD EnergyDjango /src/EnergyDjango
ADD Models /src/Models
ADD manage.py /src/
ADD requirements.txt /src/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install nano
RUN export TERM=xterm

ENV PYTHONUNBUFFERED=1
ENV PYTHONPAT /src/

