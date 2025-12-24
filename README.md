# GDS Accessibility Monitoring Platform

The accessibility monitoring platform is to support the accessibility auditing process in GDS.

It uses Django, PostgreSQL, and the Gov UK frontend design system.

There are two Django applications included in this repo. The accessibility monitoring platform is a case management system that records testing data and publishes reports.

The report viewer is a public-facing application used for public service bodies to view published reports.

## Index

- [Requirements](#requirements)

- [How to get started](#how-to-get-started)

- [Start local development environment](#start-local-development-environment)

- [Testing](#testing)

- [Pulp](#pulp)

- [Deploying prototypes](#deploying-prototypes)

- [Root dir files explainer](#root-dir-files-explainer)

## Requirements

- Docker
- Python 3.12
- PostgreSQL
- Node and NPM
- Standard JS Globally installed (if using VSCode)
- AWS CLI version 2

## How to get started

To setup AWS access, follow the instructions below.

1. Ensure you have an account on the production AWS account
2. Add your AWS credentials under the `default` profile in `~/.aws/credentials`
3. Enter `export AWS_PROFILE=mfa` in the command line
4. Alternatively, permanently add it to .zshrc with `echo -e "\nexport AWS_PROFILE=mfa" >> ~/.zshrc`
5. Set the `mfa` profile using the `python aws_tools/aws_2fa.py default 123456` and replace 123456 with your 6-digit MFA code

You should now be able to access AWS services. You can test you have the right access with `aws s3 ls`

To set up your local sandbox, follow the instructions below.

1. Create a virtual environment
2. Activate the virtual environment
3. Copy .env.example as .env
4. Run `pip install pre-commit` (enables pre-commit checks in
[.pre-commit-config.yaml](https://github.com/alphagov/accessibility-monitoring-platform/blob/dev/.pre-commit-config.yaml))
5. Run `make init`

For example:

```
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
make init
```

## Start local development environment

To start the accessibility monitoring platform environment:

1. Start the pgAdmin, Postgres SQL, and Localstack environment
2. Start the Django server
3. Start the Pulp watch process in a new terminal
4. Start browser-sync (if needed) in a new terminal

For example

```
docker compose up -d
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
docker compose up -d
make start_report_viewer
make static_files_process_watch
make sync_report_viewer
```


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

The make command will emulate the production stack with `docker compose` and will then simulate the actions of a user using cypress.

To run these tests interactively in the local sandbox:

1. `python manage.py init_int_test_data`
1. `cd stack_tests/integration_tests`
1. `npx cypress open`

Ensure your tests work with `make int_test` before creating a pull request.


## Pulp

Pulp handles the deployment of JS, SCSS, and static files.

It currently
- Transpiles SCSS to CSS
- Copies the static images and fonts to the static folder in the Django app
- Transpiles JS with Babel, Browserify, and Uglify.

To trigger a build, simply use `make static_files_process`

## Deploying prototypes

WARNING: THIS FEATURE IS NEW AND HIGHlY EXPERIMENTAL. YOU ARE LIKELY TO FACE ISSUES WHEN DEPLOYING PROTOTYPES.

Deploying prototypes runs in AWS Copilot and you will need access to the AWS test account.

To deploy a prototype, first set your temporary AWS credentials for the test account:

`python aws_tools/aws_2fa.py [test-aws-account] [nnnnnn]`

then enter

```
make deploy_prototype
```

This will deploy your local branch to a brand new Copilot app in AWS with a backup of the production data.
Users can then log in using their production environment login details or be given a burner account with new login details.

Running `make deploy_prototype` updates an existing prototype.

Once you are finished with the prototype, it can be broken down with,

```
make breakdown_prototype
```

The deployment process can take a while. A new app take upwards of an hour and an update can take around 30mins. Breaking down an app takes around 30 minutes.

A new burner account can be made at any time using:

```
make new_account_prototype
```

## Root dir files explainer

- `.coveragerc` : Settings for Coverage
- `.dockerignore` : Tells which files Docker should ignore when building images
- `.env.example` : Example settings for .env
- `.flake8` : Lints Python code to PEP8 standard
- `.gitignore` : Ignores files for git
- `.htmlhintrc` : Lints HTML
- `.pre-commit-config.yaml` : Lints the code with Black prior to commiting
- `.pylintrc` : Lints Python code to Google's style guide
- `amp_platform.DockerFile` : The Dockerfile for AMP. Used in Copilot.
- `amp_viewer.DockerFile` : The Dockerfile for the viewer. Used in Copilot.
- `docker-compose-full-stack.yml` : Sets up a full working stack using and `amp_platform.DockerFile` and `amp_viewer.DockerFile`.
- `docker-compose.yml` : Contains the dockerised setup for PostgreSQL and PGAdmin. Used for local development.
- `Makefile` : Automation tool for the repo
- `manage_report_viewer.py` : Root access for Viewer Django app
- `manage.py` : Root access for AMP Django app
- `package-lock.json` : Locked dependencies for NPM
- `package.json` : Tracks developer and production dependencies for Javascript
- `prepare_local_db.py` : Script for downloading the latest production data and loading into the local Docker postgres instance
- `pytest_report_viewer.ini` : Pytest settings for viewer unit tests
- `pytest.ini` : Pytest settings for AMP unit tests
- `README.md` : Documentation for the repo
- `requirements_for_test.txt` : Tracks developer dependencies for Python
- `requirements.in` : Tracks production dependencies for Python
- `requirements.txt` : Derived from requirements.in by pip-compile.
