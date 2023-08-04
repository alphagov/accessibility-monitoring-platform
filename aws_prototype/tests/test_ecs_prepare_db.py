import pytest

from typing import Dict

import json
from unittest.mock import patch, Mock

import boto3
from botocore.stub import Stubber

from ..ecs_prepare_db import (
    delete_db,
    create_db,
    most_recent_db_s3_path,
    download_sql_file,
    upload_db_backup,
    clean_up,
    redo_migrations,
)

TEST_POSTGRES_CREDENTIALS: Dict[str, str] = {
    "password": "PASSWORD",
    "dbname": "accessibility_monitoring_app",
    "engine": "postgres",
    "port": 5432,
    "host": "LOCALHOST",
    "username": "ADMIN",
}
TEST_POSTGRES_CREDENTIALS_STR: str = json.dumps(TEST_POSTGRES_CREDENTIALS)
EXPECTED_DELETE_COMMAND: str = (
    """PGPASSWORD=PASSWORD """
    """psql -h LOCALHOST -U ADMIN -p 5432 """
    """-c 'DROP DATABASE accessibility_monitoring_app;'"""
)
EXPECTED_CREATE_COMMAND: str = (
    """PGPASSWORD=PASSWORD """
    """psql -h LOCALHOST -U ADMIN -p 5432 """
    """-c 'CREATE DATABASE accessibility_monitoring_app;'"""
)
BUCKET_NAME: str = "bucket-name"
EXPECTED_PATH: str = "most_recent.sql"
EXPECTED_UPLOAD_COMMAND: str = (
    """PGPASSWORD=PASSWORD """
    """psql -h LOCALHOST -U ADMIN -p 5432 """
    """-d accessibility_monitoring_app < local_path"""
)


@patch("os.system")
def test_delete_db(mock_os_system):
    """Test delete_db issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        delete_db()

    mock_os_system.assert_called_once_with(EXPECTED_DELETE_COMMAND)


def test_delete_db_raises_exception():
    """Test delete_db raises exception if credentials missing."""
    with patch("aws_prototype.ecs_prepare_db.POSTGRES_CRED", ""):
        with pytest.raises(TypeError):
            delete_db()


@patch("os.system")
def test_create_db(mock_os_system):
    """Test create_db issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        create_db()

    mock_os_system.assert_called_once_with(EXPECTED_CREATE_COMMAND)


def test_create_db_raises_exception():
    """Test create_db raises exception if credentials missing."""
    with patch("aws_prototype.ecs_prepare_db.POSTGRES_CRED", ""):
        with pytest.raises(TypeError):
            create_db()


@pytest.fixture
def s3_client():
    return boto3.client("s3", region_name="eu-west-2")


@patch("aws_prototype.ecs_prepare_db.boto3.client")
def test_most_recent_db_s3_path_returns_path(mock_client, s3_client):
    """
    Test most_recent_db_s3_path returns key of most recent .sql file.
    """
    stubber: Stubber = Stubber(s3_client)
    stubber.add_response(
        method="list_objects",
        service_response={
            "Contents": [
                {
                    "Key": "earlier.sql",
                    "LastModified": "2023-07-01",
                },
                {
                    "Key": EXPECTED_PATH,
                    "LastModified": "2023-07-02",
                },
                {
                    "Key": "more_recent_non_sql",
                    "LastModified": "2023-07-03",
                },
            ]
        },
        expected_params={"Bucket": BUCKET_NAME},
    )
    stubber.activate()

    mock_client.return_value = s3_client

    assert most_recent_db_s3_path(bucket=BUCKET_NAME) == EXPECTED_PATH


@patch("aws_prototype.ecs_prepare_db.boto3.Session")
def test_download_sql_file(mock_session):
    """Test download_sql_file runs"""
    mock_client: Mock = Mock(name="mock_client")
    mock_client.download_file.return_value = {}

    mock_returned_session: Mock = Mock()
    mock_returned_session.client.return_value = mock_client
    mock_session.return_value = mock_returned_session

    download_sql_file(bucket="bucket", s3_object="s3_object", local_path="local_path")


@patch("os.system")
def test_upload_db_backup(mock_os_system):
    """Test upload_db_backup issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        upload_db_backup(local_path="local_path")

    mock_os_system.assert_called_once_with(EXPECTED_UPLOAD_COMMAND)


def test_upload_db_backup_raises_exception():
    """Test upload_db_backup raises exception if credentials missing."""
    with patch("aws_prototype.ecs_prepare_db.POSTGRES_CRED", ""):
        with pytest.raises(TypeError):
            upload_db_backup(local_path="local_path")


@patch("os.remove")
def test_clean_up(mock_os_remove):
    """Test clean_up issues expected command."""
    clean_up(local_path="local_path")

    mock_os_remove.assert_called_once_with("local_path")


@patch("os.system")
def test_redo_migrations(mock_os_system):
    """Test redo_migrations issues expected command."""
    redo_migrations()

    mock_os_system.assert_called_once_with("python ./manage.py migrate")
