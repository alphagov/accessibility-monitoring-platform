# Generated by Django 4.1.7 on 2023-04-12 09:12

from django.db import migrations


def populate_case_contact_notes(apps, schema_editor):  # pylint: disable=unused-argument
    """Populate contact_notes in cases"""
    # pylint: disable=invalid-name
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.all():
        contacts = case.contact_set.all()
        if len(contacts) == 1:
            contact_notes = contacts[0].notes
        else:
            contact_notes: str = ""
            for count, contact in enumerate(contacts, start=1):
                if contact.notes:
                    if contact_notes:
                        contact_notes += "\n\n"
                    contact_notes += f"Contact {count}:\n\n{contact.notes}"
        case.contact_notes = contact_notes
        case.save()


def remove_case_contact_notes(apps, schema_editor):  # pylint: disable=unused-argument
    """Delete all case events"""
    # pylint: disable=invalid-name
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.exclude(contact_notes=""):
        case.contact_notes = ""
        case.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0051_case_contact_notes"),
    ]

    operations = [
        migrations.RunPython(
            populate_case_contact_notes, reverse_code=remove_case_contact_notes
        )
    ]
