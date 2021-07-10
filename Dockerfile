FROM python:3.9
RUN pip install --upgrade pip

WORKDIR /src

ADD . /src/
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install nano
RUN export TERM=xterm

ENV PYTHONUNBUFFERED=1
ENV PYTHONPAT /src/

