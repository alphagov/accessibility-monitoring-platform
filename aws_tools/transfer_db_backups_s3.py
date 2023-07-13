import boto3
import os
import time

from dotenv import load_dotenv

load_dotenv()

PAAS_MIGRATION_ACCESS_KEY = os.getenv("PAAS_DB_BACKUPS_S3_ACCESS_KEY")
PAAS_MIGRATION_SECRET = os.getenv("PAAS_DB_BACKUPS_S3_SECRET_KEY")
PAAS_MIGRATION_REGION = os.getenv("PAAS_DB_BACKUPS_MIGRATION_REGION")
PAAS_MIGRATION_BUCKET = os.getenv("PAAS_DB_BACKUPS_MIGRATION_BUCKET")


def get_list_of_objs_from_paas_s3():
    session = boto3.Session(
        aws_access_key_id=PAAS_MIGRATION_ACCESS_KEY,
        aws_secret_access_key=PAAS_MIGRATION_SECRET,
        region_name=PAAS_MIGRATION_REGION
    )
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(PAAS_MIGRATION_BUCKET)
    return [x for x in my_bucket.objects.all()]


def download_file(s3_path: str) -> str:
    session = boto3.Session(
        aws_access_key_id=PAAS_MIGRATION_ACCESS_KEY,
        aws_secret_access_key=PAAS_MIGRATION_SECRET,
        region_name=PAAS_MIGRATION_REGION
    )
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(PAAS_MIGRATION_BUCKET)
    filename = s3_path.split("/")[-1]
    my_bucket.download_file(
        s3_path,
        filename
    )
    return filename


def upload_file(local_path, s3_path, aws_bucket) -> None:
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(
        local_path,
        aws_bucket,
        s3_path
    )


def cleanup(path: str) -> None:
    os.remove(path)


start = time.time()

s3_db_backup = "db-backup-amp"
all_objects = get_list_of_objs_from_paas_s3()
number_of_objects = len(all_objects)

for n, obj in enumerate(all_objects):
    print(f"{n} of {number_of_objects} completed...")
    print(f">>> Downloading {obj.key}")
    local_file = download_file(obj.key)
    print(f">>> Uploading {obj.key}")
    upload_file(local_file, obj.key, s3_db_backup)
    cleanup(local_file)

end = time.time()
print(f"Process took {end - start} seconds")
