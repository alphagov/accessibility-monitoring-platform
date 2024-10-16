""" Prepare Local DB - Downloads the latest db backup and uploads to local postgres instance """

import subprocess
from pathlib import Path
from typing import Any

import boto3

S3_BUCKET: str = "amp-aurora-backup-prod"
LOCAL_DIR_PATH: Path = Path("data", "s3_files")

if __name__ == "__main__":
    s3_client = boto3.client("s3")
    db_backups: list[Any] = []
    for key in s3_client.list_objects(Bucket=S3_BUCKET)["Contents"]:
        if "aws_aurora_backup/" in key["Key"] and "prodenv" in key["Key"]:
            db_backups.append(key)
    db_backups.sort(key=lambda x: x["LastModified"])
    file_name: str = db_backups[-1]["Key"].split("/")[-1]
    s3_path: str = db_backups[-1]["Key"]
    LOCAL_DIR_PATH.mkdir(parents=True, exist_ok=True)
    local_file_path: Path = LOCAL_DIR_PATH / file_name

    if not local_file_path.exists():
        print(f">>> downloading {s3_path}")
        s3_client.download_file(S3_BUCKET, s3_path, str(local_file_path))

    subprocess.call(
        "psql "
        + "postgres://admin:secret@localhost:5432/accessibility_monitoring_app "
        + "< "
        + str(local_file_path),
        shell=True,
    )
