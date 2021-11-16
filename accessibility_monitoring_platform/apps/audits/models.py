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
PAGE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (PAGE_TYPE_EXTRA, "Page"),
    (PAGE_TYPE_HOME, "Home page"),
    (PAGE_TYPE_CONTACT, "Contact page"),
    (PAGE_TYPE_STATEMENT, "Accessibility statement"),
    (PAGE_TYPE_PDF, "PDF"),
    (PAGE_TYPE_FORM, "A form"),
]
MANDATORY_PAGE_TYPES: List[str] = [
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

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(f"#{self.id} | {self.description}")  # type: ignore

    def get_absolute_url(self):
        return reverse(
            "audits:edit-audit-metadata",
            kwargs={"pk": self.pk, "case_id": self.case.pk},
        )


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

    class Meta:
        ordering = ["id"]

    def __str__(self):
        name: str = self.name if self.name else self.get_type_display()  # type: ignore
        if self.manual_checks_complete_date:
            return f"{name} - Completed"
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
        return str(f"{self.type} | {self.sub_type} | {self.name}")


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
