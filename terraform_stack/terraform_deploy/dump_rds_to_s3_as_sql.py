import json
import os
from datetime import datetime
import subprocess
from typing import TypedDict

import boto3
from dotenv import load_dotenv

load_dotenv()


class DatabaseCredentials(TypedDict):
    """PostgreSQL username and password values."""

    username: str
    password: str

def download_db_backup(
    db_host: str,
    db_username: str,
    db_password: str,
    db_name: str,
    temp_db_name: str,
) -> None:
    """Download a PostgreSQL database backup.

    Connects to the PostgreSQL server using the supplied credentials and
    uses ``pg_dump`` to write the database backup to the specified file.

    Args:
        db_host: Hostname of the PostgreSQL server.
        db_username: Username used to connect to PostgreSQL.
        db_password: Password used to authenticate with PostgreSQL.
        db_name: Name of the database to back up.
        temp_db_name: Path where the database backup will be written.

    Raises:
        subprocess.CalledProcessError: If the ``pg_dump`` command fails.
    """
    subprocess.run(
        [
            "pg_dump",
            "-h",
            db_host,
            "-U",
            db_username,
            "-p",
            "5432",
            "-f",
            temp_db_name,
            db_name,
        ],
        env={
            **os.environ,
            "PGPASSWORD": db_password,
        },
        check=True,
    )


def upload_file(local_path, s3_path, aws_bucket) -> None:
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(local_path, aws_bucket, s3_path)


def cleanup(path: str) -> None:
    os.remove(path)


def main() -> None:
    postgres_cred = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    s3_bucket = os.getenv("BUCKET_NAME")

    if not postgres_cred:
        raise TypeError("DB_PASSWORD is missing")
    if not db_host:
        raise TypeError("DB_HOST is missing")
    if not db_name:
        raise TypeError("DB_NAME is missing")
    if not s3_bucket:
        raise TypeError("BUCKET_NAME is missing")

    json_acceptable_string = postgres_cred.replace("'", '"')
    db_username_password: DatabaseCredentials = json.loads(json_acceptable_string)

    temp_db_path = "temp_db.sql"

    print(">>> downloading DB from RDS")
    download_db_backup(
        db_host=db_host,
        db_username=db_username_password["username"],
        db_password=db_username_password["password"],
        db_name=db_name,
        temp_db_name=temp_db_path,
    )
    object_name = (
        "aws_aurora_backup/"
        f"""{datetime.now().strftime("%Y%m%dT%H%M")}"""
        f"""_ampapp"""
        f"""_prodenv.sql"""
    )

    print(">>> Uploading file to s3 bucket")
    upload_file(local_path=temp_db_path, s3_path=object_name, aws_bucket=s3_bucket)

    print(">>> Cleaning up")
    cleanup(temp_db_path)


if __name__ == "__main__":
    main()
