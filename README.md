# GDS Accessibility Monitoring Platform

The accessibility monitoring platform is to support the accessibility auditing process in GDS.

It uses Django, PostgreSQL, and the Gov UK frontend design system.

There are two Django applications included in this repo. The accessibility monitoring platform is a case management system that records testing data and publishes reports. 

The report viewer is a public-facing application used for public service bodies to view published reports.

## Index

- [Requirements](#Requirements)

- [How to get started](#How-to-get-started)

- [Start local development environment](#Start-local-development-environment)

- [Testing](#Testing)

- [Pulp](#Pulp)

- [Deploying prototypes](#Deploying-prototypes)

- [Root dir files explainer](#Root-dir-files-explainer)

---
## Requirements

- Docker
- Python 3.9
- PostgreSQL
- Node and NPM
- Standard JS Globally installed (if using VSCode)
- AWS CLI version 2
- Cloud Foundry and a PaaS login (if using prototypes)

---
## How to get started

To set up your local sandbox, follow the instructions below.

1. Create a virtual environment
2. Activate the virtual environment
3. Copy .env.example as .env
4. Fill in AWS_ACCESS_KEY_ID_S3_STORE and AWS_SECRET_ACCESS_KEY_S3_STORE in .env
5. Run `make init`

For example:

```
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
nano .env
make init
```
---
## Start local development environment

To start the accessibility monitoring platform environment:

1. Start the pgAdmin, Postgres SQL, and Localstack environment
2. Start the Django server
3. Start the Pulp watch process in a new terminal
4. Start browser-sync (if needed) in a new terminal

For example

```
docker-compose up -d
make start
make static_files_process_watch
make sync_accessibility_monitoring_platform
```

To start the report viewer platform:

1. Start the pgAdmin, Postgres SQL, and Localstack environment
2. Start the Django server
3. Start the Pulp watch process in a new terminal
4. Start browser-sync (if needed) in a new terminal

For example

```
docker-compose up -d
make start_report_viewer
make static_files_process_watch
make sync_report_viewer
```

---

## Testing

There are currently two types of automated testing; unit, and integration testing.

Unit testing is started with

```
make test
```

The make command will start the test suite in coverage and show how much the tests cover the code. It is best to aim for 90% coverage.

Integration can be started with

```
make int_test
```

The make command will emulate the production stack with docker-compose and will then simulate the actions of a user. 

When writing tests, `int_test_developer_mode` can be used to skip starting the docker containers. This is useful when writing integration tests as it's much faster than the normal integration testing process.
The settings for this mode can be found in `stack_tests/integration_tests_developer_mode_settings.json`, and the target path for tests can be changed under `test_dir`.

Ensure your tests work with `make int_test` before creating a pull request.

---

## Pulp

Pulp is our proprietary Python replacement for Gulp and handles the deployment of JS, SCSS, and static files.

Gulp and Node were causing dependency issues, so we removed as much from the Node environment as we could. It still uses Node to process the JS code, but Python manages the rest.

It currently
- Transpiles SCSS to CSS
- Copies the static images and fonts to the static folder in the Django app
- Transpiles JS with Babel, Browserify, and Uglify.

To trigger a build, simply use `make static_files_process`

---
## Deploying prototypes

To deploy a temporary prototype onto PaaS, you will need Cloud Foundry installed locally and a PaaS account.

To deploy a prototype, simply enter

```
make deploy_prototype
```

This will deploy your local branch to a brand new space in PaaS with data copied over from the testing environment. Users can then log in using their testing environment login details.

Once you are finished with the prototype, it can be broken down with,
```
make breakdown_prototype
```

---
## Root dir files explainer

- `.adir-dir` : Shows the adr where to write the new records
- `.cfignore` : Ignores files for Cloud Foundry
- `.coveragerc` : Settings for Coverage
- `.env.example` : Example settings for .env
- `.flake8` : Lints Python code to PEP8 standard
- `.gitignore` : Ignores files for git
- `.pylintrc` : Lints Python code to Google's style guide
- `docker-compose.yml` : Contains the dockerised setup for PostgreSQL and PGAdmin
- `Makefile` : Automation tool for the repo
- `manage.py` : Root access for Django
- `manifest-prod.yml` : Cloud Foundry deployment settings for production environment
- `manifest-test.yml` : Cloud Foundry deployment settings for test environment
- `package-lock.json` : Locked dependencies for NPM
- `package.json` : Tracks developer and production dependencies for Javascript
- `Pipfile` : Tracks developer dependencies and production dependencies for Python
- `Pipfile.lock` : Locked dependencies for Pipenv. Can be used with pipenv sync
- `Procfile` : Boot command for Cloud Foundry instance
- `README.md` : Documentation for the repo
- `runtime.txt` : Used for setting up environment for Cloud Foundry deployment