# Generated by Django 4.1.7 on 2023-04-13 13:31

from django.db import migrations

TYPES_AND_LABELS = [
    {
        "type": "overview",
        "label": "An accessibility was page found for the website?",
    },
    {
        "type": "overview",
        "label": "The accessibility page includes a statement?",
    },
    {
        "type": "website",
        "label": "Accessibility statement scope is included?",
    },
    {
        "type": "website",
        "label": "The section is named correctly?",
    },
    {
        "type": "website",
        "label": "Accessibility section includes commitment to making the website accessible?",
    },
    {
        "type": "website",
        "label": "The statement includes scope of statement?",
    },
    {
        "type": "website",
        "label": "The scope covers entire website?",
    },
    {
        "type": "compliance",
        "label": "Compliance status section is included?",
    },
    {
        "type": "compliance",
        "label": "Section is named correctly?",
    },
    {
        "type": "compliance",
        "label": "The compliance status given?",
    },
    {
        "type": "compliance",
        "label": "The compliance status is correct?",
    },
    {
        "type": "non-accessible",
        "label": "The non-compliance list includes all errors found in the test? (or is not required)",
    },
    {
        "type": "non-accessible",
        "label": "The non-compliance list gives enough information? (or is not required)",
    },
    {
        "type": "non-accessible",
        "label": "Disproportionate burden claim is correct? (which includes no claim)",
    },
    {
        "type": "non-accessible",
        "label": "Disproportionate burden claim has sufficient information? (or is not required)",
    },
    {
        "type": "non-accessible",
        "label": "Out-of-scope claim is correct and sufficient? (or is not required)",
    },
    {
        "type": "preparation",
        "label": "Preparation of this accessibility statement section is included?",
    },
    {
        "type": "preparation",
        "label": "Section is named correctly?",
    },
    {
        "type": "preparation",
        "label": "Includes preparation date?",
    },
    {
        "type": "preparation",
        "label": "Preparation date is less than one year old?",
    },
    {
        "type": "preparation",
        "label": "Includes review date?",
    },
    {
        "type": "preparation",
        "label": "Review date is in date?",
    },
    {
        "type": "preparation",
        "label": "Includes method to test the website?",
    },
    {
        "type": "preparation",
        "label": "Assessment method is suitable?",
    },
    {
        "type": "feedback",
        "label": "Feedback and contact information section is included ?",
    },
    {
        "type": "feedback",
        "label": "Section is named correctly?",
    },
    {
        "type": "feedback",
        "label": "Includes description of feedback approach?",
    },
    {
        "type": "feedback",
        "label": "Includes contact details of entities responsible for accessibility?",
    },
    {
        "type": "feedback",
        "label": "There is sufficient information for contact details?",
    },
    {
        "type": "enforcement",
        "label": "Enforcement procedure section is included?",
    },
    {
        "type": "enforcement",
        "label": "Section is named correctly?",
    },
    {
        "type": "enforcement",
        "label": "Includes sufficient information about enforcement procedure?",
    },
    {
        "type": "enforcement",
        "label": "Includes link to EASS or ECHR website?",
    },
    {
        "type": "other",
        "label": "Statement is a HTML page?",
    },
    {
        "type": "other",
        "label": "Statement is accessibile from the homepage?",
    },
    {
        "type": "other",
        "label": "Statement is accessible on every page?",
    },
]

STATEMENT_BASE_TEMPLATE_CONTENT_OLD: str = """As part of the regulations you must publish an accessibility statement.

{{ audit.get_accessibility_statement_state_display }}

{% for issue in audit.report_accessibility_issues %}
* {{ issue }}{% if issue == 'mandatory wording is missing' %}
{{ audit.accessibility_statement_missing_mandatory_wording_notes }}{% endif %}
{% endfor %}

More information about accessibility statements can be found at [https://www.gov.uk/guidance/accessibility-requirements-for-public-sector-websites-and-apps](https://www.gov.uk/guidance/accessibility-requirements-for-public-sector-websites-and-apps).

A sample statement can be found at [https://www.gov.uk/government/publications/sample-accessibility-statement](https://www.gov.uk/government/publications/sample-accessibility-statement)."""
STATEMENT_BASE_TEMPLATE_CONTENT_NEW: str = """As part of the regulations you must publish an accessibility statement.

{% if audit.statement_check_results %}

{% if audit.website_failed_statement_check_results or audit.compliance_failed_statement_check_results or audit.non_accessible_failed_statement_check_results or audit.preparation_failed_statement_check_results or audit.feedback_failed_statement_check_results or audit.enforcement_failed_statement_check_results or audit.other_failed_statement_check_results %}

An accessibility statement for the website was found but we found the following issues. The issues have been separated by section.

{% if audit.website_failed_statement_check_results %}
Accessibility statement section:

{% for statement_check_result in audit.website_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.compliance_failed_statement_check_results %}
Compliance status section:

{% for statement_check_result in audit.compliance_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.non_accessible_failed_statement_check_results %}
Non accessible content overview section:

{% for statement_check_result in audit.non_accessible_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.preparation_failed_statement_check_results %}
Preparation of this accessibility statement section:

{% for statement_check_result in audit.preparation_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.feedback_failed_statement_check_results %}
Feedback and contact information section:

{% for statement_check_result in audit.feedback_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.enforcement_failed_statement_check_results %}
Enforcement procedure section:

{% for statement_check_result in audit.enforcement_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% if audit.other_failed_statement_check_results %}
Other issues we found:

{% for statement_check_result in audit.other_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% endif %}

{% elif audit.overview_failed_statement_check_results %}
Issues we found:

{% for statement_check_result in audit.overview_failed_statement_check_results %}
* {{ statement_check_result.statement_check.report_text }}  
{{ statement_check_result.report_comment }}
{% endfor %}
{% else %}
EVERYTHING IS FINE, NOTHING TO SEE HERE, MOVE ALONG.
{% endif %}

{% else %}
{{ audit.get_accessibility_statement_state_display }}

{% for issue in audit.report_accessibility_issues %}
* {{ issue }}{% if issue == 'mandatory wording is missing' %}
{{ audit.accessibility_statement_missing_mandatory_wording_notes }}{% endif %}
{% endfor %}

More information about accessibility statements can be found at [https://www.gov.uk/guidance/accessibility-requirements-for-public-sector-websites-and-apps](https://www.gov.uk/guidance/accessibility-requirements-for-public-sector-websites-and-apps).

A sample statement can be found at [https://www.gov.uk/government/publications/sample-accessibility-statement](https://www.gov.uk/government/publications/sample-accessibility-statement).
{% endif %}
"""


def populate_statement_checks(apps, schema_editor):  # pylint: disable=unused-argument
    """Populate statement checks and update base template"""
    # pylint: disable=invalid-name
    StatementCheck = apps.get_model("audits", "StatementCheck")
    for count, type_and_label in enumerate(TYPES_AND_LABELS, start=1):
        StatementCheck.objects.create(
            type=type_and_label["type"],
            label=type_and_label["label"],
            success_criteria=f"This is where success criteria will go {count}",
            report_text=f"This is where the report text will go {count}",
            position=count,
        )
    BaseTemplate = apps.get_model("reports", "BaseTemplate")
    statement_base_template = BaseTemplate.objects.get(
        name="Your accessibility statement"
    )
    statement_base_template.content = STATEMENT_BASE_TEMPLATE_CONTENT_NEW
    statement_base_template.save()


def remove_statement_checks(apps, schema_editor):  # pylint: disable=unused-argument
    """Delete all statement checks undo change to base template"""
    # pylint: disable=invalid-name
    StatementCheck = apps.get_model("audits", "StatementCheck")
    for statement_check in StatementCheck.objects.all():
        statement_check.delete()
    BaseTemplate = apps.get_model("reports", "BaseTemplate")
    statement_base_template = BaseTemplate.objects.get(
        name="Your accessibility statement"
    )
    statement_base_template.content = STATEMENT_BASE_TEMPLATE_CONTENT_OLD
    statement_base_template.save()


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0025_statementcheck_statementcheckresult"),
    ]

    operations = [
        migrations.RunPython(
            populate_statement_checks, reverse_code=remove_statement_checks
        )
    ]
