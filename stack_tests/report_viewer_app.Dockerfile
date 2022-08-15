FROM python:3.9.12
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get -y install curl gnupg
RUN apt-get install -y python3-pip python-dev libpq-dev
RUN apt-get install -y python3-psycopg2 \
    postgresql \
    postgresql-contrib
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash
RUN apt-get -y install nodejs
WORKDIR /code
COPY requirements.txt /code/
COPY pulp/ /code/pulp/
COPY manage_report_viewer.py /code/
COPY manage.py /code/
COPY common/ /code/common/
COPY package.json /code/
COPY Makefile /code/
COPY Pipfile /code/
RUN pip3 install --upgrade pip
RUN pip3 install pipenv
RUN pipenv install -d
RUN pipenv install
RUN pipenv requirements > requirements.txt
RUN pip3 install -r requirements.txt
RUN npm i
COPY report_viewer/ /code/report_viewer/
COPY accessibility_monitoring_platform/ /code/accessibility_monitoring_platform/
