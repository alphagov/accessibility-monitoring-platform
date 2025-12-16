"""Populate EmailTemplates for detailed and mobile cases"""

from django.db import migrations

CREATED_BY_USER_ID: int = 2
DETAILED_MOBILE_CASE_TYPE: str = "det-mob"
EMAIL_TEMPLATES: list[dict[str, str]] = [
    {
        "name": "1. Initial contact - request for info",
        "template_name": "d1-initial-contact-request-info",
    }
]


def populate_email_templates(apps, schema_editor):  # pylint: disable=unused-argument
    User = apps.get_model("auth", "User")
    user = User.objects.filter(id=CREATED_BY_USER_ID).first()
    if user is not None:  # In testing environment
        EmailTemplate = apps.get_model("common", "EmailTemplate")
        for email_template in EMAIL_TEMPLATES:
            EmailTemplate.objects.create(
                name=email_template["name"],
                template_name=email_template["template_name"],
                case_type=DETAILED_MOBILE_CASE_TYPE,
                created_by=user,
                updated_by=user,
            )


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    EmailTemplate = apps.get_model("common", "EmailTemplate")
    for email_template in EmailTemplate.objects.filter(
        case_type=DETAILED_MOBILE_CASE_TYPE
    ):
        email_template.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0011_emailtemplate_case_type"),
    ]

    operations = [
        migrations.RunPython(populate_email_templates, reverse_code=reverse_code),
    ]
