"""Restore email templates from backup files in code base"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import EmailTemplate

PATH_TO_EMAILS_DIRECTORY: str = (
    "accessibility_monitoring_platform/apps/common/templates/common/emails/backup/"
)


class Command(BaseCommand):
    """Django command to restore email templates"""

    def handle(self, *args, **options):
        """
        Read email templates on database and replace template with that on backup file
        """
        for email_template in EmailTemplate.objects.all():
            file_path: str = (
                f"{PATH_TO_EMAILS_DIRECTORY}{slugify(email_template.name)}.html"
            )
            try:
                backup_file = open(file_path, "r")
                email_template.template = backup_file.read()
                email_template.save()
            except OSError:
                print(f"Failed to read file: {file_path}")
