""" Prepare Local DB - Downloads the latest db backup and uploads to local postgres instance """
from typing import Any, List
import os
import boto3
from pathlib import Path


if __name__ == "__main__":
    s3_bucket: str = "amp-aurora-backup-prod"
    s3_client = boto3.client("s3")
    db_backups: List[Any] = []
    for key in s3_client.list_objects(Bucket=s3_bucket)["Contents"]:
        if (
            "aws_aurora_backup/" in key["Key"]
            and "prodenv" in key["Key"]
        ):
            db_backups.append(key)
    db_backups.sort(key=lambda x: x["LastModified"])
    file_name: str = db_backups[-1]["Key"].split("/")[-1]
    s3_path: str = db_backups[-1]["Key"]
    Path("./data/s3_files/").mkdir(parents=True, exist_ok=True)
    local_path: str = f"./data/s3_files/{file_name}"

    if not os.path.isfile(local_path):
        print(f">>> downloading {s3_path}")
        s3_client.download_file(s3_bucket, s3_path, local_path)

    os.system(
        "psql "
        "postgres://admin:secret@localhost:5432/accessibility_monitoring_app "
        "< "
        f"{local_path}"
    )
