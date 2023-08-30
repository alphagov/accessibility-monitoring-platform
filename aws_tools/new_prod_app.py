"""main - main function for deploy feature to AWS Copilot"""
import argparse
import os
import sys

import boto3
from django.core.management.utils import get_random_secret_key

sys.path.append(".")
from aws_prototype.aws_secrets import get_notify_secret

parser = argparse.ArgumentParser(description="Deploy feature branch to PaaS")

parser.add_argument(
    "-b" "--build_direction",
    dest="build_direction",
    help="Decides if it builds a branch or tears it down",
)

args = parser.parse_args()

APP_NAME: str = "ampapp2"
ENV_NAME: str = "prodenv"
SECRET_KEY: str = get_random_secret_key()
NOTIFY_SECRETS = get_notify_secret()
NOTIFY_API_KEY: str = NOTIFY_SECRETS["EMAIL_NOTIFY_API_KEY"]
EMAIL_NOTIFY_BASIC_TEMPLATE: str = NOTIFY_SECRETS["EMAIL_NOTIFY_BASIC_TEMPLATE"]
BACKUP_DB: str = "amp-aurora-backup-prod"
URL = "accessibility-monitoring.service.gov.uk"


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{APP_NAME}-{ENV_NAME}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if filtered_buckets is None:
        raise Exception("No bucket found")

    if len(filtered_buckets) != 1:
        raise Exception(
            "Multiple buckets found - script can only handle one matching bucket"
        )

    return filtered_buckets[0]


def up():
    print(">>> Setting up AWS Copilot prototype")

    print(">>> creating app")
    os.system(f"""copilot app init {APP_NAME} --domain {URL}""")

    print(">>> creating env")
    os.system(
        f"""copilot env init --name {ENV_NAME} --profile mfa --region eu-west-2 --default-config"""
    )
    os.system(f"""copilot env deploy --name {ENV_NAME}""")
    os.system(
        f"copilot secret init "
        "--name SECRET_KEY "
        f"""--values {ENV_NAME}="{SECRET_KEY}" """
        "--overwrite"
    )
    os.system(
        f"copilot secret init "
        "--name NOTIFY_API_KEY "
        f"--values {ENV_NAME}={NOTIFY_API_KEY} "
        "--overwrite"
    )
    os.system(
        "copilot secret init "
        "--name EMAIL_NOTIFY_BASIC_TEMPLATE "
        f"--values {ENV_NAME}={EMAIL_NOTIFY_BASIC_TEMPLATE} "
        "--overwrite"
    )
    os.system("copilot svc init --name viewer-svc")
    os.system("copilot svc init --name amp-svc")

    os.system(f"""copilot svc deploy --name viewer-svc --env {ENV_NAME}""")
    os.system(f"""copilot svc deploy --name amp-svc --env {ENV_NAME}""")

    bucket: str = get_copilot_s3_bucket()
    sync_command = f"aws s3 sync s3://{BACKUP_DB}/ s3://{bucket}/"
    os.system(sync_command)
    command = "python aws_prototype/ecs_prepare_db.py"
    copilot_exec_cmd = f"""copilot svc exec -a {APP_NAME} -e {ENV_NAME} -n amp-svc --command "{command}" """
    os.system(copilot_exec_cmd)


def down():
    print(">>> Breaking down Copilot prototype")
    bucket: str = get_copilot_s3_bucket()
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket)
    bucket.objects.all().delete()
    print(">>> Deleted all objects in S3")
    os.system("copilot app delete --yes")


if __name__ == "__main__":
    client = boto3.client("sts")

    if args.build_direction == "up":
        up()
    elif args.build_direction == "down":
        down()
    else:
        raise Exception("Build direction needs to be up or down")
