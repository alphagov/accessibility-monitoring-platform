FROM ubuntu:focal
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y python3 \
    python3-pip \
    nodejs \
    npm \
    libpq-dev \
    python-dev \
    python3-psycopg2 \
    postgresql \
    postgresql-contrib
WORKDIR /code
COPY requirements.txt /code/
COPY pulp/ /code/pulp/
COPY manage.py /code/
COPY package.json /code/
COPY accessibility_monitoring_platform/ /code/accessibility_monitoring_platform/
RUN pip3 install --upgrade pip
RUN pip3 install pipenv
RUN pipenv install --dev
RUN pipenv lock -r > requirements.txt
RUN pip3 install -r requirements.txt
RUN npm i
RUN python3 -c 'from pulp import *; pulp()'
