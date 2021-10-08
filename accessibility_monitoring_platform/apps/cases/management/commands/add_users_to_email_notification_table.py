from ....notifications.models import NotificationsSettings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            if not NotificationsSettings.objects.filter(user=user):
                NotificationsSettings(user=user).save()
