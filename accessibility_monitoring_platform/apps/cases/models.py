"""
Models - cases
"""
from datetime import timedelta
from typing import List, Tuple

from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.utils import timezone

from ..common.utils import extract_domain_from_url
from ..common.models import Region, Sector

STATUS_CHOICES: List[Tuple[str, str]] = [
    ("new-case", "New case"),
    ("test-in-progress", "Test in progress"),
    ("report-in-progress", "Report in progress"),
    ("awaiting-response", "Awaiting response to report"),
    ("12w-due", "12 Week review due"),
    ("12w-sent", "12 Week review sent"),
    ("escalated", "Case sent to supporting bodies"),
    ("complete", "Complete"),
    ("archived", "Archived"),
    ("not-a-psb", "Not a public sector body"),
]

DEFAULT_TEST_TYPE = "simple"
TEST_TYPE_CHOICES: List[Tuple[str, str]] = [
    (DEFAULT_TEST_TYPE, "Simplified"),
    ("detailed", "Detailed"),
]

DEFAULT_WEBSITE_TYPE = "public"
WEBSITE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (DEFAULT_WEBSITE_TYPE, "Public website"),
    ("int-extranet", "Intranet/Extranet"),
    ("n/a", "N/A"),
]

CASE_ORIGIN_CHOICES: List[Tuple[str, str]] = [
    ("org", "Organisation"),
    ("list", "Website list"),
    ("complaint", "Complaint"),
]

TEST_STATUS_CHOICES: List[Tuple[str, str]] = [
    ("complete", "Complete"),
    ("in-progress", "In progress"),
    ("not-started", "Not started"),
]

REPORT_REVIEW_STATUS_CHOICES: List[Tuple[str, str]] = [
    ("ready-to-review", "Yes"),
    ("in-progress", "In progress"),
    ("not-started", "Not started"),
]

REPORT_APPROVED_STATUS_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "Further work is needed"),
]

ACCESSIBILITY_STATEMENT_DECISION_CHOICES: List[Tuple[str, str]] = [
    ("compliant", "Compliant"),
    ("partially", "Partially compliant"),
    ("not-compliant", "Not compliant"),
    ("other", "Other"),
]

COMPLIANCE_DECISION_CHOICES: List[Tuple[str, str]] = [
    ("inaction", "No further action"),
    ("other", "Other"),
    ("unknown", "Unknown"),
]


class Case(models.Model):
    """
    Model for Case
    """

    created = models.DateTimeField(blank=True)
    status = models.CharField(
        max_length=200, choices=STATUS_CHOICES, default="new-case"
    )
    auditor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="case_auditor_user",
        blank=True,
        null=True,
    )
    test_type = models.CharField(
        max_length=10, choices=TEST_TYPE_CHOICES, default=DEFAULT_TEST_TYPE
    )
    home_page_url = models.TextField(default="", blank=True)
    domain = models.TextField(default="", blank=True)
    application = models.CharField(max_length=200, default="N/A")
    organisation_name = models.TextField(default="", blank=True)
    service_name = models.TextField(default="", blank=True)
    website_type = models.CharField(
        max_length=100, choices=WEBSITE_TYPE_CHOICES, default=DEFAULT_WEBSITE_TYPE
    )
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True)
    region = models.ManyToManyField(Region, null=True, blank=True)
    case_origin = models.CharField(
        max_length=200, choices=CASE_ORIGIN_CHOICES, default="org"
    )
    zendesk_url = models.CharField(max_length=200, default="", blank=True)
    trello_url = models.CharField(max_length=200, default="", blank=True)
    notes = models.TextField(default="", blank=True)
    is_public_sector_body = models.BooleanField(default=True)
    test_results_url = models.CharField(max_length=200, default="", blank=True)
    test_status = models.CharField(
        max_length=200, choices=TEST_STATUS_CHOICES, default="not-started"
    )
    is_website_compliant = models.BooleanField(null=True, blank=True)
    test_notes = models.TextField(default="", blank=True)
    report_draft_url = models.CharField(max_length=200, default="", blank=True)
    report_review_status = models.CharField(
        max_length=200, choices=REPORT_REVIEW_STATUS_CHOICES, default="not-started"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="case_reviewer_user",
        blank=True,
        null=True,
    )
    report_approved_status = models.CharField(
        max_length=200, choices=REPORT_APPROVED_STATUS_CHOICES, default="no"
    )
    reviewer_notes = models.TextField(default="", blank=True)
    report_final_url = models.CharField(max_length=200, default="", blank=True)
    report_sent_date = models.DateField(null=True, blank=True)
    report_acknowledged_date = models.DateField(null=True, blank=True)
    week_12_followup_date = models.DateField(null=True, blank=True)
    psb_progress_notes = models.TextField(default="", blank=True)
    week_12_followup_email_sent_date = models.DateField(null=True, blank=True)
    week_12_followup_email_acknowledgement_date = models.DateField(
        null=True, blank=True
    )
    is_website_retested = models.BooleanField(default=False)
    is_disproportionate_claimed = models.BooleanField(null=True, blank=True)
    disproportionate_notes = models.TextField(default="", blank=True)
    accessibility_statement_decison = models.CharField(
        max_length=200,
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        default="not-compliant",
    )
    accessibility_statement_url = models.CharField(
        max_length=200, default="", blank=True
    )
    accessibility_statement_notes = models.TextField(default="", blank=True)
    compliance_decision = models.CharField(
        max_length=200, choices=COMPLIANCE_DECISION_CHOICES, default="unknown"
    )
    compliance_decision_notes = models.TextField(default="", blank=True)
    compliance_email_sent_date = models.DateField(null=True, blank=True)
    sent_to_enforcement_body_sent_date = models.DateField(null=True, blank=True)
    is_case_completed = models.BooleanField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    simplified_test_filename = models.CharField(max_length=200, default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="case_created_by_user",
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(f"#{self.id} {self.organisation_name}")

    def get_absolute_url(self):
        return reverse("cases:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.is_case_completed and not self.completed:
            self.completed = now
        if self.report_acknowledged_date and not self.week_12_followup_date:
            self.week_12_followup_date = self.report_acknowledged_date + timedelta(
                weeks=12
            )
        super().save(*args, **kwargs)


class Contact(models.Model):
    """
    Model for cases Contact
    """

    case = models.ForeignKey(Case, on_delete=CASCADE)
    first_name = models.CharField(max_length=200, default="", blank=True)
    last_name = models.CharField(max_length=200, default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    detail = models.CharField(max_length=200, default="", blank=True)
    preferred = models.BooleanField(null=True, blank=True)
    notes = models.TextField(default="", blank=True)
    created = models.DateTimeField()
    created_by = models.CharField(max_length=200, default="", blank=True)
    is_archived = models.BooleanField(default=False)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return str(f"Case #{self.case.id}: {self.job_title} {self.name}")

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        super().save(*args, **kwargs)
