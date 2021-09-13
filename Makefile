init:
	pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm i \
		&& python3 -c 'from pulp import *; pulp()' \
		&& mkdir -p data \
		&& docker-compose up -d \
		&& sh download_s3_files.sh \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database a11ymon;" \
		&& export PGPASSWORD=secret; pg_restore --no-privileges --no-owner -h localhost -p 5432 -U admin -d a11ymon -1 ./data/s3_files/pubsecweb_20210615.pgadmin-backup \
		&& psql -h localhost -p 5432 -U admin -d a11ymon < ./data/s3_files/a11ymon_mini_20210527.sql \
		&& psql -h localhost -p 5432 -U admin -d a11ymon -c "ALTER SCHEMA a11ymon_mini RENAME TO a11ymon" \
		&& ./manage.py migrate websites --database=pubsecweb_db \
		&& ./manage.py migrate \
		&& python3 manage.py loaddata ./data/s3_files/20210604_auth_data.json \
		&& python3 manage.py loaddata ./data/s3_files/20210903_sector.json \
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

test:
	python manage.py collectstatic --noinput \
		&& coverage run --source='.' -p manage.py test \
		&& coverage run -m -p pytest \
		&& coverage combine \
		&& coverage report --skip-covered \
		&& coverage erase

local_deploy:
	pipenv lock -r > requirements.txt
	cf push -f manifest-test.yml

perm_for_chrome:
	chmod 755 integration_tests/chromedriver

int_test:
	python3 integration_tests/main.py
