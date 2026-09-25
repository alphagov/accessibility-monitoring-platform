"""Delete old database backups from S3"""

import logging
from datetime import date

from django.core.management.base import BaseCommand

from accessibility_monitoring_platform.apps.common.s3_utils import S3Wrapper

logger = logging.getLogger(__name__)

S3_KEY_PREFIX: str = "aws_aurora_backup/"
FIRST_BACKUP_YEAR: int = 2023


class S3RemoveOldBackups(S3Wrapper):
    def get_s3_keys(self) -> list[str]:
        bucket = self.s3_resource.Bucket(self.bucket)
        s3_keys: list[str] = []
        today: date = date.today()
        one_year_ago_key: str = (
            f"{S3_KEY_PREFIX}{today.year - 1}{today.month:02d}{today.day:02d}"
        )
        for year in range(FIRST_BACKUP_YEAR, today.year):
            s3_key_prefix: str = f"{S3_KEY_PREFIX}{year}"
            for obj in bucket.objects.filter(Prefix=s3_key_prefix):
                if obj.key > one_year_ago_key:
                    break
                s3_keys.append(obj.key)
        return s3_keys

    def delete_key(self, s3_key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)


class Command(BaseCommand):
    """Django command to remove old database backups"""

    def handle(self, *args, **options):

        s3_remove_backups: S3RemoveOldBackups = S3RemoveOldBackups()
        s3_keys: list[str] = s3_remove_backups.get_s3_keys()

        logger.info("%d S3 keys found", len(s3_keys))
        if len(s3_keys) > 0:
            logger.info("First key: %s", s3_keys[0])
            logger.info("Last key: %s", s3_keys[-1])

        for s3_key in s3_keys:
            s3_remove_backups.delete_key(s3_key=s3_key)
