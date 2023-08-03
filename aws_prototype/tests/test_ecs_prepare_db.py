import pytest

from typing import Dict

import json
from unittest.mock import patch

import boto3
from botocore.stub import Stubber

from ..ecs_prepare_db import delete_db, create_db, most_recent_db_s3_path

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


@patch("os.system")
def test_delete_db(mock_os_system):
    """Test delete_db issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        delete_db()

    mock_os_system.assert_called_once_with(EXPECTED_DELETE_COMMAND)


@patch("os.system")
def test_create_db(mock_os_system):
    """Test create_db issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        create_db()

    mock_os_system.assert_called_once_with(EXPECTED_CREATE_COMMAND)


@pytest.fixture
def s3_client():
    return boto3.client("s3", region_name="eu-west-2")


@patch("aws_prototype.ecs_prepare_db.boto3.client")
def test_most_recent_db_s3_path_returns_path(mock_client, s3_client):
    """Test get_notify_secret returns secret."""
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
                    "Key": "recent.sql",
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

    assert most_recent_db_s3_path(bucket=BUCKET_NAME) == "recent.sql"
