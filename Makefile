init:
	docker compose up -d \
		&& pip install --upgrade pip \
		&& pip install -r requirements_for_test.txt \
		&& npm i \
		&& make static_files_process \
		&& make collect_static \
		&& psql postgres://admin:secret@localhost:5432/postgres -c "create database accessibility_monitoring_app;" \
		&& python prepare_local_db.py \
		&& ./manage.py migrate \
		&& echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@email.com', 'admin@email.com', 'secret')" | python manage.py shell \
		&& echo "email: admin@email.com & password: secret"

freeze_requirements: # Pin all requirements including sub dependencies into requirements.txt
	pip install --upgrade pip-tools
	pip-compile --upgrade requirements.in

clean_local:
	docker compose down
	rm -rf ./data
	rm -rf ./node_modules
	rm -rf ./venv
	rm ./.env

start:
	python manage.py runserver 8081

start_report_viewer:
	python manage_report_viewer.py runserver 8082

static_files_process:
	node pulp/init.js ./accessibility_monitoring_platform_settings.json --nowatch

static_files_process_watch:
	node pulp/init.js ./accessibility_monitoring_platform_settings.json

collect_static:
	python3 manage.py collectstatic --noinput
	python3 manage_report_viewer.py collectstatic --noinput

test_accessibility_monitoring_platform:
	python manage.py collectstatic --noinput \
		&& coverage run -m -p pytest --ignore="stack_tests/"  --ignore="report_viewer/" -c pytest.ini \
		&& coverage run --source='./accessibility_monitoring_platform/' -p manage.py test accessibility_monitoring_platform/ \
		&& coverage combine \
		&& coverage report --skip-covered \
		&& coverage erase

test_report_viewer:
	python manage_report_viewer.py collectstatic --noinput \
		&& coverage run -m -p pytest --ignore="stack_tests/"  --ignore="accessibility_monitoring_platform/" -c pytest_report_viewer.ini \
		&& coverage combine \
		&& coverage report --skip-covered \
		&& coverage erase

test:
	make test_accessibility_monitoring_platform
	make test_report_viewer
	npm test

int_test:
	docker compose --file stack_tests/integration_tests/docker-compose.yml up --abort-on-container-exit

local_stack_up:
	docker compose --file docker-compose-full-stack.yml  up --build

local_stack_make_admin:
	docker compose exec web sh -c "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@email.com', 'admin@email.com', 'secret')\" | python manage.py shell"

local_stack_cleanup:
	rm -r data/postgres-data-full-stack

deploy_prototype:
	python aws_prototype/main.py -b up

breakdown_prototype:
	python aws_prototype/main.py -b down

new_account_prototype:
	python aws_prototype/main.py -b newaccount
