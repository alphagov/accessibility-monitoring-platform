FROM ubuntu:focal
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y python3
RUN apt install -y python3-pip
RUN apt-get install -y nodejs
RUN apt-get install -y npm
RUN apt-get install -y libpq-dev python-dev
RUN apt-get install -y python3-psycopg2
RUN apt-get install -y postgresql postgresql-contrib
WORKDIR /code
COPY requirements.txt /code/
COPY ./data/auth_data.json /code/data/
COPY ./data/pubsecweb_210216.pgadmin-backup /code/data/
COPY ./data/a11ymon210408.pgadmin-backup /code/data/
COPY data/a11ymon_mini_2021-05-04.sql /code/data/
COPY ./data/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv /code/data/
RUN pip3 install -r requirements.txt
COPY gulpfile.babel.js /code/
COPY manage.py /code/
COPY package.json /code/
COPY accessibility_monitoring_platform/ /code/accessibility_monitoring_platform/
RUN npm i
RUN npm install --only=dev
RUN npm link gulp
RUN gulp build
ARG PGPASSWORD=secret
ENV PGPASSWORD=secret
