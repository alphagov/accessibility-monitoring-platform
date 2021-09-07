"""Correcting compliance fields"""
from ...models import Case
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Correcting compliance fields"""
    def handle(self, *args, **options):
        for item in Case.objects.all():
            if item.accessibility_statement_state_final == "yes":
                item.accessibility_statement_state_final = "compliant"
            if item.accessibility_statement_state_final == "no":
                item.accessibility_statement_state_final = "not-compliant"

            if item.recommendation_for_enforcement == "no_further_action":
                item.recommendation_for_enforcement = "no-further-action"

            item.save()
