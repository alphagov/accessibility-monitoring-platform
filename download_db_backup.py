import os
from dotenv import load_dotenv
import boto3
from pathlib import Path


if __name__ == "__main__":
    load_dotenv()
    s3_bucket = "paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914"
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID_S3_STORE"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY_S3_STORE"),
        region_name=os.getenv("AWS_DEFAULT_REGION_S3_STORE"),
    )

    file_name = ""
    s3_path = ""
    if os.getenv("DB_BACKUP"):
        print(os.getenv("DB_BACKUP"))
        filename = os.getenv("DB_BACKUP").split("/")[-1]
        s3_path = os.getenv("DB_BACKUP")
    else:
        db_backups = []
        for key in s3_client.list_objects(Bucket=s3_bucket)["Contents"]:
            if "deploy_feature_to_paas_db_back/" in key["Key"]:
                db_backups.append(key)
        db_backups.sort(key=lambda x: x["LastModified"])
        file_name = db_backups[-1]["Key"].split("/")[-1]
        s3_path = db_backups[-1]["Key"]

    Path("./data/s3_files/").mkdir(parents=True, exist_ok=True)
    local_path = f"./data/s3_files/{file_name}"

    if not os.path.isfile(local_path):
        print(f">>> downloading {s3_path}")
        s3_client.download_file(
            s3_bucket,
            s3_path,
            local_path
        )
