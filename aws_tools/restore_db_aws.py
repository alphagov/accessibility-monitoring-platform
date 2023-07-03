import argparse
import boto3
import os
import sys
import subprocess
# from aws_copilot_setup import check_if_logged_into_cf  <-- also imports command line arg requirements

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy_feature_to_paas.app.copy_db import CopyDB


parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-e", "--environment", help="environment to work in - test or prod", required=True)
args = parser.parse_args()
config = vars(args)

settings = {
    "space_name": "monitoring-platform-production",
    "db_name": "monitoring-platform-default-db",
    "path": "./backup_for_AWS.sql",
    "s3_db_filename": "backup_for_AWS.sql",
    "copilot_app_name": "amp-app",
    "copilot_env_name": config['environment'],
    "copilot_svc_name": "amp-svc",
}

# copoied from aws_copilot_setup.py - if you import it, it also pulls the requirements for arguments on the command line. 
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

check_if_logged_into_cf()

copy_db = CopyDB(
    space_name=settings["space_name"],
    db_name=settings["db_name"],
    path=settings["path"],
)

copy_db.start()  # Downloads DB from CF

# Script below finds the Copilot S3 bucket
s3 = boto3.client("s3")
response = s3.list_buckets()
all_buckets = [x["Name"] for x in response["Buckets"]]
target_bucket = f"""{settings["copilot_app_name"]}-{settings["copilot_env_name"]}"""
filtered_buckets = [s for s in all_buckets if target_bucket in s]

if len(filtered_buckets) != 1:
    raise Exception("Multiple buckets found - script can only handle one matching bucket")

filtered_bucket = filtered_buckets[0]

# Uploads the DB from CF
response = s3.upload_file(
    settings["path"],
    filtered_bucket,
    settings["s3_db_filename"]
)
print(">>> successfully uploaded db to s3")

# Restores the DB from inside ECS
db_restore_command = f"""python aws_tools/aws_upload_db_backup.py {settings["s3_db_filename"]}"""
copilot_command = (
    """copilot svc exec """
    f"""-a {settings["copilot_app_name"]} """
    f"""-e {settings["copilot_env_name"]} """
    f"""-n {settings["copilot_svc_name"]} """
    f"""--command "{db_restore_command}" """
)

# Triggers twice in case data is missed the first time
os.system(copilot_command)
os.system(copilot_command)

# Cleanup
os.remove(settings["path"])

