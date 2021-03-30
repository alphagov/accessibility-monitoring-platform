# GDS Accessibility Monitoring Platform

The accessibility monitoring platform is to support the accessibility auditing process in GDS.

It uses Django, PostgreSQL, and the Gov UK frontend design system.

## Index    

- [Requirements](#Requirements)

- [How to get started](#How-to-get-started)

- [Start local development environment](#Start-local-development-environment)

- [ADR Records](#ADR-Records)

- [Testing](#Testing)

- [Root dir files explainer](#Root-dir-files-explainer)

---
## Requirements

- Docker
- Python 3.8
- PostgreSQL
- Node & NPM
- Standard JS Globally installed (if using VSCode)

---
## How to get started

To set up your local sandbox, follow the instructions below.

1. Create a virtual environment
2. Activate the virtual environment
3. Install pipenv
4. Run `make init`
5. Copy .env.example as .env
6. Create a Django secret key
6. Insert missing key in .env

For example:

```
python3 -m venv venv
source venv/bin/activate
make init
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe())"
nano .env
```
---
## Start local development environment

To launch the development environment:

1. Start the pgAdmin and Postgres SQL environment
2. Start the Django server
3. Start Gulp watch in a new terminal
4. Start the local email server (if needed)

For example

```
docker-compose up -d
make start
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

There is currently two types of automated testing, unit testing and accessibility testing. 

Static files need to be collected by Django before starting unit tests. The tests will fail unless this step is completed. This can be executed with

```
python manage.py collectstatic
```

Unit testing is started with

```
make test
```

The make command will start the test suite in coverage and show how much the tests cover the code. It is best to aim for 90% coverage.

Accessibility testing can be started with

```
make lighthouse_audit
```

This will crawl the web app with and without authentication, compile a list of webpages in the app, audit each webpage with Google Lighthouse, and then write the topline figures to `lighthouse-tests/results_auth.json` and `lighthouse-tests/results_noAuth.json`. It is best to aim for at least a 100% accessibility score.

Individual pages can be added to `lighthouse-tests/specific-domains.txt`.

Lighthouse won't catch all issues but will ensure a consistent level of quality.

---

## Root dir files explainer

- `.adir-dir` : Shows the adr where to write the new records
- `.cfignore` : Ignores files for Cloud Foundry
- `.coveragerc` : Settings for Coverage
- `.env.example` : Example settings for .env
- `.flake8` : Lints Python code to PEP8 standard
- `.gitignore` : Ignores files for git
- `.pylintrc` : Lints Python code to Google's style guide
- `.stylelintrc.json` : Contains the lint settings for stylelint - mostly used for linting SASS
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
