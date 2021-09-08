""" integration tests - download_s3_object - Function for downloading S3 object"""

import boto3
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID_S3_STORE"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY_S3_STORE"),
    region_name=os.getenv("AWS_DEFAULT_REGION_S3_STORE"),
)


def download_s3_object(s3_bucket: str, s3_path: str, local_path: str) -> None:
    """Downloads S3 object

    Args:
        s3_path (str): Path of the S3 object
        local_path (str): Path of the local path
    """
    if os.path.exists(local_path) is False:
        temp = "/".join(local_path.split("/")[:-1])
        Path(temp).mkdir(parents=True, exist_ok=True)
        s3_client.download_file(
            s3_bucket,
            s3_path,
            local_path
        )
    else:
        print(">>>> file already exists")
