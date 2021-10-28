"""
Models - checks (called tests by the users)
"""
from typing import List, Tuple

from django.db import models
from django.urls import reverse

from ..cases.models import Case
from ..common.models import VersionModel, BOOLEAN_CHOICES, BOOLEAN_DEFAULT

SCREEN_SIZE_DEFAULT = "15in"
SCREEN_SIZE_CHOICES: List[Tuple[str, str]] = [
    (SCREEN_SIZE_DEFAULT, "15 inch"),
    ("13in", "13 inch"),
]
EXEMPTION_DEFAULT = "unknown"
EXEMPTION_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (EXEMPTION_DEFAULT, "Unknown"),
]
CHECK_TYPE_DEFAULT = "initial"
CHECK_TYPE_CHOICES: List[Tuple[str, str]] = [
    (CHECK_TYPE_DEFAULT, "Initial"),
    ("eq-retest", "Equality body retest"),
]
PAGE_TYPE_EXTRA = "extra"
PAGE_TYPE_HOME = "home"
PAGE_TYPE_CONTACT = "contact"
PAGE_TYPE_STATEMENT = "statement"
PAGE_TYPE_PDF = "pdf"
PAGE_TYPE_FORM = "form"
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


class Check(VersionModel):
    """
    Model for test/check
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="check_case")
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
        max_length=20, choices=CHECK_TYPE_CHOICES, default=CHECK_TYPE_DEFAULT
    )
    check_metadata_complete_date = models.DateField(null=True, blank=True)

    # pages page
    check_pages_complete_date = models.DateField(null=True, blank=True)

    # manual page
    check_manual_complete_date = models.DateField(null=True, blank=True)

    # axe page
    check_axe_complete_date = models.DateField(null=True, blank=True)

    # pdf page
    check_pdf_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(f"{self.description} | #{self.id}")  # type: ignore

    def get_absolute_url(self):
        return reverse(
            "checks:edit-check-metadata",
            kwargs={"pk": self.pk, "case_id": self.case.pk},
        )


class Page(VersionModel):
    """
    Model for test/check page
    """

    parent_check = models.ForeignKey(
        Check, on_delete=models.CASCADE, related_name="page_check"
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
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(f"{self.parent_check} | {self.type} | #{self.pk}")  # type: ignore

    def get_absolute_url(self):
        return reverse(
            "checks:edit-check-page",
            kwargs={"pk": self.check.pk, "case_id": self.check.case.pk},
        )
