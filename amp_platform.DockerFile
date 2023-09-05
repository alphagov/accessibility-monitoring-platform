FROM --platform=linux/amd64 python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt update && apt upgrade -y
ENV NODE_MAJOR=18
RUN mkdir -p /etc/apt/keyrings; \
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg; \
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list; \
apt update && apt install nodejs npm -y;
RUN apt-get install postgresql -y
RUN psql --version
WORKDIR /code
COPY . /code/
RUN pip install -r requirements_for_test.txt
RUN npm install
EXPOSE 8001
CMD make static_files_process \
    && python manage.py collectstatic --noinput \
    && python manage.py migrate \
    && python manage.py recache_statuses \
    && waitress-serve --port=8001 accessibility_monitoring_platform.wsgi:application
