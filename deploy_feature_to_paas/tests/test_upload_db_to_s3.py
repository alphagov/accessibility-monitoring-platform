from deploy_feature_to_paas.app.upload_db_to_s3 import upload_db_to_s3
from moto import mock_s3
import boto3
import os
import pytest


FILENAME = "file.txt"
BUCKET = "mybucket"
OBJECTNAME = "/objectname.txt"


@mock_s3
def test_upload_file_to_s3_successfully():
    with open(FILENAME, "w") as f:
        f.write("Create a new text file!")

    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)

    assert upload_db_to_s3(
        file_name=FILENAME,
        bucket=BUCKET,
        object_name=OBJECTNAME,
    )
    os.remove(FILENAME)

    response = client.list_objects_v2(Bucket=BUCKET)
    s3_contents = response.get("Contents", [])
    assert len(s3_contents) == 1
    assert s3_contents[0]["Key"] == OBJECTNAME


@mock_s3
def test_upload_file_to_s3_defaults_object_name():
    with open(FILENAME, "w") as f:
        f.write("Create a new text file!")

    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)

    assert upload_db_to_s3(
        file_name=FILENAME,
        bucket=BUCKET,
    )
    os.remove(FILENAME)

    response = client.list_objects_v2(Bucket=BUCKET)

    s3_contents = response.get("Contents", [])
    assert len(s3_contents) == 1
    assert s3_contents[0]["Key"] == FILENAME


@mock_s3
def test_upload_file_to_s3_raises_exception():
    with open(FILENAME, "w") as f:
        f.write("Create a new text file!")

    with pytest.raises(Exception) as exc_info:
        upload_db_to_s3(
            file_name=FILENAME,
            bucket=BUCKET,
        )

    os.remove(FILENAME)

    assert "The specified bucket does not exist" in exc_info.value.args[0]
