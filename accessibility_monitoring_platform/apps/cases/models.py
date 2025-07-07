"""
Models - cases
"""

from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..common.models import Boolean, Sector, SubCategory, VersionModel

ONE_WEEK_IN_DAYS: int = 7
MAX_LENGTH_OF_FORMATTED_URL: int = 25
PSB_APPEAL_WINDOW_IN_DAYS: int = 28

COMPLIANCE_FIELDS: list[str] = [
    "website_compliance_state_initial",
    "website_compliance_notes_initial",
    "statement_compliance_state_initial",
    "statement_compliance_notes_initial",
    "website_compliance_state_12_week",
    "website_compliance_notes_12_week",
    "statement_compliance_state_12_week",
    "statement_compliance_notes_12_week",
]

UPDATE_SEPARATOR: str = " -> "


class SimplifiedCaseStatus(models.TextChoices):
    UNASSIGNED = "000-unassigned-case", "Unassigned case"
    TEST_IN_PROGRESS = "050-test-in-progress", "Test in progress"
    REPORT_IN_PROGRESS = "060-report-in-progress", "Report in progress"
    READY_TO_QA = "070-unassigned-qa-case", "Report ready to QA"
    QA_IN_PROGRESS = "080-qa-in-progress", "QA in progress"
    REPORT_READY_TO_SEND = "090-report-ready-to-send", "Report ready to send"
    IN_REPORT_CORES = "100-in-report-correspondence", "Report sent"
    AWAITING_12_WEEK_DEADLINE = (
        "120-in-12-week-period",
        "Report acknowledged waiting for 12-week deadline",
    )
    AFTER_12_WEEK_CORES = (
        "140-after-12-week-correspondence",
        "After 12-week correspondence",
    )
    REVIEWING_CHANGES = "150-reviewing-changes", "Reviewing changes"
    FINAL_DECISION_DUE = "160-final-decision-due", "Final decision due"
    CASE_CLOSED_WAITING_TO_SEND = (
        "170-case-closed-waiting-to-be-sent",
        "Case closed and waiting to be sent to equalities body",
    )
    CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY = (
        "180-case-closed-sent-to-equalities-body",
        "Case closed and sent to equalities body",
    )
    IN_CORES_WITH_ENFORCEMENT_BODY = (
        "190-in-correspondence-with-equalities-body",
        "In correspondence with equalities body",
    )
    COMPLETE = "200-complete", "Complete"
    DEACTIVATED = "900-deactivated", "Deactivated"
    UNKNOWN = "910-unknown", "Unknown"


class DetailedCaseStatus(models.TextChoices):
    UNASSIGNED = "000-unassigned-case", "Unassigned case"
    PSB_INFO_REQ = "010-initial-psb-info-requested", "Requested information"
    PSB_INFO_CHASING = (
        "020-initial-psb-info-chasing",
        "Chasing - no response / missed deadline",
    )
    PSB_INFO_REQ_ACK = "030-initial-psb-info-req-ack", "Acknowledge our request"
    PSB_INFO_RECEIVED = "040-initial-psb-info-received", "Received Details/Access"
    TEST_IN_PROGRESS = "050-test-in-progress", "Test in progress"
    REPORT_IN_PROGRESS = "060-report-in-progress", "Report in progress"
    READY_TO_QA = "070-unassigned-qa-case", "Report ready to QA"
    REPORT_READY_TO_SEND = "090-report-ready-to-send", "Report ready to send"
    IN_REPORT_CORES = "100-in-report-correspondence", "Report sent"
    AWAITING_REPORT_ACK = "110-awaiting-report-ack", "Waiting for response"
    AWAITING_12_WEEK_DEADLINE = (
        "120-in-12-week-period",
        "Report acknowledged waiting for 12-week deadline",
    )
    REQUESTED_12_WEEK_UPDATE = (
        "130-12-week-requested-update",
        "Requested update at 12 weeks",
    )
    AFTER_12_WEEK_CORES = (
        "140-after-12-week-correspondence",
        "After 12-week correspondence",
    )
    REVIEWING_CHANGES = "150-reviewing-changes", "Reviewing changes"
    CASE_CLOSED_WAITING_TO_SEND = (
        "170-case-closed-waiting-to-be-sent",
        "Case closed and waiting to be sent to equalities body",
    )
    CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY = (
        "180-case-closed-sent-to-equalities-body",
        "Case closed and sent to equalities body",
    )
    COMPLETE = "200-complete", "Complete"
    UNKNOWN = "910-unknown", "Unknown"


class MobileCaseStatus(models.TextChoices):
    UNASSIGNED = "000-unassigned-case", "Unassigned case"
    TEST_IN_PROGRESS = "050-test-in-progress", "Test in progress"
    REPORT_IN_PROGRESS = "060-report-in-progress", "Report in progress"
    READY_TO_QA = "070-unassigned-qa-case", "Report ready to QA"
    REPORT_READY_TO_SEND = "090-report-ready-to-send", "Report ready to send"
    IN_REPORT_CORES = "100-in-report-correspondence", "Report sent"
    AWAITING_12_WEEK_DEADLINE = (
        "120-in-12-week-period",
        "Report acknowledged waiting for 12-week deadline",
    )
    AFTER_12_WEEK_CORES = (
        "140-after-12-week-correspondence",
        "After 12-week correspondence",
    )
    REVIEWING_CHANGES = "150-reviewing-changes", "Reviewing changes"
    CASE_CLOSED_WAITING_TO_SEND = (
        "170-case-closed-waiting-to-be-sent",
        "Case closed and waiting to be sent to equalities body",
    )
    CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY = (
        "180-case-closed-sent-to-equalities-body",
        "Case closed and sent to equalities body",
    )
    COMPLETE = "200-complete", "Complete"
    UNKNOWN = "910-unknown", "Unknown"


ALL_CASE_STATUS_CHOICES: list[tuple[str, str]] = sorted(
    list(
        set(
            SimplifiedCaseStatus.choices
            + DetailedCaseStatus.choices
            + MobileCaseStatus.choices
        )
    )
)


class Sort(models.TextChoices):
    NEWEST = "", "Newest, Unassigned first"
    OLDEST = "id", "Oldest"
    NAME = "organisation_name", "Alphabetic"


class BaseCase(VersionModel):
    """
    Model for Case
    """

    class TestType(models.TextChoices):
        SIMPLIFIED = "simplified", "Simplified"
        DETAILED = "detailed", "Detailed"
        MOBILE = "mobile", "Mobile"

    class PsbLocation(models.TextChoices):
        ENGLAND = "england", "England"
        SCOTLAND = "scotland", "Scotland"
        WALES = "wales", "Wales"
        NI = "northern_ireland", "Northern Ireland"
        UK = "uk_wide", "UK-wide"
        UNKNOWN = "unknown", "Unknown"

    class EnforcementBody(models.TextChoices):
        EHRC = "ehrc", "Equality and Human Rights Commission"
        ECNI = "ecni", "Equality Commission Northern Ireland"

    class RecommendationForEnforcement(models.TextChoices):
        NO_FURTHER_ACTION = "no-further-action", "No further action"
        OTHER = "other", "For enforcement consideration"
        UNKNOWN = "unknown", "Not selected"

    class Status(models.TextChoices):
        UNASSIGNED = "000-unassigned-case", "Unassigned case"
        PSB_INFO_REQ = "010-initial-psb-info-requested", "Requested information"
        PSB_INFO_CHASING = (
            "020-initial-psb-info-chasing",
            "Chasing - no response / missed deadline",
        )
        PSB_INFO_REQ_ACK = "030-initial-psb-info-req-ack", "Acknowledge our request"
        PSB_INFO_RECEIVED = "040-initial-psb-info-received", "Received Details/Access"
        TEST_IN_PROGRESS = "050-test-in-progress", "Test in progress"
        REPORT_IN_PROGRESS = "060-report-in-progress", "Report in progress"
        READY_TO_QA = "070-unassigned-qa-case", "Report ready to QA"
        QA_IN_PROGRESS = "080-qa-in-progress", "QA in progress"
        REPORT_READY_TO_SEND = "090-report-ready-to-send", "Report ready to send"
        IN_REPORT_CORES = "100-in-report-correspondence", "Report sent"
        AWAITING_REPORT_ACK = "110-awaiting-report-ack", "Waiting for response"
        AWAITING_12_WEEK_DEADLINE = (
            "120-in-12-week-period",
            "Report acknowledged waiting for 12-week deadline",
        )
        REQUESTED_12_WEEK_UPDATE = (
            "130-12-week-requested-update",
            "Requested update at 12 weeks",
        )
        AFTER_12_WEEK_CORES = (
            "140-after-12-week-correspondence",
            "After 12-week correspondence",
        )
        REVIEWING_CHANGES = "150-reviewing-changes", "Reviewing changes"
        FINAL_DECISION_DUE = "160-final-decision-due", "Final decision due"
        CASE_CLOSED_WAITING_TO_SEND = (
            "170-case-closed-waiting-to-be-sent",
            "Case closed and waiting to be sent to equalities body",
        )
        CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY = (
            "180-case-closed-sent-to-equalities-body",
            "Case closed and sent to equalities body",
        )
        IN_CORES_WITH_ENFORCEMENT_BODY = (
            "190-in-correspondence-with-equalities-body",
            "In correspondence with equalities body",
        )
        COMPLETE = "200-complete", "Complete"
        DEACTIVATED = "900-deactivated", "Deactivated"
        UNKNOWN = "910-unknown", "Unknown"

    CLOSED_CASE_STATUSES: list[str] = [
        Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
        Status.COMPLETE,
        Status.CASE_CLOSED_WAITING_TO_SEND,
        Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        Status.DEACTIVATED,
    ]

    case_number = models.IntegerField(default=1)
    case_identifier = models.CharField(max_length=20, default="")
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="basecase_created_by",
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=200, choices=Status.choices, default=Status.UNASSIGNED
    )

    # Case metadata page
    created = models.DateTimeField(blank=True)
    auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="basecase_auditor",
        blank=True,
        null=True,
    )
    test_type = models.CharField(
        max_length=10, choices=TestType.choices, default=TestType.SIMPLIFIED
    )
    home_page_url = models.TextField(default="", blank=True)
    domain = models.TextField(default="", blank=True)
    organisation_name = models.TextField(default="", blank=True)
    psb_location = models.CharField(
        max_length=20,
        choices=PsbLocation.choices,
        default=PsbLocation.UNKNOWN,
    )
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, null=True, blank=True)
    enforcement_body = models.CharField(
        max_length=20,
        choices=EnforcementBody.choices,
        default=EnforcementBody.EHRC,
    )
    is_complaint = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    parental_organisation_name = models.TextField(default="", blank=True)
    website_name = models.TextField(default="", blank=True)
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    is_feedback_requested = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    case_details_complete_date = models.DateField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="basecase_reviewer",
        blank=True,
        null=True,
    )
    recommendation_for_enforcement = models.CharField(
        max_length=20,
        choices=RecommendationForEnforcement.choices,
        default=RecommendationForEnforcement.UNKNOWN,
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        if self.organisation_name:
            return f"{self.organisation_name} | {self.case_identifier}"
        return self.case_identifier

    def save(self, *args, **kwargs) -> None:
        now: datetime = timezone.now()
        if not self.id:
            self.created = now
            max_case_number = BaseCase.objects.aggregate(models.Max("case_number")).get(
                "case_number__max"
            )
            if max_case_number is not None:
                self.case_number = max_case_number + 1
            self.case_identifier = f"#{self.test_type[0].upper()}-{self.case_number}"
        self.updated = now
        self.updated_date = now.date()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse(f"{self.test_type}:case-detail", kwargs={"pk": self.pk})
