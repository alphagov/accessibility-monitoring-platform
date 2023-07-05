import boto3
import os
import sys
from aws_copilot_setup import check_if_logged_into_cf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_json import import_json_data
from deploy_feature_to_paas.app.copy_db import CopyDB

SETTINGS = import_json_data()

check_if_logged_into_cf()

copy_db = CopyDB(
    space_name=SETTINGS["pass_space_name"],
    db_name=SETTINGS["pass_db_name"],
    path=SETTINGS["path"],
)

copy_db.start()  # Downloads DB from CF

# Script below finds the Copilot S3 bucket
s3 = boto3.client("s3")
response = s3.list_buckets()
all_buckets = [x["Name"] for x in response["Buckets"]]
target_bucket = f"""{SETTINGS["copilot_app_name"]}-{SETTINGS["copilot_env_name"]}"""
filtered_buckets = [s for s in all_buckets if target_bucket in s]

if len(filtered_buckets) != 1:
    raise Exception("Multiple buckets found - script can only handle one matching bucket")

filtered_bucket = filtered_buckets[0]

# Uploads the DB from CF
response = s3.upload_file(
    SETTINGS["path"],
    filtered_bucket,
    SETTINGS["s3_db_filename"]
)
print(">>> successfully uploaded db to s3")

# Restores the DB from inside ECS
db_restore_command = f"""python aws_tools/aws_upload_db_backup.py {SETTINGS["s3_db_filename"]}"""
copilot_command = (
    """copilot svc exec """
    f"""-a {SETTINGS["copilot_app_name"]} """
    f"""-e {SETTINGS["copilot_env_name"]} """
    f"""-n {SETTINGS["copilot_svc_exec_name"]} """
    f"""--command "{db_restore_command}" """
)

# Triggers twice in case data is missed the first time
os.system(copilot_command)
os.system(copilot_command)

# Cleanup
os.remove(SETTINGS["path"])
