init:
	pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm i \
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
		&& echo "email and username is admin@email.com and password is secret"

migrate:
	python manage.py migrate

dump_data:
	python3 manage.py dumpdata --natural-foreign \
		--exclude=auth.permission --exclude=contenttypes \
   	--indent=4 > data.json

load_data:
	python3 manage.py loaddata $(value db_data)

start:
	python manage.py runserver 8081

sync:
	gulp serve

mail_server:
	python -m smtpd -n -c DebuggingServer localhost:1025

coverage:
	coverage run --source='.' manage.py test && coverage report --skip-covered && coverage erase

db_restore:
	pg_restore --no-privileges --no-owner -h localhost -p 5432 -U admin -P secret -d domain_register -1 $(value db_restore_file)

kill_all:
	docker kill $(docker ps -q)

freeze:
	pipenv lock -r > requirements.txt

ignore:
	/tmp/lifecycle/shell