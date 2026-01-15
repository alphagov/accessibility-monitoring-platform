"""main - main function for deploy feature to AWS Copilot"""

import argparse
import copy
import os
import shutil
import subprocess
from typing import LiteralString

import boto3
import yaml
from django.core.management.utils import get_random_secret_key

from .utils import (
    create_burner_account,
    get_aws_resource_tags,
    write_prototype_platform_metadata,
)

parser = argparse.ArgumentParser(description="Deploy feature branch to AWS")

parser.add_argument(
    "-b" "--build_direction",
    dest="build_direction",
    help="Decides if it builds a branch or tears it down",
)

parser.add_argument(
    "-fd" "--flush_database",
    dest="flush_database",
    action="store_true",
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

git_branch_prefix: str = "".join(e for e in git_branch_name if e.isalnum())[:4]
first_letter_of_profile: str = os.getenv("USER", "u")[0]
prototype_name = f"{git_branch_prefix}{first_letter_of_profile}"

AWS_ACCOUNT_ID: str = "144664177605"
APP_NAME: str = f"app{prototype_name}"
ENV_NAME: str = f"env{prototype_name}"
SECRET_KEY: str = get_random_secret_key()
NOTIFY_API_KEY: str = "NO_API_KEY"
EMAIL_NOTIFY_BASIC_TEMPLATE: str = "NO_TEMPLATE"
BACKUP_DB: str = "db-store-for-prototypes"
YAML_DIR_AMP: str = "copilot/amp-svc/manifest.yml"


def switch_cp_apps():
    workspace_file = f"{os.getcwd()}/copilot/.workspace"
    lines = [f"""application: {APP_NAME}""", ""]
    with open(workspace_file, "w", encoding="UTF-8") as f:
        for line in lines:
            f.write(line)
            f.write("\n")


def does_copilot_env_already_exist(env_name: str) -> bool:
    copilot_command: list[LiteralString] = "copilot env ls".split(" ")
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
        raise Exception(
            "Multiple buckets found - script can only handle one matching bucket"
        )

    return filtered_buckets[0]


def empty_s3_buckets() -> None:
    s3_client = boto3.client("s3")
    s3_resource = boto3.resource("s3")

    response = s3_client.list_buckets()
    all_buckets = [x["Name"] for x in response["Buckets"]]
    target_bucket = f"""{APP_NAME}-{ENV_NAME}"""
    filtered_buckets = [s for s in all_buckets if target_bucket in s]
    print(f">>> S3 buckets found: {len(filtered_buckets)}")

    for bucket in filtered_buckets:
        bucket = s3_resource.Bucket(bucket)
        bucket.objects.all().delete()
        print(f">>> Deleted all objects in {bucket.name}")

    print("Successfully wiped all buckets")


def restore_copilot_prod_settings() -> None:
    print(">>> restoring copilot settings for production")
    # Replace .workspace with prod app
    workspace_file = f"{os.getcwd()}/copilot/.workspace"
    lines = ["application: ampapp", ""]
    with open(workspace_file, "w", encoding="UTF-8") as f:
        for line in lines:
            f.write(line)
            f.write("\n")

    # Removes any prototype env settings
    to_delete = []
    preserved_folders = ["prodenv", "stageenv", "testenv", "", "addons"]
    for x in os.walk(f"{os.getcwd()}/copilot/environments/"):
        sub_folder_name = x[0].split("/")[-1]
        if sub_folder_name not in preserved_folders:
            to_delete.append(sub_folder_name)
    for folder in to_delete:
        shutil.rmtree(f"{os.getcwd()}/copilot/environments/{folder}")


def restore_prototype_env_file() -> None:
    print(">>> Restoring env in copilot")
    os.makedirs(
        os.path.dirname(f"{os.getcwd()}/copilot/environments/{ENV_NAME}/"),
        exist_ok=True,
    )
    os.system(
        f"copilot env show -n {ENV_NAME} --manifest > copilot/environments/{ENV_NAME}/manifest.yml"
    )


def prep_yaml() -> str:
    with open(YAML_DIR_AMP, encoding="UTF-8") as f:
        doc = yaml.load(f, Loader=yaml.Loader)
    backup_yaml = copy.deepcopy(doc)
    doc["variables"][
        "ALLOWED_HOSTS"
    ] = f"amp-svc.{ENV_NAME}.{APP_NAME}.proto.accessibility-monitoring.service.gov.uk"
    with open(YAML_DIR_AMP, "w", encoding="UTF-8") as f:
        yaml.dump(doc, f)
    return backup_yaml


def restore_yaml(backup_yaml: str):
    with open(YAML_DIR_AMP, "w", encoding="UTF-8") as f:
        yaml.dump(backup_yaml, f)


def flush_database():
    bucket: str = get_copilot_s3_bucket()
    sync_command = f"aws s3 sync s3://{BACKUP_DB}/ s3://{bucket}/"
    os.system(sync_command)
    command = "python aws_prototype/ecs_prepare_db.py"
    copilot_exec_cmd = f"""copilot svc exec -a {APP_NAME} -e {ENV_NAME} -n amp-svc --command "{command}" """
    os.system(copilot_exec_cmd)
    create_burner_account(app_name=APP_NAME, env_name=ENV_NAME)


def up():
    print(">>> Setting up AWS Copilot prototype")

    switch_cp_apps()

    print(">>> creating app")
    os.system(
        f"""copilot app init {APP_NAME} --domain proto.accessibility-monitoring.service.gov.uk {get_aws_resource_tags()}"""
    )

    env_exists: bool = does_copilot_env_already_exist(env_name=ENV_NAME)

    if env_exists:
        print(f">>> {ENV_NAME} already exists")
        restore_prototype_env_file()

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

    backup_yaml = prep_yaml()

    os.system(
        f"""copilot svc deploy --name amp-svc --env {ENV_NAME} {get_aws_resource_tags()}"""
    )

    restore_yaml(backup_yaml)

    os.system(
        f"""copilot svc deploy --name viewer-svc --env {ENV_NAME} {get_aws_resource_tags(system='Viewer')}"""
    )

    if args.flush_database or env_exists is False:
        flush_database()

    restore_copilot_prod_settings()


def down():
    print(">>> Breaking down Copilot prototype")
    switch_cp_apps()
    restore_prototype_env_file()
    empty_s3_buckets()
    os.system("copilot app delete --yes")
    restore_copilot_prod_settings()


if __name__ == "__main__":
    write_prototype_platform_metadata(
        git_branch_name=git_branch_name, prototype_name=prototype_name
    )
    client = boto3.client("sts")
    account_id = client.get_caller_identity()["Account"]

    if account_id != AWS_ACCOUNT_ID:
        raise Exception("AWS credentials is not running in AWS test account")

    if APP_NAME == "ampapp":
        raise Exception("The app is a protected name...")

    if ENV_NAME in ["prod", "stage", "test"]:
        raise Exception("The env is a protected name...")

    if args.build_direction == "up":
        up()
    elif args.build_direction == "down":
        down()
    elif args.build_direction == "newaccount":
        create_burner_account(app_name=APP_NAME, env_name=ENV_NAME)
    elif args.build_direction == "reload_database":
        flush_database()
    else:
        raise Exception("Build direction needs to be up or down or newaccount")
