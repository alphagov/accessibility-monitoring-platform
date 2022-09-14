FROM python:3.9.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl
WORKDIR /code
COPY . /code/
RUN pip install -r requirements_for_test.txt
