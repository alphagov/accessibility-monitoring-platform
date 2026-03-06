"""AWS S3 wrapper"""

import boto3
from django.conf import settings


class S3Wrapper:
    def __init__(self) -> None:
        self.s3_resource = boto3.resource(
            service_name="s3",
            region_name=settings.DATABASES["aws-s3-bucket"]["aws_region"],
            aws_access_key_id=settings.DATABASES["aws-s3-bucket"]["aws_access_key_id"],
            aws_secret_access_key=settings.DATABASES["aws-s3-bucket"][
                "aws_secret_access_key"
            ],
            endpoint_url=settings.S3_MOCK_ENDPOINT,
        )

        self.s3_client = boto3.client(
            "s3",
            region_name=settings.DATABASES["aws-s3-bucket"]["aws_region"],
            aws_access_key_id=settings.DATABASES["aws-s3-bucket"]["aws_access_key_id"],
            aws_secret_access_key=settings.DATABASES["aws-s3-bucket"][
                "aws_secret_access_key"
            ],
            endpoint_url=settings.S3_MOCK_ENDPOINT,
        )

        # Creates bucket for unit testing, integration testing, and local development
        if settings.DEBUG or settings.UNDER_TEST:
            response = self.s3_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in response["Buckets"]]
            if settings.DATABASES["aws-s3-bucket"]["bucket_name"] not in bucket_names:
                self.s3_client.create_bucket(
                    Bucket=settings.DATABASES["aws-s3-bucket"]["bucket_name"],
                )

        self.bucket: str = settings.DATABASES["aws-s3-bucket"]["bucket_name"]
