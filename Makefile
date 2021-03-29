init:
	pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm link gulp \
		&& npm i \
		&& npm install --only=dev \
		&& gulp build \
		&& docker-compose up -d \
		&& sleep 20 \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database domain_register;" \
		&& echo "password is secret" \
		&& pg_restore --no-privileges --no-owner -h localhost -p 5432 -U admin -d domain_register -1 ./data/pubsecweb_210216.pgadmin-backup \
		&& ./manage.py migrate query_local_website_registry --database=accessibility_domain_db \
		&& ./manage.py migrate \
		&& python3 manage.py loaddata ./data/auth_data.json \
		&& psql -Atx postgres://admin:secret@localhost:5432/domain_register -c "\COPY pubsecweb.nuts_conversion FROM './data/Local_Authority_District_(December_2018)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2018)_Lookup_in_United_Kingdom.csv' DELIMITER ',' CSV HEADER;"
		&& echo "email is admin@email.com and password is secret"

start:
	python manage.py runserver 8081

sync:
	gulp serve

mail_server:
	python -m smtpd -n -c DebuggingServer localhost:1025

test:
	coverage run --source='.' manage.py test && coverage report --skip-covered && coverage erase

lighthouse_audit:
	node lighthouse-tests/lighthouse-test.js

load_data:
	python3 manage.py loaddata $(value db_data)

local_deploy:
	pipenv lock -r > requirements.txt
	cf push -f manifest-test.yml
