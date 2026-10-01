"""S3 housekeeping: Delete old database backups from S3"""

import logging
from datetime import date

from django.core.management.base import BaseCommand

from accessibility_monitoring_platform.apps.common.s3_utils import S3Wrapper

logger = logging.getLogger(__name__)

S3_KEY_PREFIX: str = "aws_aurora_backup/"
DELETE_CHUNK_SIZE: int = 600


class S3DBBackup(S3Wrapper):
    def get_s3_keys(self) -> list[str]:
        self.s3_bucket = self.s3_resource.Bucket(self.bucket_name)
        s3_keys: list[str] = []
        today: date = date.today()
        one_year_ago_key: str = (
            f"{S3_KEY_PREFIX}{today.year - 1}{today.month:02d}{today.day:02d}"
        )
        for obj in self.s3_bucket.objects.filter(Prefix=S3_KEY_PREFIX):
            if obj.key > one_year_ago_key:
                break
            s3_keys.append(obj.key)
        return s3_keys

    def delete_keys(self, dry_run: bool, s3_keys: list[str]) -> None:
        """Delete objects in batches"""
        s3_keys_chunks: list[list[str]] = [
            s3_keys[i : i + DELETE_CHUNK_SIZE]
            for i in range(0, len(s3_keys), DELETE_CHUNK_SIZE)
        ]
        for s3_keys_chunk in s3_keys_chunks:
            if len(s3_keys_chunk) > 1:
                logger.info(
                    "Deleting from %s to %s", s3_keys_chunk[0], s3_keys_chunk[-1]
                )
            if dry_run is False:
                self.s3_bucket.delete_objects(
                    Delete={"Objects": [{"Key": s3_key} for s3_key in s3_keys_chunk]}
                )


def rm_old_db_backups(dry_run: bool = False):
    """Delete database backups over one year old from S3"""
    s3_db_backup: S3DBBackup = S3DBBackup()
    s3_keys: list[str] = s3_db_backup.get_s3_keys()

    logger.info("Processing bucket: %s", s3_db_backup.bucket_name)
    logger.info("%d S3 keys found", len(s3_keys))
    if len(s3_keys) > 0:
        logger.info("First key: %s", s3_keys[0])
        logger.info("Last key: %s", s3_keys[-1])

    s3_db_backup.delete_keys(dry_run=dry_run, s3_keys=s3_keys)


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
