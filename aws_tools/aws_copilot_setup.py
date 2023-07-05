import argparse
import os
import subprocess
import time

import boto3
from django.core.management.utils import get_random_secret_key
from aws_secrets import get_notify_secret
from import_json import import_json_data

start = time.time()

parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument("-b", "--build-direction", help="build direction - up or down")

args = parser.parse_args()
config = vars(args)

SETTINGS = import_json_data()
SECRET_KEY = get_random_secret_key()
NOTIFY_SECRETS = get_notify_secret()
NOTIFY_API_KEY = NOTIFY_SECRETS["EMAIL_NOTIFY_API_KEY"]
EMAIL_NOTIFY_BASIC_TEMPLATE = NOTIFY_SECRETS["EMAIL_NOTIFY_BASIC_TEMPLATE"]


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{SETTINGS["copilot_app_name"]}-{SETTINGS["copilot_env_name"]}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if filtered_buckets is None:
        raise Exception("No bucket found")

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
        f"""copilot app init {SETTINGS["copilot_app_name"]} --domain {SETTINGS["copilot-domain"]}"""
    )
    os.system(f"""copilot env init --name {SETTINGS["copilot_env_name"]} --profile mfa --region eu-west-2 --default-config""")
    os.system(f"""copilot env deploy --name {SETTINGS["copilot_env_name"]}""")
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
    os.system(f"""copilot svc deploy --name viewer-svc --env {SETTINGS["copilot_env_name"]}""")
    os.system(f"""copilot svc deploy --name amp-svc --env {SETTINGS["copilot_env_name"]}""")
    os.system(
        """copilot svc exec """
        f"""-a {SETTINGS["copilot_app_name"]} """
        f"""-e {SETTINGS["copilot_env_name"]} """
        """-n amp-svc """
        """--command "python aws_tools/aws_reset_db.py" """
    )
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
