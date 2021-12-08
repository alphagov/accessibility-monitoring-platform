"""
Models - audits (called tests by the users)
"""
from typing import List, Tuple

from django.db import models
from django.urls import reverse

from ..cases.models import Case
from ..common.models import (
    VersionModel,
    BOOLEAN_CHOICES,
    BOOLEAN_DEFAULT,
    BOOLEAN_TRUE,
)
from ..common.utils import format_date

SCREEN_SIZE_DEFAULT: str = "15in"
SCREEN_SIZE_CHOICES: List[Tuple[str, str]] = [
    (SCREEN_SIZE_DEFAULT, "15 inch"),
    ("13in", "13 inch"),
]
AUDIT_TYPE_DEFAULT: str = "initial"
AUDIT_TYPE_RETEST = "retest"
AUDIT_TYPE_CHOICES: List[Tuple[str, str]] = [
    (AUDIT_TYPE_DEFAULT, "Initial"),
    (AUDIT_TYPE_RETEST, "12 week retest"),
    ("eq-body-test", "Equality body test"),
]
PAGE_TYPE_EXTRA: str = "extra"
PAGE_TYPE_HOME: str = "home"
PAGE_TYPE_CONTACT: str = "contact"
PAGE_TYPE_STATEMENT: str = "statement"
PAGE_TYPE_PDF: str = "pdf"
PAGE_TYPE_FORM: str = "form"
PAGE_TYPE_CORONAVIRUS: str = "coronavirus"
PAGE_TYPE_ALL: str = "all-except-pdf"
PAGE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (PAGE_TYPE_ALL, "All pages"),
    (PAGE_TYPE_EXTRA, "Additional page"),
    (PAGE_TYPE_HOME, "Home page"),
    (PAGE_TYPE_CONTACT, "Contact page"),
    (PAGE_TYPE_STATEMENT, "Accessibility statement"),
    (PAGE_TYPE_CORONAVIRUS, "Coronavirus"),
    (PAGE_TYPE_PDF, "PDF"),
    (PAGE_TYPE_FORM, "Form"),
]
TEST_TYPE_MANUAL: str = "manual"
TEST_TYPE_AXE: str = "axe"
TEST_TYPE_PDF: str = "pdf"
TEST_TYPE_CHOICES: List[Tuple[str, str]] = [
    (TEST_TYPE_MANUAL, "Manual"),
    (TEST_TYPE_AXE, "Axe"),
    (TEST_TYPE_PDF, "PDF"),
]
DECLARATION_STATE_DEFAULT: str = "not-present"
DECLARATION_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    (DECLARATION_STATE_DEFAULT, "Not included"),
    ("other", "Other"),
]
SCOPE_STATE_DEFAULT: str = "not-present"
SCOPE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    (SCOPE_STATE_DEFAULT, "Not included"),
    ("incomplete", "Does not cover entire website"),
    ("other", "Other"),
]
COMPLIANCE_STATE_DEFAULT: str = "not-present"
COMPLIANCE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (COMPLIANCE_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
NON_REGULATION_STATE_DEFAULT: str = "not-present"
NON_REGULATION_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (NON_REGULATION_STATE_DEFAULT, "Not present"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
DISPROPORTIONATE_BURDEN_STATE_DEFAULT: str = "no-claim"
DISPROPORTIONATE_BURDEN_STATE_CHOICES: List[Tuple[str, str]] = [
    (DISPROPORTIONATE_BURDEN_STATE_DEFAULT, "No claim"),
    ("assessment", "Claim with assessment"),
    ("no-assessment", "Claim with no assessment"),
]
CONTENT_NOT_IN_SCOPE_STATE_DEFAULT: str = "not-present"
CONTENT_NOT_IN_SCOPE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (CONTENT_NOT_IN_SCOPE_STATE_DEFAULT, "Not present"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
PREPARATION_DATE_STATE_DEFAULT: str = "not-present"
PREPARATION_DATE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present"),
    (PREPARATION_DATE_STATE_DEFAULT, "Not included"),
    ("other", "Other (Please specify)"),
]
METHOD_STATE_DEFAULT: str = "not-present"
METHOD_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present"),
    ("incomplete", "Present but missing detail"),
    (METHOD_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
REVIEW_STATE_DEFAULT: str = "not-present"
REVIEW_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present and correct"),
    (REVIEW_STATE_DEFAULT, "Not included"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
FEEDBACK_STATE_DEFAULT: str = "not-present"
FEEDBACK_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present"),
    ("incomplete", "Present but missing detail"),
    (FEEDBACK_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
CONTACT_INFORMATION_STATE_DEFAULT: str = "not-present"
CONTACT_INFORMATION_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present"),
    ("incomplete", "Present but missing detail"),
    (CONTACT_INFORMATION_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
ENFORCEMENT_PROCEDURE_STATE_DEFAULT: str = "not-present"
ENFORCEMENT_PROCEDURE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("present", "Present"),
    (ENFORCEMENT_PROCEDURE_STATE_DEFAULT, "Not included"),
    ("other", "Other (Please specify)"),
]
ACCESS_REQUIREMENTS_STATE_DEFAULT: str = "req-not-met"
ACCESS_REQUIREMENTS_STATE_CHOICES: List[Tuple[str, str]] = [
    ("req-met", "Meets requirements"),
    (ACCESS_REQUIREMENTS_STATE_DEFAULT, "Does not meet requirements"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
OVERALL_COMPLIANCE_STATE_DEFAULT: str = "not-compliant"
OVERALL_COMPLIANCE_STATE_CHOICES: List[Tuple[str, str]] = [
    ("compliant", "Compliant"),
    ("partial", "Partially Compliant"),
    (OVERALL_COMPLIANCE_STATE_DEFAULT, "Not Compliant"),
    ("no-statement", "No Statement"),
]
ACCESSIBILITY_STATEMENT_STATE_DEFAULT: str = "not-found"
ACCESSIBILITY_STATEMENT_STATE_CHOICES: List[Tuple[str, str]] = [
    (
        ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
        "An accessibility statement for the website was not found.",
    ),
    (
        "found",
        "An accessibility statement for the website was found in the correct format.",
    ),
    ("found-but", "An accessibility statement for the website was found but:"),
]
REPORT_OPTIONS_NEXT_DEFAULT: str = "errors"
REPORT_OPTIONS_NEXT_CHOICES: List[Tuple[str, str]] = [
    (REPORT_OPTIONS_NEXT_DEFAULT, "Errors were found"),
    ("no-errors", "No serious errors were found"),
]

REPORT_ACCESSIBILITY_ISSUE_TEXT = {
    "accessibility_statement_not_correct_format": "It was not in the correct format",
    "accessibility_statement_not_specific_enough": "It was not specific enough",
    "accessibility_statement_missing_accessibility_issues": "Accessibility issues were found during the test that"
    " were not included in the statement",
    "accessibility_statement_missing_mandatory_wording": "Mandatory wording is missing",
    "accessibility_statement_needs_more_re_disproportionate": "We require more information covering the"
    " disproportionate burden claim",
    "accessibility_statement_needs_more_re_accessibility": "It required more information detailing the accessibility"
    " issues",
    "accessibility_statement_deadline_not_complete": "It includes a deadline of XXX for fixing XXX issues and this"
    " has not been completed",
    "accessibility_statement_deadline_not_sufficient": "It includes a deadline of XXX for fixing XXX issues and"
    " this is not sufficient",
    "accessibility_statement_out_of_date": "It is out of date and needs to be reviewed",
    "accessibility_statement_template_update": "It is a requirement that accessibility statements are accessible."
    " Some users may experience difficulties using PDF documents. It may be beneficial for users if there was a HTML"
    " version of your full accessibility statement.",
    "accessibility_statement_accessible": "In 2020 the GOV.UK sample template was updated to include an extra"
    " mandatory piece of information to outline the scope of your accessibility statement. This needs to be added to"
    " your statement.",
    "accessibility_statement_prominent": "Your statement should be prominently placed on the homepage of the website"
    " or made available on every web page, for example in a static header or footer, as per the legislative"
    " requirement.",
}
REPORT_NEXT_ISSUE_TEXT = {
    "report_next_change_statement": "They have an acceptable statement but need to change it because of the"
    " errors we found",
    "report_next_no_statement": "They don’t have a statement, or it is in the wrong format",
    "report_next_statement_not_right": "They have a statement but it is not quite right",
    "report_next_statement_matches": "Their statement matches",
    "report_next_disproportionate_burden": "Disproportionate burden",
}


class Audit(VersionModel):
    """
    Model for test
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="audit_case")
    is_deleted = models.BooleanField(default=False)

    # metadata page
    date_of_test = models.DateTimeField(null=True, blank=True)
    name = models.TextField(default="", blank=True)
    screen_size = models.CharField(
        max_length=20,
        choices=SCREEN_SIZE_CHOICES,
        default=SCREEN_SIZE_DEFAULT,
    )
    type = models.CharField(
        max_length=20, choices=AUDIT_TYPE_CHOICES, default=AUDIT_TYPE_DEFAULT
    )
    retest_of_audit = models.ForeignKey(
        "Audit",
        on_delete=models.DO_NOTHING,
        related_name="audit_retest",
        null=True,
        blank=True,
    )
    audit_metadata_complete_date = models.DateField(null=True, blank=True)

    # website test page
    audit_website_complete_date = models.DateField(null=True, blank=True)

    # test page page
    next_page = models.ForeignKey(
        "Page",
        on_delete=models.CASCADE,
        related_name="audit_next_page",
        null=True,
        blank=True,
    )

    # Accessibility statement 1
    accessibility_statement_backup_url = models.TextField(default="", blank=True)
    declaration_state = models.CharField(
        max_length=20,
        choices=DECLARATION_STATE_CHOICES,
        default=DECLARATION_STATE_DEFAULT,
    )
    declaration_notes = models.TextField(default="", blank=True)
    scope_state = models.CharField(
        max_length=20, choices=SCOPE_STATE_CHOICES, default=SCOPE_STATE_DEFAULT
    )
    scope_notes = models.TextField(default="", blank=True)
    compliance_state = models.CharField(
        max_length=20,
        choices=COMPLIANCE_STATE_CHOICES,
        default=COMPLIANCE_STATE_DEFAULT,
    )
    compliance_notes = models.TextField(default="", blank=True)
    non_regulation_state = models.CharField(
        max_length=20,
        choices=NON_REGULATION_STATE_CHOICES,
        default=NON_REGULATION_STATE_DEFAULT,
    )
    non_regulation_notes = models.TextField(default="", blank=True)
    disproportionate_burden_state = models.CharField(
        max_length=20,
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
        default=DISPROPORTIONATE_BURDEN_STATE_DEFAULT,
    )
    disproportionate_burden_notes = models.TextField(default="", blank=True)
    content_not_in_scope_state = models.CharField(
        max_length=20,
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
        default=CONTENT_NOT_IN_SCOPE_STATE_DEFAULT,
    )
    content_not_in_scope_notes = models.TextField(default="", blank=True)
    preparation_date_state = models.CharField(
        max_length=20,
        choices=PREPARATION_DATE_STATE_CHOICES,
        default=PREPARATION_DATE_STATE_DEFAULT,
    )
    preparation_date_notes = models.TextField(default="", blank=True)
    audit_statement_1_complete_date = models.DateField(null=True, blank=True)

    # Accessibility statement 2
    method_state = models.CharField(
        max_length=20, choices=METHOD_STATE_CHOICES, default=METHOD_STATE_DEFAULT
    )
    method_notes = models.TextField(default="", blank=True)
    review_state = models.CharField(
        max_length=20, choices=REVIEW_STATE_CHOICES, default=REVIEW_STATE_DEFAULT
    )
    review_notes = models.TextField(default="", blank=True)
    feedback_state = models.CharField(
        max_length=20, choices=FEEDBACK_STATE_CHOICES, default=FEEDBACK_STATE_DEFAULT
    )
    feedback_notes = models.TextField(default="", blank=True)
    contact_information_state = models.CharField(
        max_length=20,
        choices=CONTACT_INFORMATION_STATE_CHOICES,
        default=CONTACT_INFORMATION_STATE_DEFAULT,
    )
    contact_information_notes = models.TextField(default="", blank=True)
    enforcement_procedure_state = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
        default=ENFORCEMENT_PROCEDURE_STATE_DEFAULT,
    )
    enforcement_procedure_notes = models.TextField(default="", blank=True)
    access_requirements_state = models.CharField(
        max_length=20,
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
        default=ACCESS_REQUIREMENTS_STATE_DEFAULT,
    )
    access_requirements_notes = models.TextField(default="", blank=True)
    overall_compliance_state = models.CharField(
        max_length=20,
        choices=OVERALL_COMPLIANCE_STATE_CHOICES,
        default=OVERALL_COMPLIANCE_STATE_DEFAULT,
    )
    overall_compliance_notes = models.TextField(default="", blank=True)
    audit_statement_2_complete_date = models.DateField(null=True, blank=True)

    # Summary
    audit_summary_complete_date = models.DateField(null=True, blank=True)

    # Report options
    accessibility_statement_state = models.CharField(
        max_length=20,
        choices=ACCESSIBILITY_STATEMENT_STATE_CHOICES,
        default=ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
    )
    accessibility_statement_not_correct_format = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_not_specific_enough = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_missing_accessibility_issues = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_missing_mandatory_wording = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_needs_more_re_disproportionate = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_needs_more_re_accessibility = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_deadline_not_complete = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_deadline_not_sufficient = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_out_of_date = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_template_update = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_accessible = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    accessibility_statement_prominent = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    report_options_next = models.CharField(
        max_length=20,
        choices=REPORT_OPTIONS_NEXT_CHOICES,
        default=REPORT_OPTIONS_NEXT_DEFAULT,
    )
    report_next_change_statement = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    report_next_no_statement = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    report_next_statement_not_right = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    report_next_statement_matches = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    report_next_disproportionate_burden = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    audit_report_options_complete_date = models.DateField(null=True, blank=True)

    # Report text
    audit_report_text_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        if self.name:
            return str(
                f"{self.name}"
                f" | {self.get_type_display()}"  # type: ignore
                f" | {format_date(self.date_of_test)}"
            )
        return str(
            f"{self.get_type_display()}"  # type: ignore
            f" | {format_date(self.date_of_test)}"
        )

    def get_absolute_url(self):
        return reverse("audits:edit-audit-metadata", kwargs={"pk": self.pk})

    @property
    def report_accessibility_issues(self):
        return [
            value
            for key, value in REPORT_ACCESSIBILITY_ISSUE_TEXT.items()
            if getattr(self, key) == BOOLEAN_TRUE
        ]

    @property
    def every_page(self):
        return self.page_audit.filter(is_deleted=False)  # type: ignore

    @property
    def every_page_except_all(self):
        return self.every_page.exclude(page_type=PAGE_TYPE_ALL)

    @property
    def html_pages(self):
        return self.every_page_except_all.exclude(page_type=PAGE_TYPE_PDF)

    @property
    def all_page(self):
        return self.every_page.filter(page_type=PAGE_TYPE_ALL).first()

    @property
    def failed_check_results(self):
        return (
            self.checkresult_audit.filter(is_deleted=False, failed=BOOLEAN_TRUE)  # type: ignore
            .exclude(page__page_type=PAGE_TYPE_ALL)
            .order_by("wcag_definition__id")
        )


class Page(models.Model):
    """
    Model for test/audit page
    """

    audit = models.ForeignKey(
        Audit, on_delete=models.CASCADE, related_name="page_audit"
    )
    is_deleted = models.BooleanField(default=False)

    page_type = models.CharField(
        max_length=20, choices=PAGE_TYPE_CHOICES, default=PAGE_TYPE_EXTRA
    )
    name = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):  # pylint: disable=invalid-str-returned
        return self.name if self.name else self.get_page_type_display()  # type: ignore

    def get_absolute_url(self):
        return reverse("audits:edit-audit-page", kwargs={"pk": self.pk})

    @property
    def all_check_results(self):
        return self.checkresult_page.filter(is_deleted=False).order_by("wcag_definition__id")  # type: ignore

    @property
    def pdf_check_results(self):
        return self.all_check_results.filter(type=TEST_TYPE_PDF)


class WcagDefinition(models.Model):
    """
    Model for WCAG tests captured by the platform
    """

    type = models.CharField(
        max_length=20, choices=TEST_TYPE_CHOICES, default=TEST_TYPE_MANUAL
    )
    name = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        if self.description:
            return str(f"{self.name}: {self.description}")
        return self.name


class CheckResult(VersionModel):
    """
    Model for test result
    """

    audit = models.ForeignKey(
        Audit, on_delete=models.CASCADE, related_name="checkresult_audit"
    )
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="checkresult_page"
    )
    is_deleted = models.BooleanField(default=False)
    type = models.CharField(
        max_length=20, choices=TEST_TYPE_CHOICES, default=TEST_TYPE_PDF
    )
    wcag_definition = models.ForeignKey(
        WcagDefinition,
        on_delete=models.CASCADE,
        related_name="checkresult_wcagdefinition",
    )

    failed = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(f"#{self.pk} | {self.wcag_definition}")
