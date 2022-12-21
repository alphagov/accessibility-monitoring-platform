FROM --platform=linux/amd64 python:3.9.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable nodejs
WORKDIR /code
COPY . /code/
RUN pip install -r requirements_for_test.txt
RUN npm install
