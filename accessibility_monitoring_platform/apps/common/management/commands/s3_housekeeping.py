"""S3 housekeeping: Delete old database backups from S3"""

import logging
from datetime import date

from django.core.management.base import BaseCommand

from accessibility_monitoring_platform.apps.common.s3_utils import S3Wrapper

logger = logging.getLogger(__name__)

S3_KEY_PREFIX: str = "aws_aurora_backup/"
FIRST_BACKUP_YEAR: int = 2023


class S3DBBackup(S3Wrapper):
    def get_s3_keys(self) -> list[str]:
        bucket = self.s3_resource.Bucket(self.bucket_name)
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
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)


def rm_old_db_backups(dry_run: bool = False):
    """Delete database backups over one year old from S3"""
    s3_db_backup: S3DBBackup = S3DBBackup()
    s3_keys: list[str] = s3_db_backup.get_s3_keys()

    logger.info("%d S3 keys found", len(s3_keys))
    if len(s3_keys) > 0:
        logger.info("First key: %s", s3_keys[0])
        logger.info("Last key: %s", s3_keys[-1])

    if dry_run is False:
        for s3_key in s3_keys:
            s3_db_backup.delete_key(s3_key=s3_key)


class Command(BaseCommand):
    """Django command to perform housekeeping"""

    help = "Housekeeping: Delete old database backups from S3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Run without updates"
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        rm_old_db_backups(dry_run=dry_run)
