FROM python:3.9.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash
RUN apt-get install -y nodejs
RUN apt-get install postgresql -y
WORKDIR /code
COPY . /code/
RUN pip install -r requirements_for_test.txt
RUN npm install
EXPOSE 8001
RUN make static_files_process
RUN python manage.py collectstatic --noinput
RUN python manage_report_viewer.py collectstatic --noinput
CMD python manage.py migrate \
    && python manage.py recache_statuses \
    && waitress-serve --port=8001 accessibility_monitoring_platform.wsgi:application