"""Delete old database backups from S3"""

from datetime import date

from django.core.management.base import BaseCommand

from accessibility_monitoring_platform.apps.common.s3_utils import S3Wrapper

# import logging


S3_KEY_PREFIX: str = "aws_aurora_backup/"
FIRST_BACKUP_YEAR: int = 2023


class S3RemoveOldBackups(S3Wrapper):
    def get_s3_keys(self) -> list[str]:
        # bucket = self.s3_resource.Bucket(self.bucket)
        s3_keys: list[str] = []
        this_year: int = date.today().year
        for year in range(FIRST_BACKUP_YEAR, this_year):
            s3_key_prefix: str = f"{S3_KEY_PREFIX}{year}"
            # for obj in bucket.objects.filter(Prefix=s3_key_prefix):
            #     s3_keys.append(obj.key)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket, Prefix=s3_key_prefix
            )
            if "Contents" in response:
                for s3_object_metadata in response.get("Contents", []):
                    s3_keys.append(s3_object_metadata["Key"])


class Command(BaseCommand):
    """Django command to remove old database backups"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument

        s3_remove_backups: S3RemoveOldBackups = S3RemoveOldBackups()
        s3_keys: list[str] = s3_remove_backups.get_s3_keys()
        print(f"{len(s3_keys)} S3 keys found")
        if len(s3_keys) > 0:
            print(f"First key: {s3_keys[0]}")
            print(f"Last key: {s3_keys[-1]}")
