""" Reset staging DB - Wipes postgres DB and uploads a backup of prod db"""

import json
import os
from typing import Any

import boto3
from dotenv import load_dotenv

load_dotenv()


POSTGRES_CRED = os.getenv("DB_SECRET", "")
if POSTGRES_CRED == "":
    raise TypeError("DB_SECRET is empty")
json_acceptable_string: str = POSTGRES_CRED.replace("'", '"')
DB_SECRETS_DICT = json.loads(json_acceptable_string)


def check_if_env_is_staging() -> bool:
    copilot_app_name: str = os.getenv("COPILOT_APPLICATION_NAME", "")
    copilot_env_name: str = os.getenv("COPILOT_ENVIRONMENT_NAME", "")
    print(copilot_env_name)
    if copilot_app_name != "ampapp" or copilot_env_name != "stageenv":
        raise TypeError("App is not executing inside staging env")
    print(">>> Script running in staging environment")
    return True


def download_db_backup() -> str:
    print(">>> Downloading DB backup..")
    s3_bucket: str = "ampapp-stageenv-addonsstack-u-reportstoragebucket-hms911jlrqzu"
    s3_client = boto3.client("s3")
    db_backups: list[Any] = []
    for key in s3_client.list_objects(Bucket=s3_bucket)["Contents"]:
        if "aws_aurora_backup/" in key["Key"] and "prodenv" in key["Key"]:
            db_backups.append(key)
    db_backups.sort(key=lambda x: x["LastModified"])
    file_name: str = db_backups[-1]["Key"].split("/")[-1]
    s3_path: str = db_backups[-1]["Key"]
    local_path: str = f"./{file_name}"
    s3_client.download_file(s3_bucket, s3_path, local_path)
    print(f">>> Downloaded {file_name} from S3")
    return local_path


def wipe_existing_db() -> bool:
    print(f">>> Deleting {DB_SECRETS_DICT['dbname']}...")
    if POSTGRES_CRED is None:
        raise TypeError("DB_SECRET is None")

    psql_command = (
        f"PGPASSWORD={DB_SECRETS_DICT['password']} "
        "psql "
        f"-h {DB_SECRETS_DICT['host']} "
        f"-U {DB_SECRETS_DICT['username']} "
        f"-p {DB_SECRETS_DICT['port']} "
        f"-c 'DROP DATABASE {DB_SECRETS_DICT['dbname']};'"
    )
    os.system(psql_command)
    return True


def create_empty_db_postgres() -> bool:
    print(f">>> Creating {DB_SECRETS_DICT['dbname']}...")
    psql_command = (
        f"PGPASSWORD={DB_SECRETS_DICT['password']} "
        "psql "
        f"-h {DB_SECRETS_DICT['host']} "
        f"-U {DB_SECRETS_DICT['username']} "
        f"-p {DB_SECRETS_DICT['port']} "
        f"-c 'CREATE DATABASE {DB_SECRETS_DICT['dbname']};'"
    )
    os.system(psql_command)
    return True


def load_db_backup(db_path: str) -> bool:
    print(f">>> Loading {db_path}...")
    psql_command = (
        f"PGPASSWORD={DB_SECRETS_DICT['password']} "
        "psql "
        f"-h {DB_SECRETS_DICT['host']} "
        f"-U {DB_SECRETS_DICT['username']} "
        f"-p {DB_SECRETS_DICT['port']} "
        f"-d {DB_SECRETS_DICT['dbname']} "
        f"< {db_path}"
    )
    os.system(psql_command)
    return True


def perform_migrations() -> bool:
    os.system("python ./manage.py migrate")
    return True


def clean_up(path: str) -> None:
    os.remove(path)


if __name__ == "__main__":
    check_if_env_is_staging()
    local_path_db_backup: str = download_db_backup()
    wipe_existing_db()
    create_empty_db_postgres()
    load_db_backup(local_path_db_backup)
    perform_migrations()
    clean_up(local_path_db_backup)
