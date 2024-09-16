"""
    Enable the correspondence process for those cases where
    no-contact emails have already been sent.
"""

from django.db import migrations


def enable_cores_process(apps, schema_editor):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")

    for case in Case.objects.filter(enable_correspondence_process=False).exclude(
        correspondence_notes=""
    ):
        case.enable_correspondence_process = True
        case.save()

    for case in Case.objects.filter(enable_correspondence_process=False).filter(
        no_psb_contact="yes"
    ):
        case.enable_correspondence_process = True
        case.save()

    for case in Case.objects.filter(enable_correspondence_process=False).exclude(
        no_psb_contact_notes=""
    ):
        case.enable_correspondence_process = True
        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "cases",
            "0005_rename_contact_details_complete_date_case_manage_contact_details_complete_date_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(enable_cores_process, reverse_code=reverse_code),
    ]
