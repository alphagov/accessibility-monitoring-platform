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
COPY ./data/s3_files/20210604_auth_data.json /code/data/s3_files/
COPY ./data/s3_files/pubsecweb_210216.pgadmin-backup /code/data/s3_files/
COPY ./data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv /code/data/s3_files/
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
