ENVFILE=.env

init:
	pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm i \
		&& npx gulp build \
		&& mkdir -p data \
		&& docker-compose up -d \
		&& source .env \
		&& eval `cat $(ENVFILE)` && \
			export AWS_DEFAULT_REGION="$${AWS_DEFAULT_REGION_S3_STORE}" \
			export AWS_ACCESS_KEY_ID="$${AWS_ACCESS_KEY_ID_S3_STORE}" \
			export AWS_SECRET_ACCESS_KEY="$${AWS_SECRET_ACCESS_KEY_S3_STORE}" \
		&& [ -f "./data/s3_files/20210604_auth_data.json" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/fixtures/20210604_auth_data.json ./data/s3_files/20210604_auth_data.json \
		&& [ -f "./data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/extra/Local_Authority_District_\(December_2018\)_to_NUTS3_to_NUTS2_to_NUTS1_\(January_2018\)_Lookup_in_United_Kingdom.csv "./data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv" \
		&& [ -f "./data/s3_files/pubsecweb_210216.pgadmin-backup" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/pubsecweb/pubsecweb_210216.pgadmin-backup ./data/s3_files/pubsecweb_210216.pgadmin-backup \
		&& [ -f "./data/s3_files/a11ymon_mini_20210527.sql" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/a11ymon/a11ymon_mini_20210527.sql ./data/s3_files/a11ymon_mini_20210527.sql \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database a11ymon;" \
		&& export PGPASSWORD=secret; pg_restore --no-privileges --no-owner -h localhost -p 5432 -U admin -d a11ymon -1 ./data/s3_files/pubsecweb_210216.pgadmin-backup \
		&& psql -h localhost -p 5432 -U admin -d a11ymon < ./data/s3_files/a11ymon_mini_20210527.sql \
		&& psql -h localhost -p 5432 -U admin -d a11ymon -c "ALTER SCHEMA a11ymon_mini RENAME TO a11ymon" \
		&& ./manage.py migrate query_local_website_registry --database=pubsecweb_db \
		&& ./manage.py migrate \
		&& python3 manage.py loaddata ./data/s3_files/20210604_auth_data.json \
		&& psql -Atx postgres://admin:secret@localhost:5432/a11ymon -c "\COPY pubsecweb.nuts_conversion FROM './data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv' DELIMITER ',' CSV HEADER;" \
		&& echo "email is admin@email.com and password is secret"

start:
	python manage.py runserver 8081

sync:
	npx gulp serve

mail_server:
	python -m smtpd -n -c DebuggingServer localhost:1025

test:
	coverage run --source='.' manage.py test accessibility_monitoring_platform.apps.axe_data accessibility_monitoring_platform.apps.query_local_website_registry && pytest && coverage report --skip-covered && coverage erase

lighthouse_audit:
	node lighthouse-tests/lighthouse-test.js

load_data:
	python3 manage.py loaddata $(value db_data)

local_deploy:
	pipenv lock -r > requirements.txt
	cf push -f manifest-test.yml

perm_for_chrome:
	chmod 755 integration_tests/chromedriver

int_test:
	python3 integration_tests/main.py

int_test_no_docker:
	python3 integration_tests/main.py --ignore-docker

dockerstack:
	docker-compose -f docker/int_tests.docker-compose.yml down --volumes
	docker build -t django_amp -f - . < docker/django_app.Dockerfile
	docker-compose -f docker/int_tests.docker-compose.yml up

dockerstack_stop:
	docker-compose -f docker/int_tests.docker-compose.yml down
	docker-compose -f docker/int_tests.docker-compose.yml down --volumes
