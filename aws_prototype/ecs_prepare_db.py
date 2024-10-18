"""ECS Prepare DB - Launches on ECS that prepares the Aurora for the prototype"""

import json
import os

import boto3

# from main import get_copilot_s3_bucket

POSTGRES_CRED = os.getenv("DB_SECRET", "")
TEMP_DB_NAME = "temp_db.sql"
S3_BUCKET = os.getenv("DB_NAME")
json_acceptable_string: str = POSTGRES_CRED.replace("'", '"')
db_secrets_dict = json.loads(json_acceptable_string) if json_acceptable_string else {}


def delete_db() -> None:
    if POSTGRES_CRED == "":
        raise TypeError("DB_SECRET is missing")

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
    if POSTGRES_CRED == "":
        raise TypeError("DB_SECRET is missing")

    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "psql "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f"-c 'CREATE DATABASE {db_secrets_dict['dbname']};'"
    )
    os.system(psql_command)


def most_recent_db_s3_path(bucket: str):
    s3_client = boto3.client("s3")
    db_backups: list = []
    for key in s3_client.list_objects(Bucket=bucket)["Contents"]:
        if ".sql" in key["Key"]:
            db_backups.append(key)
    db_backups.sort(key=lambda x: x["LastModified"])
    s3_path = db_backups[-1]["Key"]
    return s3_path


def download_sql_file(bucket: str, s3_object: str, local_path: str) -> None:
    session = boto3.Session()
    s3_client = session.client("s3")
    s3_client.download_file(
        bucket,
        s3_object,
        local_path,
    )
    print(">>> Downloaded DB")


def upload_db_backup(local_path: str) -> None:
    if POSTGRES_CRED == "":
        raise TypeError("DB_SECRET is missing")

    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "psql "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f"-d {db_secrets_dict['dbname']} "
        f"< {local_path}"
    )
    os.system(psql_command)


def clean_up(local_path: str) -> None:
    os.remove(local_path)
    print(">>> Deleted local DB backup")


def redo_migrations() -> None:
    os.system("python ./manage.py migrate")


def main():
    if POSTGRES_CRED == "":
        raise TypeError("DB_SECRET is missing")

    delete_db()
    create_db()
    db_s3_path: str = most_recent_db_s3_path(bucket=S3_BUCKET)
    download_sql_file(bucket=S3_BUCKET, s3_object=db_s3_path, local_path=TEMP_DB_NAME)
    upload_db_backup(local_path=TEMP_DB_NAME)
    redo_migrations()


if __name__ == "__main__":
    main()
