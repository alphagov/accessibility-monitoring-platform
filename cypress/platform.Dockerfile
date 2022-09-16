FROM python:3.9.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash
RUN apt-get install -y nodejs
WORKDIR /code
COPY pulp/ /code/pulp/
COPY cypress/ /code/cypress/
COPY manage_report_viewer.py /code/
COPY manage.py /code/
COPY common/ /code/common/
COPY package.json /code/
COPY Makefile /code/
COPY requirements.txt /code/
COPY requirements_for_test.txt /code/
RUN pip install -r requirements_for_test.txt
RUN npm install
COPY report_viewer/ /code/report_viewer/
COPY accessibility_monitoring_platform/ /code/accessibility_monitoring_platform/
