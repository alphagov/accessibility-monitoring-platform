ENVFILE=.env

init:
	pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm i \
		&& python3 -c 'from pulp import *; pulp()' \
		&& mkdir -p data \
		&& docker-compose up -d \
		&& source .env \
		&& eval `cat $(ENVFILE)` && \
			export AWS_DEFAULT_REGION="$${AWS_DEFAULT_REGION_S3_STORE}" \
			export AWS_ACCESS_KEY_ID="$${AWS_ACCESS_KEY_ID_S3_STORE}" \
			export AWS_SECRET_ACCESS_KEY="$${AWS_SECRET_ACCESS_KEY_S3_STORE}" \
		&& [ -f "./data/s3_files/20210604_auth_data.json" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/fixtures/20210604_auth_data.json ./data/s3_files/20210604_auth_data.json \
		&& [ -f "./data/s3_files/region_and_sector.json" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/fixtures/region_and_sector.json ./data/s3_files/region_and_sector.json \
		&& [ -f "./data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/extra/Local_Authority_District_\(December_2018\)_to_NUTS3_to_NUTS2_to_NUTS1_\(January_2018\)_Lookup_in_United_Kingdom.csv "./data/s3_files/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv" \
		&& [ -f "./data/s3_files/pubsecweb_20210615.pgadmin-backup" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/pubsecweb/pubsecweb_20210615.pgadmin-backup ./data/s3_files/pubsecweb_20210615.pgadmin-backup \
		&& [ -f "./data/s3_files/a11ymon_mini_20210527.sql.zip" ] && echo "file exists" || aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/a11ymon/a11ymon_mini_20210527.sql.zip ./data/s3_files/a11ymon_mini_20210527.sql.zip \
		&& [ -f "./data/s3_files/a11ymon_mini_20210527.sql" ] && echo "file exists" || unzip -o ./data/s3_files/a11ymon_mini_20210527.sql.zip \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database a11ymon;" \
		&& export PGPASSWORD=secret; pg_restore --no-privileges --no-owner -h localhost -p 5432 -U admin -d a11ymon -1 ./data/s3_files/pubsecweb_20210615.pgadmin-backup \
		&& psql -h localhost -p 5432 -U admin -d a11ymon < ./data/s3_files/a11ymon_mini_20210527.sql \
		&& psql -h localhost -p 5432 -U admin -d a11ymon -c "ALTER SCHEMA a11ymon_mini RENAME TO a11ymon" \
		&& ./manage.py migrate query_local_website_registry --database=pubsecweb_db \
		&& ./manage.py migrate \
		&& python3 manage.py loaddata ./data/s3_files/20210604_auth_data.json \
		&& python3 manage.py loaddata ./data/s3_files/region_and_sector.json \
		&& echo "email is admin@email.com and password is secret"

start:
	python manage.py runserver 8081

static_files_process:
	python3 -c 'from pulp import *; pulp()'

watch:
	npx nodemon -e scss,js --watch accessibility_monitoring_platform/static/scss --watch accessibility_monitoring_platform/static/js --exec "python3 -c 'from pulp import *; pulp()'"

sync:
	npx browser-sync start -p http://127.0.0.1:8081/ \
		--files "./accessibility_monitoring_platform/**/*.py" \
		--files "./accessibility_monitoring_platform/**/*.html" \
		--files "./accessibility_monitoring_platform/static/compiled/*.scss" \
		--files "./accessibility_monitoring_platform/static/compiled/**" \
		--watchEvents change --watchEvents add \
		--reload-delay 500

mail_server:
	python -m smtpd -n -c DebuggingServer localhost:1025

test:
	python manage.py collectstatic --noinput \
		&& coverage run --source='.' -p manage.py test \
		&& coverage run -m -p pytest \
		&& coverage combine \
		&& coverage report --skip-covered \
		&& coverage erase

# Currently out of use
# lighthouse_audit:
# 	node lighthouse-tests/lighthouse-test.js

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
