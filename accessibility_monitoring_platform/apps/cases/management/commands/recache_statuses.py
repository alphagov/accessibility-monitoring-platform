from ...models import Case
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        for item in Case.objects.all():
            item.save()
