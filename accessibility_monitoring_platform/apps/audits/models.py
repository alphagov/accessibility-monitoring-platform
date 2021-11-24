"""
Models - audits (called tests by the users)
"""
from typing import List, Tuple

from django.db import models
from django.urls import reverse

from ..cases.models import Case
from ..common.models import VersionModel, BOOLEAN_CHOICES, BOOLEAN_DEFAULT

SCREEN_SIZE_DEFAULT: str = "15in"
SCREEN_SIZE_CHOICES: List[Tuple[str, str]] = [
    (SCREEN_SIZE_DEFAULT, "15 inch"),
    ("13in", "13 inch"),
]
EXEMPTION_DEFAULT: str = "unknown"
EXEMPTION_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (EXEMPTION_DEFAULT, "Unknown"),
]
AUDIT_TYPE_DEFAULT: str = "initial"
AUDIT_TYPE_CHOICES: List[Tuple[str, str]] = [
    (AUDIT_TYPE_DEFAULT, "Initial"),
    ("eq-retest", "Equality body retest"),
]
PAGE_TYPE_EXTRA: str = "extra"
PAGE_TYPE_HOME: str = "home"
PAGE_TYPE_CONTACT: str = "contact"
PAGE_TYPE_STATEMENT: str = "statement"
PAGE_TYPE_PDF: str = "pdf"
PAGE_TYPE_FORM: str = "form"
PAGE_TYPE_ALL: str = "all-except-pdf"
PAGE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (PAGE_TYPE_ALL, "All pages"),
    (PAGE_TYPE_EXTRA, "Page"),
    (PAGE_TYPE_HOME, "Home page"),
    (PAGE_TYPE_CONTACT, "Contact page"),
    (PAGE_TYPE_STATEMENT, "Accessibility statement"),
    (PAGE_TYPE_PDF, "PDF"),
    (PAGE_TYPE_FORM, "A form"),
]
MANDATORY_PAGE_TYPES: List[str] = [
    PAGE_TYPE_ALL,
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
]
TEST_TYPE_MANUAL: str = "manual"
TEST_TYPE_AXE: str = "axe"
TEST_TYPE_PDF: str = "pdf"
TEST_TYPE_CHOICES: List[Tuple[str, str]] = [
    (TEST_TYPE_AXE, "Axe"),
    (TEST_TYPE_MANUAL, "Manual"),
    (TEST_TYPE_PDF, "PDF"),
]
TEST_SUB_TYPE_DEFAULT: str = "other"
TEST_SUB_TYPE_CHOICES: List[Tuple[str, str]] = [
    ("additional", "Additional"),
    ("audio-visual", "Audio and Visual"),
    ("keyboard", "Keyboard"),
    (TEST_SUB_TYPE_DEFAULT, "Other"),
    ("pdf", "PDF"),
    ("zoom", "Zoom and Reflow"),
    ("relationship", "Relationship"),
    ("navigation", "Navigation"),
    ("presentation", "Presentation"),
    ("aria", "ARIA"),
    ("timing", "Timing"),
    ("nontext", "Non-text"),
    ("language", "Language"),
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


class Audit(VersionModel):
    """
    Model for test
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="audit_case")
    is_deleted = models.BooleanField(default=False)

    # metadata page
    date_of_test = models.DateTimeField(null=True, blank=True)
    description = models.TextField(default="", blank=True)
    screen_size = models.CharField(
        max_length=20,
        choices=SCREEN_SIZE_CHOICES,
        default=SCREEN_SIZE_DEFAULT,
    )
    is_exemption = models.CharField(
        max_length=20, choices=EXEMPTION_CHOICES, default=EXEMPTION_DEFAULT
    )
    notes = models.TextField(default="", blank=True)
    type = models.CharField(
        max_length=20, choices=AUDIT_TYPE_CHOICES, default=AUDIT_TYPE_DEFAULT
    )
    audit_metadata_complete_date = models.DateField(null=True, blank=True)

    # pages page
    audit_pages_complete_date = models.DateField(null=True, blank=True)

    # manual page
    next_page = models.ForeignKey(
        "Page",
        on_delete=models.CASCADE,
        related_name="audit_next_page",
        null=True,
        blank=True,
    )
    audit_manual_complete_date = models.DateField(null=True, blank=True)

    # axe page
    audit_axe_complete_date = models.DateField(null=True, blank=True)

    # pdf page
    audit_pdf_complete_date = models.DateField(null=True, blank=True)

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
    audit_report_options_complete_date = models.DateField(null=True, blank=True)

    # Report text
    audit_report_text_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(f"#{self.id} | {self.description}")  # type: ignore

    def get_absolute_url(self):
        return reverse(
            "audits:edit-audit-metadata",
            kwargs={"pk": self.pk, "case_id": self.case.pk},
        )

    @property
    def all_pages(self):
        return self.page_audit.filter(is_deleted=False, not_found=BOOLEAN_DEFAULT).exclude(type=PAGE_TYPE_PDF)  # type: ignore

    @property
    def html_pages(self):
        return self.all_pages.exclude(type=PAGE_TYPE_ALL)  # type: ignore

    @property
    def standard_pages(self):
        return self.html_pages.exclude(type=PAGE_TYPE_EXTRA)  # type: ignore

    @property
    def extra_pages(self):
        return self.html_pages.filter(type=PAGE_TYPE_EXTRA)  # type: ignore


class Page(VersionModel):
    """
    Model for test/audit page
    """

    audit = models.ForeignKey(
        Audit, on_delete=models.CASCADE, related_name="page_audit"
    )
    is_deleted = models.BooleanField(default=False)

    type = models.CharField(
        max_length=20, choices=PAGE_TYPE_CHOICES, default=PAGE_TYPE_EXTRA
    )
    name = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    not_found = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    manual_checks_complete_date = models.DateField(null=True, blank=True)
    axe_checks_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):  # pylint: disable=invalid-str-returned
        name: str = self.name if self.name else self.get_type_display()  # type: ignore
        return name

    def get_absolute_url(self):
        return reverse(
            "audits:edit-audit-page",
            kwargs={"pk": self.audit.pk, "case_id": self.audit.case.pk},
        )


class WcagDefinition(models.Model):
    """
    Model for WCAG tests captured by the platform
    """

    type = models.CharField(
        max_length=20, choices=TEST_TYPE_CHOICES, default=TEST_TYPE_PDF
    )
    sub_type = models.CharField(
        max_length=20, choices=TEST_SUB_TYPE_CHOICES, default=TEST_SUB_TYPE_DEFAULT
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
