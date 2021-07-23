"""
Models - cases
"""
from datetime import date
from typing import List, Tuple

from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.utils import timezone

from ..common.utils import extract_domain_from_url
from ..common.models import Region, Sector

STATUS_CHOICES: List[Tuple[str, str]] = [
    ("unknown", "Unknown"),
    ("unassigned-case", "Unassigned case"),
    ("new-case", "New case"),
    ("test-in-progress", "Test in progress"),
    ("report-in-progress", "Report in progress"),
    ("qa-in-progress", "QA in progress"),
    ("report-ready-to-send", "Report ready to send"),
    ("in-report-correspondence", "In report correspondence"),
    ("in-probation-period", "In probation period"),
    ("in-12-week-correspondence", "In 12 week correspondence"),
    ("final-decision", "Final decision"),
    ("complete", "Complete"),
    ("archived", "Archived"),
]

QA_STATUS_CHOICES: List[Tuple[str, str]] = [
    ("unknown", "Unknown"),
    ("unassigned-qa-case", "Unassigned QA case"),
    ("in-qa", "In QA"),
    ("qa-approved", "QA approved"),
]

EB_STATUS_CHOICES: List[Tuple[str, str]] = [
    ("unknown", "Unknown"),
    ("no-correspondence", "No correspondence"),
    ("in-correspondence", "In correspondence"),
    ("completed", "Completed"),
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

ARCHIVE_DECISION_CHOICES: List[Tuple[str, str]] = [
    ("not-psb", "Organisation is not a public sector body"),
    ("mistake", "Case was opened by mistake"),
    ("duplicate", "This case was a duplicate case"),
    ("other", "Other"),
]

DEFAULT_CASE_COMPLETED = "no-decision"
CASE_COMPLETED_CHOICES = [
    (
        "no-action",
        "No further action is required and the case can be marked as complete",
    ),
    ("escalated", "The audit needs to be sent to the relevant equalities body"),
    (DEFAULT_CASE_COMPLETED, "Decision not reached"),
]

DEFAULT_ESCALATION_STATE = "unknown"
ESCALATION_STATE_CHOICES = [
    (
        "no-action",
        "No further action is required and correspondence has closed regarding this issue",
    ),
    ("ongoing", "Correspondence ongoing"),
    (DEFAULT_ESCALATION_STATE, "Not known"),
]


class Case(models.Model):
    """
    Model for Case
    """

    created = models.DateTimeField(blank=True)
    status = models.CharField(
        max_length=200, choices=STATUS_CHOICES, default="new-case"
    )
    qa_status = models.CharField(
        max_length=200, choices=QA_STATUS_CHOICES, default="unknown"
    )
    equalities_body_status = models.CharField(
        max_length=200, choices=EB_STATUS_CHOICES, default="unknown"
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
    region = models.ManyToManyField(Region, blank=True)
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
    report_is_ready_to_review = models.BooleanField(default=False)
    report_is_approved = models.BooleanField(default=False)
    report_approved_status = models.CharField(
        max_length=200, choices=REPORT_APPROVED_STATUS_CHOICES, default="no"
    )
    reviewer_notes = models.TextField(default="", blank=True)
    report_final_url = models.CharField(max_length=200, default="", blank=True)
    report_sent_date = models.DateField(null=True, blank=True)

    report_acknowledged_date = models.DateField(null=True, blank=True)
    report_followup_week_1_due_date = models.DateField(null=True, blank=True)
    report_followup_week_1_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_4_due_date = models.DateField(null=True, blank=True)
    report_followup_week_4_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_12_due_date = models.DateField(null=True, blank=True)
    report_followup_week_12_sent_date = models.DateField(null=True, blank=True)

    twelve_week_1_week_chaser_due_date = models.DateField(null=True, blank=True)
    twelve_week_1_week_chaser_sent_date = models.DateField(null=True, blank=True)
    twelve_week_4_week_chaser_due_date = models.DateField(null=True, blank=True)
    twelve_week_4_week_chaser_sent_date = models.DateField(null=True, blank=True)
    twelve_week_correspondence_acknowledged_date = models.DateField(
        null=True, blank=True
    )

    correspondence_notes = models.TextField(default="", blank=True)
    psb_progress_notes = models.TextField(default="", blank=True)
    retested_website = models.DateField(null=True, blank=True)
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
    enforcement_body_correspondence_notes = models.TextField(default="", blank=True)
    escalation_state = models.CharField(
        max_length=20,
        choices=ESCALATION_STATE_CHOICES,
        default=DEFAULT_ESCALATION_STATE,
    )
    case_completed = models.CharField(
        max_length=20, choices=CASE_COMPLETED_CHOICES, default=DEFAULT_CASE_COMPLETED
    )
    completed = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archive_reason = models.CharField(
        max_length=200, choices=ARCHIVE_DECISION_CHOICES, default="unknown"
    )
    archive_notes = models.TextField(default="", blank=True)
    no_psb_contact = models.BooleanField(default=False)

    simplified_test_filename = models.CharField(max_length=200, default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="case_created_by_user",
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(f"#{self.id} | {self.organisation_name}")

    def get_absolute_url(self):
        return reverse("cases:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.case_completed != DEFAULT_CASE_COMPLETED and not self.completed:
            self.completed = now
        self.status = self.set_status()
        self.qa_status = self.set_qa_status()
        self.equalities_body_status = self.set_equalities_body_status()
        super().save(*args, **kwargs)

    @property
    def summary(self):
        return str(f"{self.organisation_name} | {self.domain} | #{self.id}")

    def set_status(self):
        if self.is_archived:
            return "archived"
        elif self.case_completed != DEFAULT_CASE_COMPLETED:
            return "complete"
        elif self.auditor is None:
            return "unassigned-case"
        elif self.contact_exists is False:
            return "new-case"
        elif self.test_status != "complete" and self.report_sent_date is None:
            return "test-in-progress"
        elif self.test_status == "complete" and self.report_review_status != "ready-to-review":
            return "report-in-progress"
        elif self.report_review_status == "ready-to-review" and self.report_approved_status == "no":
            return "qa-in-progress"
        elif self.report_approved_status == "yes" and self.report_sent_date is None:
            return "report-ready-to-send"
        elif self.report_sent_date and self.report_acknowledged_date is None:
            return "in-report-correspondence"
        elif self.report_acknowledged_date and self.report_followup_week_12_sent_date is None:
            return "in-probation-period"
        elif self.report_followup_week_12_sent_date and self.twelve_week_correspondence_acknowledged_date is None:
            # TODO Add 'no response to 12 week update' as an option once field is in model
            # i.e.
            # elif self.twelve_week_update_requested_sent_date \
            #   and self.twelve_week_correspondence_acknowledged_date is None\
            #   and self.twelve_week_correspondence_no_response is None:
            return "in-12-week-correspondence"
        elif self.twelve_week_correspondence_acknowledged_date and self.case_completed == DEFAULT_CASE_COMPLETED:
            # TODO Same as above but final-decision-due
            return "final-decision-due"

        return "unknown"

    def set_qa_status(self):
        if (
            self.reviewer is None
            and self.report_review_status == "ready-to-review"
            and self.report_approved_status != "yes"
        ):
            return "unassigned-qa-case"
        elif (
            self.report_review_status == "ready-to-review"
            and self.report_approved_status != "yes"
        ):
            return "in-qa"
        elif (
            self.report_review_status == "ready-to-review"
            and self.report_approved_status == "yes"
        ):
            return "qa-approved"
        return "unknown"

    def set_equalities_body_status(self):
        if (self.sent_to_enforcement_body_sent_date is None and self.no_psb_contact is None):
            return "no-correspondence"
        elif (self.sent_to_enforcement_body_sent_date or self.no_psb_contact is None):
            return "in-correspondence"
        return "completed"
        # TODO: Need to add explicit finished state once field has been added to model and form.

    @property
    def new_case_progress(self):
        to_check = [
            "auditor",
            "test_type",
            "home_page_url",
            "organisation_name",
            "website_type",
            "region",
            "case_origin",
        ]
        percentage_increase = round(100 / (len(to_check) + 2))
        progress = 0
        for field in to_check:
            if getattr(self, field):
                progress += percentage_increase

        if self.region.values_list("name", flat=True).exists():
            progress += percentage_increase

        if Contact.objects.filter(case_id=self.id).exists():
            progress += percentage_increase

        return str(progress) + "%"

    @property
    def test_progress(self):
        to_check = [
            "test_results_url",
        ]
        percentage_increase = round(100 / (len(to_check) + 1))
        progress = 0
        for field in to_check:
            if getattr(self, field):
                progress += percentage_increase
        if self.test_status == "complete":
            progress += percentage_increase
        return str(progress) + "%"

    @property
    def report_progress(self):
        if (
            self.report_review_status == "ready-to-review"
            and self.reviewer
            and self.report_approved_status == "no"
        ):
            return "Being reviewed"

        if (
            self.report_review_status == "ready-to-review"
            and self.reviewer
            and self.report_approved_status == "yes"
        ):
            return "Ready to send"

        to_check = [
            "report_draft_url",
            "reviewer",
            "report_final_url",
            "report_sent_date",
            "report_acknowledged_date",
        ]
        percentage_increase = round(100 / (len(to_check) + 2))
        progress = 0
        for field in to_check:
            if getattr(self, field):
                progress += percentage_increase

        if self.report_review_status == "ready-to-review":
            progress += percentage_increase

        if self.report_approved_status == "yes":
            progress += percentage_increase

        return str(progress) + "%"

    @property
    def in_report_correspondence_progress(self):
        now = date.today()
        if (
            self.report_followup_week_1_due_date 
            and self.report_followup_week_1_due_date > now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1 week followup coming up"
        elif (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date < now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1 week followup due"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date > now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4 week followup coming up"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date < now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4 week followup due"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_sent_date
        ):
            return "4 week followup sent"
        return "Unknown"

    @property
    def twelve_week_correspondence_progress(self):
        now = date.today()
    #         twelve_week_1_week_chaser_due_date = models.DateField(null=True, blank=True)
    # twelve_week_1_week_chaser_sent_date = models.DateField(null=True, blank=True)
    # twelve_week_4_week_chaser_due_date = models.DateField(null=True, blank=True)
    # twelve_week_4_week_chaser_sent_date = models.DateField(null=True, blank=True)
        # if (
        #     self.twelve_week_1_week_chaser_due_date > now
        #     and self.twelve_week_1_week_chaser_sent_date is None
        # ):
        #     return "1 week chaser coming up"
        # elif (
        #     self.twelve_week_update_requested_sent_date < now
        #     and self.twelve_week_update_requested_sent_date is None
        # ):
        #     return "1 week chaser due"
        # elif (
        #     self.twelve_week_update_requested_sent_date
        #     and self.twelve_week_4_week_chaser_due_date > now
        #     and self.twelve_week_4_week_chaser_sent_date is None
        # ):
        #     return "4 week chaser coming up"
        # elif (
        #     self.twelve_week_update_requested_sent_date
        #     and self.twelve_week_4_week_chaser_due_date < now
        #     and self.twelve_week_4_week_chaser_sent_date is None
        # ):
        #     return "4 week chaser due"
        # elif (
        #     self.twelve_week_update_requested_sent_date
        #     and self.twelve_week_4_week_chaser_sent_date
        # ):
        #     return "4 week chaser sent"
        return "Unknown"

    @property
    def final_decision_progress(self):
        return "TO DO PROGRESS"

    @property
    def twelve_week_progress(self):
        if self.report_followup_week_12_sent_date is None:
            return "Follow up email not sent"

        if (
            self.report_followup_week_12_sent_date
            and self.report_acknowledged_date is None
        ):
            now = date.today()
            return "No response - {} days".format(
                (now - self.report_followup_week_12_sent_date).days
            )

        to_check = [
            "report_followup_week_12_due_date",
            "report_followup_week_12_sent_date",
            "report_acknowledged_date",
            "compliance_email_sent_date",
        ]
        percentage_increase = round(100 / (len(to_check)))
        progress = 0
        for field in to_check:
            if getattr(self, field):
                progress += percentage_increase

        return str(progress) + "%"

    @property
    def contact_exists(self):
        return Contact.objects.filter(case_id=self.id).exists()


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
        return str(f"{self.detail} (Case #{self.case.id})")

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        super().save(*args, **kwargs)
