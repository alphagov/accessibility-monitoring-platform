import boto3
import os
from aws_secrets import get_s3_secret
from import_json import import_json_data
import argparse

parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-e", "--environment", help="environment to work in - test or prod", default="test")
args = parser.parse_args()
config = vars(args)

SETTINGS = import_json_data()

paas_s3_secrets = get_s3_secret()
PAAS_MIGRATION_ACCESS_KEY = paas_s3_secrets["PAAS_S3_ACCESS_KEY"]
PAAS_MIGRATION_SECRET = paas_s3_secrets["PAAS_S3_SECRET_KEY"]
PAAS_MIGRATION_REGION = paas_s3_secrets["PAAS_MIGRATION_REGION"]
PAAS_MIGRATION_BUCKET = paas_s3_secrets["PAAS_MIGRATION_BUCKET"]


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{SETTINGS["global"]["copilot_app_name"]}-{SETTINGS["environment"][config['environment']]["copilot_env_name"]}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if len(filtered_buckets) != 1:
        raise Exception("Multiple buckets found - script can only handle one matching bucket")

    return filtered_buckets[0]


def get_list_of_objs_from_paas_s3():
    session = boto3.Session(
        aws_access_key_id=PAAS_MIGRATION_ACCESS_KEY,
        aws_secret_access_key=PAAS_MIGRATION_SECRET,
        region_name=PAAS_MIGRATION_REGION
    )
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(PAAS_MIGRATION_BUCKET)
    return [x for x in my_bucket.objects.all()]


def download_file(s3_path: str) -> str:
    session = boto3.Session(
        aws_access_key_id=PAAS_MIGRATION_ACCESS_KEY,
        aws_secret_access_key=PAAS_MIGRATION_SECRET,
        region_name=PAAS_MIGRATION_REGION
    )
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(PAAS_MIGRATION_BUCKET)
    filename = s3_path.split("/")[-1]
    my_bucket.download_file(
        s3_path,
        filename
    )
    return filename


def upload_file(local_path, s3_path, aws_bucket) -> None:
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(
        local_path,
        aws_bucket,
        s3_path
    )


def cleanup(path: str) -> None:
    os.remove(path)


copilot_bucket = get_copilot_s3_bucket()
all_objects = get_list_of_objs_from_paas_s3()
number_of_objects = len(all_objects)

for n, obj in enumerate(all_objects):
    local_file = download_file(obj.key)
    upload_file(local_file, obj.key, copilot_bucket)
    cleanup(local_file)
    if n % 10 == 0:
        print(f"{n} of {number_of_objects} completed...")
