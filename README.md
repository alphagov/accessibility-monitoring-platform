# GDS Accessibility Monitoring Platform

## How to get started

To set up your local sandbox, follow the instructions below.

1. Create virtual environment
2. Activate virtual environment
3. Install pipenv
4. Run pipenv developer installation
5. Install NPM dependencies
6. Copy .env.example as .env
7. Fill in missing values in .env

For example:

```
python3 -m venv venv
source venv/bin/activate
make init
cp .env.example .env
nano .env
```

To set up the database in pgAdmin:

1. Start the pgAdmin and Postgres SQL environment
2. Run the db migrations
3. Import database backup (if needed)
4. Load dummy data (if needed)

For example:

```
docker-compose up -d
python3 manage.py migrate
db_restore db_restore_file=PATH_TO_FILE
load_data db_data=PATH_TO_FILE
```

To launch the development environment:

1. Start the pgAdmin and Postgres SQL environment
2. Start the Django server
3. Start Browsersync (in a new terminal)
4. Start Webpack (in a new terminal)
5. Start the local email server

For example

```
docker-compose up -d
make start
make sync
make webpack
make mail_server
```

To create new Architecture Design Record (ADR):

1. Ensure `adr` is installed
2. Use `adr new` if you are creating a new design record
3. Use `adr new -s` if you are superseding a previous design record

For example

```
brew install adr-tools
adr new Implement as Unix shell scripts
adr new -s 9 Use Rust for performance-critical functionality
```
