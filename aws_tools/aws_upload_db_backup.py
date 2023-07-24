import boto3
import json
import os
import sys

S3_BUCKET = os.getenv("DB_NAME")
POSTGRES_CRED = os.getenv("DB_SECRET")
TEMP_DB_NAME = "temp_db.sql"


def check_s3_object_exists() -> None:
    if len(sys.argv) == 1:
        raise TypeError("No S3 object given in command line")

    s3_obj_path = sys.argv[1]
    if ".sql" not in s3_obj_path:
        raise TypeError("S3 object does not end in .sql. Object shoud be a postgres backup.")

    s3 = boto3.client("s3")
    if s3.head_object(Bucket=S3_BUCKET, Key=sys.argv[1]):
        print(">>> DB found in S3")


def download_sql_file() -> None:
    session = boto3.Session()
    s3_client = session.client("s3")
    s3_client.download_file(
        S3_BUCKET,
        sys.argv[1],
        TEMP_DB_NAME
    )
    print(">>> Downloaded DB")


def upload_db_backup() -> None:
    if POSTGRES_CRED is None:
        raise TypeError("DB_SECRET is None")

    json_acceptable_string: str = POSTGRES_CRED.replace("'", "\"")
    db_secrets_dict = json.loads(json_acceptable_string)
    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "psql "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f"-d {db_secrets_dict['dbname']} "
        f"< {TEMP_DB_NAME}")
    os.system(psql_command)


def clean_up() -> None:
    os.remove(TEMP_DB_NAME)
    print(">>> Deleted local DB backup")


if __name__ == "__main__":
    check_s3_object_exists()
    download_sql_file()
    upload_db_backup()
    clean_up()
