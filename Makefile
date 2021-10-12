init:
	docker-compose up -d \
		&& pip install --upgrade pip \
		&& pip install pipenv \
		&& pipenv install -d \
		&& npm i \
		&& python -c 'from pulp import *; pulp()' \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& python prepare_local_db.py \
		&& ./manage.py migrate \
		&& echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@email.com', 'admin@email.com', 'secret')" | python manage.py shell \
		&& echo "email: admin@email.com & password: secret"

clean_local:
	docker-compose down
	rm -rf ./data

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

int_test:
	python3 stack_tests/main.py

deploy_prototype:
	python deploy_feature_to_paas/main.py -b up -s deploy_feature_to_paas/deploy_feature_settings.json

breakdown_prototype:
	python deploy_feature_to_paas/main.py -b down -s deploy_feature_to_paas/deploy_feature_settings.json

staging_env:
	python deploy_feature_to_paas/main.py -b up -s deploy_feature_to_paas/deploy_staging_settings.json -f true
	python3 stack_tests/main.py -s ./stack_tests/smoke_tests_stage_env_settings.json
	python deploy_feature_to_paas/main.py -b down -s deploy_feature_to_paas/deploy_staging_settings.json
