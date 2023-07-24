import boto3
import os
import sys
from aws_copilot_setup import check_if_logged_into_cf
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_json import import_json_data
from deploy_feature_to_paas.app.copy_db import CopyDB

parser = argparse.ArgumentParser(
    description="Just an example",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-e", "--environment", help="environment to work in - test or prod", default="test")
args = parser.parse_args()
config = vars(args)

SETTINGS = import_json_data()

check_if_logged_into_cf()

copy_db = CopyDB(
    space_name=SETTINGS["global"]["pass_space_name"],
    db_name=SETTINGS["global"]["pass_db_name"],
    path=SETTINGS["global"]["path"],
)

copy_db.start()  # Downloads DB from CF

# Script below finds the Copilot S3 bucket
s3 = boto3.client("s3")
response = s3.list_buckets()
all_buckets = [x["Name"] for x in response["Buckets"]]
target_bucket = f"""{SETTINGS["global"]["copilot_app_name"]}-{SETTINGS["environment"][config["environment"]]["copilot_env_name"]}"""
filtered_buckets = [s for s in all_buckets if target_bucket in s]

if len(filtered_buckets) != 1:
    raise Exception("Multiple buckets found - script can only handle one matching bucket")

filtered_bucket = filtered_buckets[0]

# Uploads the DB from CF
response = s3.upload_file(
    SETTINGS["global"]["path"],
    filtered_bucket,
    SETTINGS["global"]["s3_db_filename"]
)
print(">>> successfully uploaded db to s3")

# Restores the DB from inside ECS
db_restore_command = f"""python aws_tools/aws_upload_db_backup.py {SETTINGS["global"]["s3_db_filename"]}"""
copilot_command = (
    """copilot svc exec """
    f"""-a {SETTINGS["global"]["copilot_app_name"]} """
    f"""-e {SETTINGS["environment"][config["environment"]]["copilot_env_name"]} """
    f"""-n {SETTINGS["service"]["platform"]["copilot_svc_exec_name"]} """
    f"""--command "{db_restore_command}" """
)

# Triggers twice in case data is missed the first time
os.system(copilot_command)
os.system(copilot_command)

# Cleanup
os.remove(SETTINGS["global"]["path"])
