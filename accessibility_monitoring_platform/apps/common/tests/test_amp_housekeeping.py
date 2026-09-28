"""Test for rm_old_db_backups command"""

from datetime import date
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from ..management.commands.amp_housekeeping import S3_KEY_PREFIX, rm_old_db_backups

BUCKET_NAME: str = "bucketname"
FILE_TO_DELETE_KEY: str = f"{S3_KEY_PREFIX}20250401"
FILE_TO_KEEP_KEY: str = f"{S3_KEY_PREFIX}20250402"
FILE_BODY: bytes = b"contents"
MOCK_DATE: date = date(2026, 4, 1)


@pytest.mark.django_db
@mock_aws
def test_rm_old_db_backups():
    connection = boto3.resource("s3", region_name="us-east-1")
    bucket = connection.Bucket(BUCKET_NAME)
    bucket.create()
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket=BUCKET_NAME, Key=FILE_TO_DELETE_KEY, Body=FILE_BODY)
    s3.put_object(Bucket=BUCKET_NAME, Key=FILE_TO_KEEP_KEY, Body=FILE_BODY)
    keys: list[str] = [obj.key for obj in bucket.objects.filter(Prefix=S3_KEY_PREFIX)]

    assert keys == [FILE_TO_DELETE_KEY, FILE_TO_KEEP_KEY]

    with patch(
        "accessibility_monitoring_platform.apps.common.management.commands.amp_housekeeping.date"
    ) as mock_date:
        mock_date.today.return_value = MOCK_DATE

        rm_old_db_backups()

        keys: list[str] = [
            obj.key for obj in bucket.objects.filter(Prefix=S3_KEY_PREFIX)
        ]

        assert keys == [FILE_TO_KEEP_KEY]
