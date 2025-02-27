"""Backup email templates from database to code base"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import EmailTemplate

PATH_TO_EMAILS_DIRECTORY: str = (
    "accessibility_monitoring_platform/apps/common/templates/common/emails/backup/"
)


class Command(BaseCommand):
    """Django command to backup email templates"""

    def handle(self, *args, **options):
        """Read all email templates from database and save as files"""
        for email_template in EmailTemplate.objects.all():
            backup_file = open(
                f"{PATH_TO_EMAILS_DIRECTORY}{slugify(email_template.name)}.html", "w"
            )
            backup_file.write(str(email_template.template))
            backup_file.close()
