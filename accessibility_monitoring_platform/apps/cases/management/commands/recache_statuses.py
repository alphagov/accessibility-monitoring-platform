"""Command to recalculate and recache statuses"""

from django.core.management.base import BaseCommand

from ...models import Case


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        for case in Case.objects.all():
            case.status.calculate_and_save_status()
