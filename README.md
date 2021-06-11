# GDS Accessibility Monitoring Platform

The accessibility monitoring platform is to support the accessibility auditing process in GDS.

It uses Django, PostgreSQL, and the Gov UK frontend design system.

## Index

- [Requirements](#Requirements)

- [How to get started](#How-to-get-started)

- [Start local development environment](#Start-local-development-environment)

- [ADR Records](#ADR-Records)

- [Testing](#Testing)

- [Pulp](#Pulp)

- [Root dir files explainer](#Root-dir-files-explainer)

---
## Requirements

- Docker
- Python 3.8
- PostgreSQL
- Node and NPM
- Standard JS Globally installed (if using VSCode)
- AWS CLI version 2

---
## How to get started

To set up your local sandbox, follow the instructions below.

1. Create a virtual environment
2. Activate the virtual environment
3. Copy .env.example as .env
4. Create a Django secret key
5. Fill in AWS_ACCESS_KEY_ID_S3_STORE and AWS_SECRET_ACCESS_KEY_S3_STORE, SECRET_KEY in with Django secret key in .env
6. Run `make init`

For example:

```
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe())"
nano .env
make init
```
---
## Start local development environment

To launch the development environment:

1. Start the pgAdmin and Postgres SQL environment
2. Start the Django server
3. Start the Pulp watch process in a new terminal
4. Start browser-sync (if needed) in a new terminal
5. Start the local email server (if needed) in a new terminal

For example

```
docker-compose up -d
make start
make watch
make sync
make mail_server
```
---
## ADR Records

To create a new Architecture Design Record (ADR):

1. Ensure `adr` is installed
2. Use `adr new` if you are making a new design record
3. Use `adr new -s` if you are superseding a previous design record

For example

```
brew install adr-tools
adr new Implement as Unix shell scripts
adr new -s 9 Use Rust for performance-critical functionality
```
---
## Testing

There is currently three types of automated testing; unit, integration and lighthouse testing.

Static files need to be collected by Django before starting unit tests. The tests will fail unless this step is completed. This can be executed with

```
python manage.py collectstatic
```

Unit testing is started with

```
make test
```

The make command will start the test suite in coverage and show how much the tests cover the code. It is best to aim for 90% coverage.

Integration can be started with

```
make int_test
```

The make command will start a docker-compose stack and execute python unit tests located in integration tests. If you are writing integration tests, the stack can be started with `make dockerstack`, and starting the tests with `int_test_no_docker`.

N.B. Lighthouse tests are not implemented at this time.

Lighthouse testing can be started with

```
make lighthouse_audit
```

This will crawl the web app with and without authentication, compile a list of webpages in the app, audit each webpage with Google Lighthouse, and then write the topline figures to `lighthouse-tests/results_auth.json` and `lighthouse-tests/results_noAuth.json`. It is best to aim for at least a 100% accessibility score.

Individual pages can be added to `lighthouse-tests/specific-domains.txt`.

Lighthouse won't catch all issues but will ensure a consistent level of quality.

---

## Pulp

Pulp is our proprietary Python replacement for Gulp and handles the deployment of JS, SCSS, and static files.

Gulp and Node were causing dependency issues, so we removed as much from the Node environment as could. It still uses Node to process the JS code, but Python manages the rest.

It currently
- Transpiles SCSS to CSS
- Copies the static images and fonts to the static folder in the Django app
- Transpiles JS with Babel, Browserify, and Uglify.

In the future, it may
- Monitor files for changes and automatically trigger a pipeline.
- Find a streamlined approach to work with browser-sync
- Use Django to trigger the build process
- Targeted file watching and functions

To trigger a build, simply use `make static_files_process`

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