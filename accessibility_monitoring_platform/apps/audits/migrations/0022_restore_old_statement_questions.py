# Restore text to older statement questions and create new ones with the newer text

from datetime import date

from django.db import migrations

OLD_STATEMENT_QUESTIONS = {
    24: {
        "label": """Is no content listed as being out of scope that should be in another part of the accessibility statement?""",
        "success_criteria": """No content is listed as out of scope that should be in another section.""",
        "report_text": """Content is included in the out of scope section that should be listed in another part of the statement.""",
    },
    25: {
        "label": """Is there a heading for preparation of this accessibility statement?""",
        "success_criteria": """There is a heading for preparation of this accessibility statement.""",
        "report_text": """A heading for "Preparation of this accessibility statement" was not found.""",
    },
    26: {
        "label": """Is the statement preparation heading worded correctly?""",
        "success_criteria": """The heading is "preparation\"""",
        "report_text": """The heading for "Preparation of this accessibility statement" is not worded correctly.""",
    },
    27: {
        "label": """Is there a date for the statement preparation?""",
        "success_criteria": """There is a date for statement preparation.""",
        "report_text": """A statement preparation date was not included.""",
    },
    1: {
        "label": """Is there an accessibility page?""",
        "success_criteria": """An accessibility page is found on the website""",
        "report_text": """No accessibility page or statement was found on the website. You need to write and publish an accessibility statement that meets the required legal format.""",
    },
    3: {
        "label": """Is the page heading "Accessibility statement"?""",
        "success_criteria": """The title and main heading is Accessibility Statement or Accessibility Statement for [x]""",
        "report_text": """The title and main heading of the page should be "Accessibility statement" or "Accessibility statement for [name of website]".""",
    },
    43: {
        "label": """Does the scope of the accessibility page clearly cover the site being tested?""",
        "success_criteria": """There is an accessibility page or statement reachable from the site being tested, which clearly applies to the site being tested.""",
        "report_text": """An accessibility page or statement was linked to from your website but it was not clear whether your website was included in the scope of that page or statement.""",
    },
    10: {
        "label": """Does the statement cover the entire website?""",
        "success_criteria": """The statement covers the entire website, no further accessibility statements are needed.""",
        "report_text": """The accessibility statement needs to cover the entire website. Either this statement needs to be extended or an additional statement needs to be published.""",
    },
    11: {
        "label": """Is there a heading for compliance status?""",
        "success_criteria": """There is a heading for compliance status""",
        "report_text": """A heading for "Compliance status" was not found.""",
    },
    12: {
        "label": """If there is a compliance status heading, is the heading worded correctly?""",
        "success_criteria": """The heading is "Compliance status\"""",
        "report_text": """The heading for "Compliance status" is not worded correctly""",
    },
    13: {
        "label": """Is 1 of the 3 compliance status options included?""",
        "success_criteria": """A compliance status option is included""",
        "report_text": """The statement does not include the compliance status, as required in the model accessibility statement.""",
    },
    14: {
        "label": """Is the compliance status option correct?""",
        "success_criteria": """The status option matches our testing results and is worded correctly""",
        "report_text": """The compliance status does not match the results of our testing or is not using the correct wording.""",
    },
    15: {
        "label": """Is there a heading for non-accessible content?""",
        "success_criteria": """A heading for non-accessible content is included (if needed)""",
        "report_text": """A heading for "Non-accessible content" was not found.""",
    },
    16: {
        "label": """Is the non-accessible content heading worded correctly?""",
        "success_criteria": """The heading is "Non-accessible content\"""",
        "report_text": """The heading for "Non-accessible content" is not worded correctly.""",
    },
    17: {
        "label": """Are issues found from the testing listed as non-accessible content in the statement?""",
        "success_criteria": """The issues found in testing are included in the non-accessible content section.""",
        "report_text": """Known accessibility issues are not included within the 'non-accessible content' section. You need to review your accessibility statement to cover the issues found in this report and any others found during your own audit.""",
    },
    18: {
        "label": """Is non-compliant content correct and complete?""",
        "success_criteria": """Non-compliant content is correct and complete.""",
        "report_text": """The non-accessible content is not correct or complete.""",
    },
    19: {
        "label": """Is the non-compliant content clear?""",
        "success_criteria": """Non-compliant content is clear.""",
        "report_text": """The non-accessible content is not clear.""",
    },
    20: {
        "label": """Does the non-compliant content mention the WCAG criteria?""",
        "success_criteria": """The non-compliant content mentions the WCAG criteria it fails.""",
        "report_text": """The non-accessible content does not say which WCAG criteria it fails.""",
    },
    21: {
        "label": """Are all dates for fixes in the future?""",
        "success_criteria": """There are no dates in the past for fixes.""",
        "report_text": """The non-compliant content includes dates for fixes that are in the past.""",
    },
    22: {
        "label": """If disproportionate burden is claimed, is the scope of disproportionate burden content clear?""",
        "success_criteria": """The scope of disproportionate burden content is not clear.""",
        "report_text": """The content where disproportionate burden is claimed is not clear or in enough detail.""",
    },
    23: {
        "label": """If disproportionate burden is claimed, is the disproportionate burden assessment provided?""",
        "success_criteria": """The disproportionate burden assessment is provided.""",
        "report_text": """A disproportionate burden assessment must have been completed before adding a claim to your accessibility statement. You need to send evidence of the assessment to us for review.""",
    },
    28: {
        "label": """Is the statement preparation date worded correctly?""",
        "success_criteria": """The statement preparation date is worded correctly.""",
        "report_text": """A statement preparation date was included but needs to be worded correctly.""",
    },
    29: {
        "label": """Is there a date for the last review of the statement?""",
        "success_criteria": """There is a date for the last statement review or has been published in the last year.""",
        "report_text": """A statement review date was not included.""",
    },
    30: {
        "label": """Is the the last review date worded correctly?""",
        "success_criteria": """The last statement review date is worded correctly.""",
        "report_text": """A statement review date was included but needs to be worded correctly.""",
    },
    32: {
        "label": """Is there information about the method used to prepare the statement?""",
        "success_criteria": """The method used to prepare the statement is not included.""",
        "report_text": """The statement does not include the method used to prepare the statement.""",
    },
    33: {
        "label": """Is the method used to prepare the statement descriptive enough?""",
        "success_criteria": """The method used to prepare the statement is not descriptive enough.""",
        "report_text": """The method used to prepare the statement needs to be more descriptive.""",
    },
    34: {
        "label": """Is there a heading for feedback and contact information?""",
        "success_criteria": """There is a heading for feedback and contact information.""",
        "report_text": """A heading for "Feedback and contact information" was not found.""",
    },
    36: {
        "label": """Is there contact information for the organisation?""",
        "success_criteria": """There is an email address or contact form.""",
        "report_text": """There is no contact information to report accessibility issues.""",
    },
    37: {
        "label": """Is there a heading for enforcement procedure?""",
        "success_criteria": """There is a heading for enforcement procedure.""",
        "report_text": """A heading for "Enforcement procedure" is not found.""",
    },
    38: {
        "label": """Is the heading for enforcement procedure worded correctly?""",
        "success_criteria": """The heading is "Enforcement procedure".""",
        "report_text": """The heading for "Enforcement procedure" is not worded correctly.""",
    },
    39: {
        "label": """If GB: does the content mention EHRC?""",
        "success_criteria": """The content mentions EHRC as the enforcement body.""",
        "report_text": """The statement must say that EHRC are responsible for enforcing the regulations.""",
    },
    40: {
        "label": """If NI: does the content mention ECNI?""",
        "success_criteria": """The content mentions ECNI as the enforcement body.""",
        "report_text": """The statement must say that ECNI are responsible for enforcing the regulations.""",
    },
    41: {
        "label": """If GB: is there a link to EASS?""",
        "success_criteria": """There is a line about contacting EASS and this is linked.""",
        "report_text": """There must be a link to the EASS website for complaints.""",
    },
    4: {
        "label": """Is there an accessibility commitment?""",
        "success_criteria": """A commitment to make the site accessible is found""",
        "report_text": """There is no commitment to make the website accessible, as required in the model accessibility statement.""",
    },
    5: {
        "label": """Does the commitment use the correct wording?""",
        "success_criteria": """The text is: [Name of organisation] is committed to making its [website(s)/mobile application(s), as appropriate] accessible, in accordance with the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018.""",
        "report_text": """The wording of the commitment to make the website accessible is incorrect.""",
    },
    7: {
        "label": """Is the accessibility statement provided as a web page?""",
        "success_criteria": """The statement is a web page.""",
        "report_text": """Some users may have accessibility issues reading an accessibility statement that is not a standard HTML web page. It would be beneficial to publish as a web page.""",
    },
    8: {
        "label": """Is the accessibility statement prominent on the home page or on every page of the site?""",
        "success_criteria": """The statement is not properly linked.""",
        "report_text": """Your statement should be prominently placed on the homepage of the website or made available on every web page, for example in a static header or footer, as the regulations require.""",
    },
    9: {
        "label": """Is the statement complete on one page?""",
        "success_criteria": """The statement is on one page and is not split over many pages.""",
        "report_text": """The statement should be easy to read and navigate. Splitting the statement over multiple pages could mean a user cannot find the information they were looking for.""",
    },
    2: {
        "label": """Does the accessibility page include a statement, including some mandatory sections?""",
        "success_criteria": """The accessibility page includes some statement wording and sections. (If you would like them to work on the statement before testing, select "No")""",
        "report_text": """The accessibility page does not include an accessibility statement that follows the model accessibility statement template. You need to write and publish an accessibility statement that meets the required legal format.""",
    },
    6: {
        "label": """Is there a scope for the accessibility statement?""",
        "success_criteria": """The statement is clear about what it applies to.""",
        "report_text": """There is no scope included for the statement or it is not clear enough.""",
    },
    31: {
        "label": """If there is a review date, is the statement review date within the last year?""",
        "success_criteria": """The statement has not been reviewed in the last year.""",
        "report_text": """The statement has not been reviewed in the last year and is out of date.""",
    },
    35: {
        "label": """Is the feedback and contact information heading worded correctly?""",
        "success_criteria": """The heading is "Feedback and contact information\"""",
        "report_text": """The heading for "Feedback and contact information" is not worded correctly.""",
    },
    42: {
        "label": """If NI: is there a link to ECNI?""",
        "success_criteria": """There is a line about contacting ECNI and this is linked.""",
        "report_text": """There must be a link to the ECNI website for complaints.""",
    },
}
HIGHEST_OLD_STATEMENT_CHECK_ID: int = 43
QUESTIONS_UPDATE_DATE: date = date(2025, 7, 30)


def restore_old_statement_questions(apps, schema_editor):
    Audit = apps.get_model("audits", "Audit")
    StatementCheck = apps.get_model("audits", "StatementCheck")
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    recent_audits: list[Audit] = list(
        Audit.objects.filter(date_of_test__gt=QUESTIONS_UPDATE_DATE)
    )
    new_issue_number: int = StatementCheck.objects.all().count()
    for statement_check in StatementCheck.objects.filter(
        id__lte=HIGHEST_OLD_STATEMENT_CHECK_ID, date_end=None
    ):
        new_issue_number += 1
        new_statement_check = StatementCheck.objects.create(
            type=statement_check.type,
            label=statement_check.label,
            success_criteria=statement_check.success_criteria,
            report_text=statement_check.report_text,
            position=statement_check.position + 5,
            date_start=QUESTIONS_UPDATE_DATE,
            date_end=statement_check.date_end,
            issue_number=new_issue_number,
        )

        for audit in recent_audits:
            statement_check_result: StatementCheckResult = (
                StatementCheckResult.objects.get(
                    audit=audit, statement_check_id=statement_check.id
                )
            )
            statement_check_result.statement_check = new_statement_check
            statement_check_result.save()

        statement_check.date_end = QUESTIONS_UPDATE_DATE
        statement_check.label = OLD_STATEMENT_QUESTIONS[statement_check.id]["label"]
        statement_check.success_criteria = OLD_STATEMENT_QUESTIONS[statement_check.id][
            "success_criteria"
        ]
        statement_check.report_text = OLD_STATEMENT_QUESTIONS[statement_check.id][
            "report_text"
        ]
        statement_check.save()

    new_position: int = 0
    for statement_check in StatementCheck.objects.all().order_by("position"):
        new_position += 10
        statement_check.position = new_position
        statement_check.save()


def reverse_code(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0021_alter_reteststatementcheckresult_type_and_more"),
    ]

    operations = [
        migrations.RunPython(
            restore_old_statement_questions, reverse_code=reverse_code
        ),
    ]
