import argparse
import os
import subprocess
import time

import boto3
from django.core.management.utils import get_random_secret_key
from aws_secrets import get_notify_secret
# Opted to get the secrets from AWS secrets manager instead of storing them locally
# from dotenv import load_dotenv

# load_dotenv()

start = time.time()

parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument("-b", "--build-direction", help="build direction - up or down", required=True)
parser.add_argument("-e", "--environment", help="environment to work in - test or prod", required=True)
parser.add_argument("-s", "--service", help="which service - platform or viewer or all", required=True)

args = parser.parse_args()
config = vars(args)

SETTINGS = {
    "copilot_app_name": "amp-app",
    "copilot_env_name": "test-env",
}
AWS_TAGS_GLOBAL = {
    "Product": "Accessibility Monitoring Platform",
    "Owner": "a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk",
    "Source": "https://github.com/alphagov/accessibility-monitoring-platform"
}
# if setting up an env other than test or prod, add an option here and call the script with "--environment [your-env-name]"
AWS_TAGS_ENV = {
    "test": {"Environment": "Testing"},
    "prod": {"Environment": "Production"}
}
AWS_TAGS_SRV = {
    "platform": {"System": "Auditing Platform"},
    "viewer": {"System": "Report Viewer"}
}

SECRET_KEY = get_random_secret_key()

notify_secrets = get_notify_secret()
# NOTIFY_API_KEY = os.getenv("NOTIFY_API_KEY")
NOTIFY_API_KEY = notify_secrets["EMAIL_NOTIFY_API_KEY"]
# EMAIL_NOTIFY_BASIC_TEMPLATE = os.getenv("EMAIL_NOTIFY_BASIC_TEMPLATE")
EMAIL_NOTIFY_BASIC_TEMPLATE = notify_secrets["EMAIL_NOTIFY_BASIC_TEMPLATE"]


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{SETTINGS["copilot_app_name"]}-{SETTINGS["copilot_env_name"]}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if len(filtered_buckets) > 1:
        raise Exception("Multiple buckets found - script can only handle one matching bucket")
    if len(filtered_buckets) == 0:
        return "There is no bucket"

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


def convert_dict_to_string(dictionary):
    pairs = []
    for key, value in dictionary.items():
        pair = f'"{key}"="{value}"'
        pairs.append(pair)
    return ','.join(pairs)


def setup() -> None:
    print(">>> Setting up new " + SETTINGS['copilot_env_name'] + " environment")
    os.system("copilot app init amp-app --domain aws.accessibility-monitoring.service.gov.uk --resource-tags " + convert_dict_to_string(AWS_TAGS_GLOBAL))
    os.system("copilot env init --name " + SETTINGS['copilot_env_name'] + " --profile mfa --region eu-west-2 --default-config")
    os.system("copilot env deploy --name " + SETTINGS['copilot_env_name'])
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
    if config["service"] == "viewer" or config["service"] == "all":
        os.system("copilot svc init --name viewer-svc --svc-type \"Load Balanced Web Service\"")
        os.system("copilot svc deploy --name viewer-svc --env " + SETTINGS['copilot_env_name'] + " --resource-tags "  + convert_dict_to_string(AWS_TAGS_ENV[environment]))

    if config["service"] == "platform" or config["service"] == "all":
        os.system("copilot svc init --name amp-svc --svc-type \"Load Balanced Web Service\"")
        os.system("copilot svc deploy --name amp-svc --env " + SETTINGS['copilot_env_name'] + " --resource-tags "  + convert_dict_to_string(AWS_TAGS_ENV[environment]))
    
    os.system("""copilot svc exec -a amp-app -e """ + SETTINGS['copilot_env_name'] + """ -n amp-svc --command "python aws_tools/aws_reset_db.py" """)
    os.system("python aws_tools/restore_db_aws.py")
    os.system("python aws_tools/transfer_s3_contents.py")
    end = time.time()
    print(f"Process took {end - start} seconds")


def breakdown() -> None:
    # Process to be coded:
    # delete specified service(s)
    # if no services remain, remove the bucket
    # if no services remain, delete the environment

    bucket = get_copilot_s3_bucket()
    if (bucket != "There is no bucket"):
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

    if NOTIFY_API_KEY is None:
        raise Exception("Missing NOTIFY_API_KEY in .env file")

    if EMAIL_NOTIFY_BASIC_TEMPLATE is None:
        raise Exception("Missing EMAIL_NOTIFY_BASIC_TEMPLATE in .env file")

    environment = config["environment"]
    SETTINGS["copilot_env_name"] = environment + "-env"

    if config["build_direction"] == "up":
        setup()
    elif config["build_direction"] == "down":
        breakdown()
    else:
        raise Exception("--build-direction needs to be either up or down")
