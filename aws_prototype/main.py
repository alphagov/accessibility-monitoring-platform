"""main - main function for deploy feature to AWS Copilot"""
import argparse
import os
import subprocess
from typing import List, Any

import boto3
from django.core.management.utils import get_random_secret_key

from aws_secrets import get_notify_secret
from create_dummy_account import create_dummy_account

parser = argparse.ArgumentParser(description="Deploy feature branch to PaaS")

parser.add_argument(
    "-b" "--build_direction",
    dest="build_direction",
    help="Decides if it builds a branch or tears it down",
)

args = parser.parse_args()

git_branch_name: str = subprocess.check_output(
    [
        "git",
        "branch",
        "--show-current",
    ]
).decode("utf-8")

git_branch_name: str = "".join(e for e in git_branch_name if e.isalnum())[:4]

APP_NAME: str = f"app-{git_branch_name}"
ENV_NAME: str = f"env-{git_branch_name}"
SECRET_KEY: str = get_random_secret_key()
NOTIFY_SECRETS = get_notify_secret()
NOTIFY_API_KEY: str = NOTIFY_SECRETS["EMAIL_NOTIFY_API_KEY"]
EMAIL_NOTIFY_BASIC_TEMPLATE: str = NOTIFY_SECRETS["EMAIL_NOTIFY_BASIC_TEMPLATE"]
BAKCUP_DB: str = "aurora-backup-test-tb"


def switch_cp_apps():
    workspace_file = f"{os.getcwd()}/copilot/.workspace"
    lines = [f"""application: {APP_NAME}""", ""]
    with open(workspace_file, "w", encoding="UTF-8") as f:
        for line in lines:
            f.write(line)
            f.write("\n")


def does_copilot_app_already_exist(app_name: str) -> bool:
    copilot_command: List[str] = "copilot app ls".split(" ")
    output = subprocess.check_output(copilot_command).decode("utf-8")
    if app_name in output:
        return True
    return False


def does_copilot_env_already_exist(env_name: str) -> bool:
    copilot_command: List[str] = "copilot env ls".split(" ")
    output = subprocess.check_output(copilot_command).decode("utf-8")
    if env_name in output:
        return True
    return False


def get_copilot_s3_bucket() -> str:
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]

    target_bucket = f"""{APP_NAME}-{ENV_NAME}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]

    if filtered_buckets is None:
        raise Exception("No bucket found")

    if len(filtered_buckets) != 1:
        raise Exception("Multiple buckets found - script can only handle one matching bucket")

    return filtered_buckets[0]


def up():
    print(">>> Setting up AWS Copilot prototype")

    switch_cp_apps()
    app_exist: bool = does_copilot_app_already_exist(app_name=APP_NAME)

    if app_exist is False:
        print(">>> creating app")
        os.system(
            f"""copilot app init {APP_NAME} --domain proto.accessibility-monitoring.service.gov.uk"""
        )

    env_exist: bool = does_copilot_env_already_exist(env_name=ENV_NAME)
    print(">>> env_exist: ", env_exist)
    if env_exist is False:
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

    # if env_exist is False:
    #     bucket: str = get_copilot_s3_bucket()
    #     sync_command = f"aws s3 sync s3://{BAKCUP_DB}/ s3://{bucket}/"
    #     os.system(sync_command)
    #     command = "python aws_prototype/ecs_prepare_db.py"
    #     copilot_exec_cmd = f"""copilot svc exec -a {APP_NAME} -e {ENV_NAME} -n amp-svc --command "{command}" """
    #     os.system(copilot_exec_cmd)

    #     # Make dummy account
    #     create_dummy_account(
    #         app_name=APP_NAME,
    #         env_name=ENV_NAME,
    #     )


def down():
    print(">>> Breaking down Copilot prototype")
    bucket: str = get_copilot_s3_bucket()
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket)
    bucket.objects.all().delete()
    os.system("copilot app delete --yes")


if __name__ == "__main__":
    if args.build_direction == "up":
        up()
    elif args.build_direction == "down":
        down()
    else:
        raise Exception("Build direction needs to be up or down")
