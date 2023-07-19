import boto3
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CRED = os.getenv("DB_SECRET")
COPILOT_APPLICATION_NAME = os.getenv("COPILOT_APPLICATION_NAME")
COPILOT_ENVIRONMENT_NAME = os.getenv("COPILOT_ENVIRONMENT_NAME")
BUCKET_NAME = os.getenv("DB_NAME")
TEMP_DB_NAME = "temp_db.sql"


def download_db_backup() -> None:
    if POSTGRES_CRED is None:
        raise TypeError("DB_SECRET is None")

    json_acceptable_string: str = POSTGRES_CRED.replace("'", "\"")
    db_secrets_dict = json.loads(json_acceptable_string)
    psql_command = (
        f"PGPASSWORD={db_secrets_dict['password']} "
        "pg_dump "
        f"-h {db_secrets_dict['host']} "
        f"-U {db_secrets_dict['username']} "
        f"-p {db_secrets_dict['port']} "
        f" {db_secrets_dict['dbname']} "
        f"> {TEMP_DB_NAME}")
    os.system(psql_command)


def upload_file(local_path, s3_path, aws_bucket) -> None:
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(
        local_path,
        aws_bucket,
        s3_path
    )


def cleanup(path: str) -> None:
    os.remove(path)


if __name__ == "__main__":
    download_db_backup()
    print(">>> downloading DB from Aurora")
    object_name = (
        "aws_aurora_backup/"
        f"""{datetime.now().strftime("%Y%m%dT%H%M")}"""
        f"""_{COPILOT_APPLICATION_NAME}"""
        f"""_{COPILOT_ENVIRONMENT_NAME}.sql"""
    )
    print(">>> Uploading file to s3 bucket")
    upload_file(
        local_path=TEMP_DB_NAME,
        s3_path=object_name,
        aws_bucket=BUCKET_NAME
    )
    print(">>> Cleaning up")
    cleanup(TEMP_DB_NAME)
