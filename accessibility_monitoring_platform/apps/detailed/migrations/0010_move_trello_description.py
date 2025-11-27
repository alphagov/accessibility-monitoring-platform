# Update creation datetime of Trello descriptions to put them at the beginning of customer notes

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.db import migrations

TRELLO_DESCRIPTION_LABEL: str = "Description imported from Trello"
TRELLO_DESCRIPTION_TIME: datetime = datetime(1970, 1, 1, tzinfo=timezone.utc)


def move_trello_description(apps, schema_editor):
    DetailedCaseHistory = apps.get_model("detailed", "DetailedCaseHistory")
    with patch("django.utils.timezone.now", Mock(return_value=TRELLO_DESCRIPTION_TIME)):
        for detailed_case_history in DetailedCaseHistory.objects.filter(
            label=TRELLO_DESCRIPTION_LABEL
        ):
            DetailedCaseHistory.objects.create(
                detailed_case=detailed_case_history.detailed_case,
                event_type="note",
                value=detailed_case_history.value,
                label=detailed_case_history.label,
                created_by=detailed_case_history.created_by,
            )
            detailed_case_history.delete()


def reverse_code(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("detailed", "0009_alter_detailedcasehistory_detailed_case_status"),
    ]

    operations = [
        migrations.RunPython(move_trello_description, reverse_code=reverse_code),
    ]
