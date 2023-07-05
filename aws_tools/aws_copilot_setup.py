import argparse
import os
import subprocess
import time

import boto3
from django.core.management.utils import get_random_secret_key
from aws_secrets import get_notify_secret

start = time.time()

parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument("-b", "--build-direction", help="build direction - up or down")

args = parser.parse_args()
config = vars(args)

SETTINGS = {
    "copilot_app_name": "amp-app-r",
    "copilot_env_name": "prod-env",
}

SECRET_KEY = get_random_secret_key()

notify_secrets = get_notify_secret()
NOTIFY_API_KEY = notify_secrets["EMAIL_NOTIFY_API_KEY"]
EMAIL_NOTIFY_BASIC_TEMPLATE = notify_secrets["EMAIL_NOTIFY_BASIC_TEMPLATE"]


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{SETTINGS["copilot_app_name"]}-{SETTINGS["copilot_env_name"]}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if len(filtered_buckets) != 1:
        raise Exception("Multiple buckets found - script can only handle one matching bucket")

    return filtered_buckets[0]


def check_if_logged_into_cf() -> None:
    print(">>> Checking if logged into Cloud Foundry...")
    command: str = "cf spaces"
    process: subprocess.Popen = subprocess.Popen(
        command.split(),
        stdout=subprocess.PIPE,
    )
    output = process.communicate()
    if "FAILED" in output[0].decode("utf-8"):
        raise Exception("Not logged into Cloud Foundry. Ensure you are logged in before continuing")
    print(">>> User is logged into CF")


def setup() -> None:
    print(">>> Setting up new environment")
    os.system(
        f"""copilot app init {SETTINGS["copilot_app_name"]} --domain aws.accessibility-monitoring.service.gov.uk"""
    )
    os.system("copilot env init --name prod-env --profile mfa --region eu-west-2 --default-config")
    os.system("copilot env deploy --name prod-env")
    os.system(
        f"copilot secret init "
        "--name SECRET_KEY "
        f"--values {SETTINGS['copilot_env_name']}='{SECRET_KEY}' "
        "--overwrite"
    )
    os.system(
        f"copilot secret init "
        "--name NOTIFY_API_KEY "
        f"--values {SETTINGS['copilot_env_name']}={NOTIFY_API_KEY} "
        "--overwrite"
    )
    os.system(
        "copilot secret init "
        "--name EMAIL_NOTIFY_BASIC_TEMPLATE "
        f"--values {SETTINGS['copilot_env_name']}={EMAIL_NOTIFY_BASIC_TEMPLATE} "
        "--overwrite"
    )
    os.system("copilot svc init --name viewer-svc")
    os.system("copilot svc init --name amp-svc")
    os.system("copilot svc deploy --name viewer-svc --env prod-env")
    os.system("copilot svc deploy --name amp-svc --env prod-env")
    os.system(f"""copilot svc exec -a {SETTINGS["copilot_app_name"]} -e prod-env -n amp-svc --command "python aws_tools/aws_reset_db.py" """)
    os.system("python aws_tools/restore_db_aws.py")
    os.system("python aws_tools/transfer_s3_contents.py")
    end = time.time()
    print(f"Process took {end - start} seconds")


def breakdown() -> None:
    bucket = get_copilot_s3_bucket()
    session = boto3.Session()
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(bucket)
    all_objects = [x for x in my_bucket.objects.all()]
    total_objects = len(all_objects)
    for n, obj in enumerate(all_objects):
        my_bucket.delete_objects(
            Delete={
                "Objects": [
                    {
                        "Key": obj.key   # the_name of_your_file
                    }
                ]
            }
        )
        if n % 10 == 0:
            print(f"{n} of {total_objects} deleted...")
    os.system("copilot app delete --yes")
    end = time.time()
    print(f"Process took {end - start} seconds")


if __name__ == "__main__":
    check_if_logged_into_cf()

    if config["build_direction"] == "up":
        setup()
    elif config["build_direction"] == "down":
        breakdown()
    else:
        raise Exception("--build-direction needs to be either up or down")
