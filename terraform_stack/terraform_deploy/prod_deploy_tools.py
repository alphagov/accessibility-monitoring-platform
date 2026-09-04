"""ECS Prepare DB - Launches on ECS that prepares the database for the production environment"""

import json
import os
import subprocess
from typing import Any, TypedDict

import boto3



def delete_db(
    db_host: str,
    db_username: str,
    db_password: str,
    db_name: str,
) -> None:
    """Delete a PostgreSQL database if it exists.

    Args:
        db_host: PostgreSQL server hostname.
        db_username: Username used to connect to PostgreSQL.
        db_password: Password used to authenticate with PostgreSQL.
        db_name: Name of the database to drop.

    Raises:
        subprocess.CalledProcessError: If the `psql` command fails.
    """

    subprocess.run(
        [
            "psql",
            "-h",
            db_host,
            "-U",
            db_username,
            "-d",
            "postgres",
            "-p",
            "5432",
            "-c",
            f"DROP DATABASE IF EXISTS {db_name};",
        ],
        env={
            **os.environ,
            "PGPASSWORD": db_password,
        },
        check=True,
    )


def create_db(
    db_host: str,
    db_username: str,
    db_password: str,
    db_name: str,
) -> None:
    """Create a PostgreSQL database.

    Connects to the PostgreSQL server using the supplied credentials and
    executes a ``CREATE DATABASE`` statement.

    Args:
        db_host: Hostname of the PostgreSQL server.
        db_username: Username used to connect to PostgreSQL.
        db_password: Password used to authenticate with PostgreSQL.
        db_name: Name of the database to create.

    Raises:
        subprocess.CalledProcessError: If the ``psql`` command fails.
    """
    subprocess.run(
        [
            "psql",
            "-h",
            db_host,
            "-U",
            db_username,
            "-d",
            "postgres",
            "-p",
            "5432",
            "-c",
            f"CREATE DATABASE {db_name};",
        ],
        env={
            **os.environ,
            "PGPASSWORD": db_password,
        },
        check=True,
    )



def most_recent_db_s3_path(bucket: str) -> str:
    """Return the S3 key for the most recently modified SQL backup.

    Searches for SQL backup files within the ``aws_aurora_backup`` folder
    and returns the key of the most recently modified matching object.

    Args:
        bucket: Name of the S3 bucket containing database backups.

    Returns:
        The S3 object key for the most recently modified SQL backup,
        or an empty string if no matching backup exists.

    Raises:
        botocore.exceptions.BotoCoreError: If the AWS SDK encounters an error.
        botocore.exceptions.ClientError: If the S3 request fails.
    """
    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator("list_objects_v2")

    latest_backup = None

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix="aws_aurora_backup/",
    ):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".sql"):
                if (
                    latest_backup is None
                    or obj["LastModified"] > latest_backup["LastModified"]
                ):
                    latest_backup = obj

    if latest_backup is None:
        return ""

    return latest_backup["Key"]


def download_sql_file(
    bucket: str,
    s3_object: str,
    local_path: str,
) -> None:
    """Download a SQL backup from Amazon S3 to a local file.

    Creates an S3 client using the default AWS credentials and downloads
    the specified object to the given local file path.

    Args:
        bucket: Name of the S3 bucket containing the SQL backup.
        s3_object: Key of the SQL backup object in the S3 bucket.
        local_path: Local filesystem path where the SQL backup will be
            saved.

    Raises:
        botocore.exceptions.BotoCoreError: If the AWS SDK encounters an
            error.
        botocore.exceptions.ClientError: If the download request fails.
    """
    session = boto3.Session()
    s3_client = session.client("s3")

    s3_client.download_file(
        bucket,
        s3_object,
        local_path,
    )
    print(f"- Downloaded {s3_object}")


def load_db_backup(
    local_path: str,
    db_host: str,
    db_username: str,
    db_password: str,
    db_name: str,
) -> None:
    """Load a SQL backup file into a PostgreSQL database.

    Opens the local SQL file and pipes its contents into the ``psql``
    command-line client using the supplied connection details.

    Args:
        local_path: Path to the local SQL backup file.
        db_host: Hostname of the PostgreSQL server.
        db_username: Username used to connect to PostgreSQL.
        db_password: Password used to authenticate with PostgreSQL.
        db_name: Name of the database into which the backup will be loaded.

    Raises:
        FileNotFoundError: If the SQL backup file does not exist.
        PermissionError: If the SQL backup file cannot be opened.
        subprocess.CalledProcessError: If the ``psql`` command fails.
    """
    with open(local_path, "r", encoding="utf-8") as sql_file:
        subprocess.run(
            [
                "psql",
                "-h",
                db_host,
                "-U",
                db_username,
                "-d",
                "postgres",
                "-p",
                "5432",
                "-d",
                db_name,
            ],
            stdin=sql_file,
            env={
                **os.environ,
                "PGPASSWORD": db_password,
            },
            check=True,
        )


def clean_up(local_path: str) -> None:
    """Delete a local database backup file.

    Removes the file at the supplied local path and prints a confirmation
    message after the deletion succeeds.

    Args:
        local_path: Path to the local database backup file to delete.
    """
    os.remove(local_path)
    print("- Deleted local DB backup")


def redo_migrations() -> None:
    """Apply all pending Django database migrations.

    Runs the Django ``migrate`` management command using the project's
    local ``manage.py`` file.

    Raises:
        subprocess.CalledProcessError: If the migration command exits with
            a non-zero status.
        OSError: If the Python executable or ``manage.py`` cannot be executed.
    """
    subprocess.run(
        ["python", "./manage.py", "migrate"],
        check=True,
    )


class DatabaseCredentials(TypedDict):
    """PostgreSQL username and password values."""

    username: str
    password: str


def main() -> None:
    """Restore the latest database backup and rerun Django migrations.

    Reads the database connection details and backup bucket name from
    environment variables. It then:

    1. Deletes and recreates the configured PostgreSQL database.
    2. Finds the most recent SQL backup in the configured S3 bucket.
    3. Downloads and restores the backup.
    4. Deletes the temporary local backup file.
    5. Applies pending Django migrations.

    Required environment variables:
        DB_PASSWORD: JSON-like string containing ``username`` and ``password``.
        DB_HOST: Hostname of the PostgreSQL server.
        DB_NAME: Name of the PostgreSQL database.
        BUCKET_NAME: Name of the S3 bucket containing database backups.

    Raises:
        TypeError: If a required environment variable is missing or empty.
        json.JSONDecodeError: If ``DB_PASSWORD`` is not valid JSON.
        KeyError: If the parsed credentials do not contain ``username`` or
            ``password``.
        subprocess.CalledProcessError: If a database or migration command fails.
    """
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

    delete_db(
        db_host=db_host,
        db_name=db_name,
        db_username=db_username_password["username"],
        db_password=db_username_password["password"],
    )

    create_db(
        db_host=db_host,
        db_name=db_name,
        db_username=db_username_password["username"],
        db_password=db_username_password["password"],
    )

    db_s3_path = most_recent_db_s3_path(bucket=s3_bucket)

    download_sql_file(
        bucket=s3_bucket,
        s3_object=db_s3_path,
        local_path=temp_db_path,
    )

    load_db_backup(
        local_path=temp_db_path,
        db_host=db_host,
        db_name=db_name,
        db_username=db_username_password["username"],
        db_password=db_username_password["password"],
    )

    clean_up(local_path=temp_db_path)
    redo_migrations()


if __name__ == "__main__":
    main()