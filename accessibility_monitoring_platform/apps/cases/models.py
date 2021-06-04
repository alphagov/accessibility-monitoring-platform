"""
Models - cases
"""
from django.db import models
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.utils import timezone

STATUS_CHOICES = [
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

TEST_TYPE_CHOICES = [
    ("simple", "Simple"),
    ("detailed", "Detailed"),
]

WEBSITE_TYPE_CHOICES = [
    ("public", "Public website"),
    ("int-extranet", "Intranet/Extranet"),
    ("other", "Other"),
    ("unknown", "Unknown"),
]

CASE_ORIGIN_CHOICES = [
    ("org", "Organisation"),
    ("list", "Website list"),
    ("complaint", "Complaint"),
]

TEST_STATUS_CHOICES = [
    ("complete", "Complete"),
    ("in-progress", "In progress"),
    ("not-started", "Not started"),
]

REPORT_REVIEW_STATUS_CHOICES = [
    ("ready-to-review", "Yes"),
    ("in-progress", "In progress"),
    ("not-started", "Not started"),
]

REPORT_APPROVED_STATUS_CHOICES = [
    ("yes", "Yes"),
    ("no", "Further work is needed"),
]

ACCESSIBILITY_STATEMENT_DECISION_CHOICES = [
    ("compliant", "Compliant"),
    ("partially", "Partially compliant"),
    ("not-compliant", "Not compliant"),
    ("other", "Other"),
]

COMPLIANCE_DECISION_CHOICES = [
    ("inaction", "No further action"),
    ("other", "Other"),
    ("unknown", "Unknown"),
]


class Case(models.Model):
    """
    Model for Case
    """

    created = models.DateTimeField()
    status = models.CharField(max_length=200, choices=STATUS_CHOICES)
    auditor = models.CharField(max_length=200)
    test_type = models.CharField(
        max_length=10, choices=TEST_TYPE_CHOICES, default="simple"
    )
    home_page_url = models.TextField(default="")
    domain = models.TextField(default="")
    application = models.CharField(max_length=200, default="N/A")
    organisation_name = models.TextField(default="")
    website_type = models.CharField(
        max_length=100, choices=WEBSITE_TYPE_CHOICES, default="public"
    )
    sector = models.CharField(max_length=200, default="Sector")
    region = models.CharField(max_length=200, default="London")
    case_origin = models.CharField(
        max_length=200, choices=CASE_ORIGIN_CHOICES, default="org"
    )
    zendesk_url = models.CharField(max_length=200, default="")
    trello_url = models.CharField(max_length=200, default="")
    notes = models.TextField(default="")
    is_public_sector_body = models.BooleanField(default=True)
    test_results_url = models.CharField(max_length=200, default="")
    test_status = models.CharField(
        max_length=200, choices=TEST_STATUS_CHOICES, default="not-started"
    )
    is_website_compliant = models.BooleanField(default=False)
    test_notes = models.TextField(default="")
    report_draft_url = models.CharField(max_length=200, default="")
    report_review_status = models.CharField(
        max_length=200, choices=REPORT_REVIEW_STATUS_CHOICES, default="not-started"
    )
    reviewer = models.CharField(max_length=200, default="")
    report_approved_status = models.CharField(
        max_length=200, choices=REPORT_APPROVED_STATUS_CHOICES, default="no"
    )
    reviewer_notes = models.TextField(default="")
    report_final_url = models.CharField(max_length=200, default="")
    report_sent_date = models.DateField(null=True)
    report_acknowledged_date = models.DateField(null=True)
    week_12_followup_date = models.DateField(null=True)
    psb_progress_notes = models.TextField(default="")
    week_12_followup_email_sent_date = models.DateField(null=True)
    week_12_followup_email_acknowledgement_date = models.DateField(null=True)
    is_website_retested = models.BooleanField(default=False)
    is_disproportionate_claimed = models.BooleanField(default=False)
    disproportionate_notes = models.TextField(default="")
    accessibility_statement_decison = models.CharField(
        max_length=200,
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        default="not-compliant",
    )
    accessibility_statement_url = models.CharField(max_length=200, default="")
    accessibility_statement_notes = models.TextField(default="")
    compliance_decision = models.CharField(
        max_length=200, choices=COMPLIANCE_DECISION_CHOICES, default="unknown"
    )
    compliance_decision_notes = models.TextField(default="")
    compliance_email_sent_date = models.DateField(null=True)
    sent_to_enforcement_body_sent_date = models.DateField(null=True)
    is_case_completed = models.BooleanField(default=False)
    completed = models.DateTimeField(null=True)
    archived = models.BooleanField(default=False)

    simplified_test_filename = models.CharField(max_length=200)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return str(f"#{self.id} {self.organisation_name}")

    def get_absolute_url(self):
        return reverse("cases:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self.is_case_completed and not self.completed:
            self.completed = timezone.now()
        super().save(*args, **kwargs)
class Contact(models.Model):
    """
    Model for cases Contact
    """

    case = models.ForeignKey(Case, on_delete=CASCADE)
    first_name = models.CharField(max_length=200, default="")
    last_name = models.CharField(max_length=200, default="")
    job_title = models.CharField(max_length=200, default="")
    detail = models.CharField(max_length=200, default="")
    preferred = models.BooleanField(default=False)
    notes = models.TextField(default="")
    created = models.DateTimeField()
    created_by = models.CharField(max_length=200)
    archived = models.BooleanField(default=False)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return str(f"Case #{self.case.id}: {self.job_title} {self.name}")

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        super().save(*args, **kwargs)
