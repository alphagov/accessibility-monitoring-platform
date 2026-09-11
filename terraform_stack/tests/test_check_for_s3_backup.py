from datetime import datetime, timezone
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from terraform_stack.terraform_deploy.check_for_s3_backup import wait_for_recent_s3_object

BUCKET = "test-backup-bucket"
PREFIX = "aws_aurora_backup/"


@mock_aws
def test_finds_recent_backup():
    s3 = boto3.client("s3", region_name="eu-west-2")

    s3.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )

    s3.put_object(
        Bucket=BUCKET,
        Key=f"{PREFIX}backup.sql",
        Body=b"fake backup contents",
    )

    result = wait_for_recent_s3_object(
        bucket=BUCKET,
        prefix=PREFIX,
        recent_within_minutes=10,
        timeout_seconds=5,
        initial_poll_seconds=1,
    )

    assert result["Key"] == f"{PREFIX}backup.sql"
    assert result["LastModified"] <= datetime.now(timezone.utc)


@mock_aws
def test_times_out_when_no_backup_found():
    s3 = boto3.client("s3", region_name="eu-west-2")

    s3.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )

    # Avoid actually sleeping during the unit test.
    with patch("terraform_stack.terraform_deploy.check_for_s3_backup.time.sleep"):
        # Make monotonic advance far enough to trigger the timeout.
        with patch(
            "terraform_stack.terraform_deploy.check_for_s3_backup.time.monotonic",
            side_effect=[0, 1, 3, 6],
        ):
            with pytest.raises(TimeoutError, match="No recent object found"):
                wait_for_recent_s3_object(
                    bucket=BUCKET,
                    prefix=PREFIX,
                    recent_within_minutes=10,
                    timeout_seconds=5,
                    initial_poll_seconds=1,
                    max_poll_seconds=2,
                )
