import boto3
from dotenv import load_dotenv
import os


load_dotenv()

bucket = "paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID_S3_STORE"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY_S3_STORE"),
    region_name=os.getenv("AWS_DEFAULT_REGION_S3_STORE"),
)

# s3_client.delete_object(
#     Bucket=bucket,
#     Key="20211006_monitoring-platform-test_monitoring-platform-default-db.sql"
# )

for key in s3_client.list_objects(Bucket=bucket)["Contents"]:
    print(key["Key"])
