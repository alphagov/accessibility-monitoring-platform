import json
from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.stub import Stubber

from ..ecs_prepare_db import (
    clean_up,
    create_db,
    delete_db,
    download_sql_file,
    main,
    most_recent_db_s3_path,
    redo_migrations,
    upload_db_backup,
)

TEST_POSTGRES_CREDENTIALS: dict[str, str] = {
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
LOCAL_PATH: str = "local_path"
REDO_MIGRATIONS_COMMAND: str = "python ./manage.py migrate"
S3_PATH: str = "s3_path"


@pytest.fixture
def s3_client():
    """AWS client for use with stubber"""
    return boto3.client("s3", region_name="eu-west-2")


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

    download_sql_file(bucket="bucket", s3_object="s3_object", local_path=LOCAL_PATH)


@patch("os.system")
def test_upload_db_backup(mock_os_system):
    """Test upload_db_backup issues expected command."""
    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch("aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS):
        upload_db_backup(local_path=LOCAL_PATH)

    mock_os_system.assert_called_once_with(EXPECTED_UPLOAD_COMMAND)


def test_upload_db_backup_raises_exception():
    """Test upload_db_backup raises exception if credentials missing."""
    with patch("aws_prototype.ecs_prepare_db.POSTGRES_CRED", ""):
        with pytest.raises(TypeError):
            upload_db_backup(local_path=LOCAL_PATH)


@patch("os.remove")
def test_clean_up(mock_os_remove):
    """Test clean_up issues expected command."""
    clean_up(local_path=LOCAL_PATH)

    mock_os_remove.assert_called_once_with(LOCAL_PATH)


@patch("os.system")
def test_redo_migrations(mock_os_system):
    """Test redo_migrations issues expected command."""
    redo_migrations()

    mock_os_system.assert_called_once_with(REDO_MIGRATIONS_COMMAND)


@patch("aws_prototype.ecs_prepare_db.delete_db")
@patch("aws_prototype.ecs_prepare_db.create_db")
@patch("aws_prototype.ecs_prepare_db.most_recent_db_s3_path")
@patch("aws_prototype.ecs_prepare_db.download_sql_file")
@patch("aws_prototype.ecs_prepare_db.upload_db_backup")
@patch("aws_prototype.ecs_prepare_db.redo_migrations")
def test_main(
    mock_redo_migrations,
    mock_upload_db_backup,
    mock_download_sql_file,
    mock_most_recent_db_s3_path,
    mock_create_db,
    mock_delete_db,
):
    """Test main function"""
    mock_most_recent_db_s3_path.return_value = S3_PATH

    with patch(
        "aws_prototype.ecs_prepare_db.POSTGRES_CRED", TEST_POSTGRES_CREDENTIALS_STR
    ), patch(
        "aws_prototype.ecs_prepare_db.db_secrets_dict", TEST_POSTGRES_CREDENTIALS
    ), patch(
        "aws_prototype.ecs_prepare_db.S3_BUCKET", BUCKET_NAME
    ):
        main()

    mock_delete_db.assert_called_once_with()
    mock_create_db.assert_called_once_with()
    mock_most_recent_db_s3_path.assert_called_once_with(bucket=BUCKET_NAME)
    mock_download_sql_file.assert_called_once_with(
        bucket="bucket-name", s3_object="s3_path", local_path="temp_db.sql"
    )
    mock_upload_db_backup.assert_called_once_with(local_path="temp_db.sql")
    mock_redo_migrations.assert_called_once_with()
