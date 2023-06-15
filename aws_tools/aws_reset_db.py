import json
import os

POSTGRES_CRED = os.getenv("DB_SECRET")
json_acceptable_string: str = POSTGRES_CRED.replace("'", "\"")
db_secrets_dict = json.loads(json_acceptable_string)


def delete_db() -> None:
    if POSTGRES_CRED is None:
        raise TypeError("DB_SECRET is None")

    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "psql "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f"-c 'DROP DATABASE {db_secrets_dict['dbname']};'"
    )
    os.system(psql_command)


def create_db() -> None:
    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "psql "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f"-c 'CREATE DATABASE {db_secrets_dict['dbname']};'"
    )
    os.system(psql_command)


if __name__ == "__main__":
    if POSTGRES_CRED is None:
        raise TypeError("DB_SECRET is None")
    delete_db()
    create_db()
