"""Command to recalculate and recache statuses"""

from django.core.management.base import BaseCommand

from ...models import SimplifiedCase


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        for simplified_case in SimplifiedCase.objects.all():
            simplified_case.update_case_status()
