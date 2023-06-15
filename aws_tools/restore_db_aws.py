import boto3
import os
import sys
from aws_copilot_setup import check_if_logged_into_cf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy_feature_to_paas.app.copy_db import CopyDB


settings = {
    "space_name": "monitoring-platform-production",
    "db_name": "monitoring-platform-default-db",
    "path": "./backup_for_AWS.sql",
    "s3_db_filename": "backup_for_AWS.sql",
    "copilot_app_name": "amp-app",
    "copilot_env_name": "prod-env",
    "copilot_svc_name": "amp-svc",
}

check_if_logged_into_cf()

copy_db = CopyDB(
    space_name=settings["space_name"],
    db_name=settings["db_name"],
    path=settings["path"],
)

copy_db.start()

s3 = boto3.client("s3")
response = s3.list_buckets()
all_buckets = [x["Name"] for x in response["Buckets"]]
target_bucket = f"""{settings["copilot_app_name"]}-{settings["copilot_env_name"]}"""
filtered_buckets = [s for s in all_buckets if target_bucket in s]

if len(filtered_buckets) != 1:
    raise Exception("Multiple buckets found - script can only handle one matching bucket")

filtered_bucket = filtered_buckets[0]

response = s3.upload_file(
    settings["path"],
    filtered_bucket,
    settings["s3_db_filename"]
)
print(">>> successfully uploaded db to s3")

db_restore_command = f"""python aws_tools/aws_upload_db_backup.py {settings["s3_db_filename"]}"""
copilot_command = (
    """copilot svc exec """
    f"""-a {settings["copilot_app_name"]} """
    f"""-e {settings["copilot_env_name"]} """
    f"""-n {settings["copilot_svc_name"]} """
    f"""--command "{db_restore_command}" """
)

os.system(copilot_command)
os.system(copilot_command)
os.remove(settings["path"])
