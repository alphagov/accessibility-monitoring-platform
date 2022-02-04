"""Function to upload file to s3"""
import logging
from typing import Union
import boto3
from botocore.exceptions import ClientError
import os


def upload_db_to_s3(file_name: str, bucket: str, object_name: Union[str, None] = None):
    """Upload a file to an S3 bucket

    Args:
        file_name: File to upload
        bucket: Bucket to upload to
        object_name: S3 object name. If not specified then file_name is used

    return:
        True if file was uploaded, else False
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID_S3_STORE"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY_S3_STORE"),
        region_name=os.getenv("AWS_DEFAULT_REGION_S3_STORE"),
    )

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
