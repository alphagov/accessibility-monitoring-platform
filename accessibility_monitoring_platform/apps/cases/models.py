"""
Models - cases
"""

import re
from dataclasses import dataclass
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

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


def extract_id_from_case_url(case_url: str) -> int | None:
    """Extract case id from case overview URL"""
    regex_search_result = re.search(
        ".*/(simplified|detailed|mobile)/(.+?)/(view|case-detail)/?", case_url
    )
    if regex_search_result is not None:
        case_id: str = regex_search_result.group(2)
        if case_id.isdigit():
            return int(case_id)


def get_previous_case_identifier(previous_case_url: str) -> str | None:
    """Build case identifier from URL"""
    case_id: int | None = extract_id_from_case_url(case_url=previous_case_url)
    if case_id:
        base_case: BaseCase = BaseCase.objects.get(id=case_id)
        return base_case.case_identifier


class DisablePyTestCollectionMixin(object):
    __test__ = False


class TestType(DisablePyTestCollectionMixin, models.TextChoices):
    SIMPLIFIED = "simplified", "Simplified"
    DETAILED = "detailed", "Detailed"
    MOBILE = "mobile", "Mobile"


@dataclass
class CaseStatusChoice:
    name: str
    value: str
    label: str
    test_types: list[TestType]

    @property
    def search_cases_choices_label(self):
        if len(self.test_types) < len(TestType):
            test_type_initials: str = "&".join(
                [test_type.label[0] for test_type in self.test_types]
            )
            return f"{self.label} ({test_type_initials})"
        return self.label


CASE_STATUS_UNKNOWN: CaseStatusChoice = CaseStatusChoice(
    name="UNKNOWN",
    value="910-unknown",
    label="Unknown",
    test_types=[TestType.SIMPLIFIED],
)
CASE_STATUS_UNASSIGNED: CaseStatusChoice = CaseStatusChoice(
    name="UNASSIGNED",
    value="000-unassigned-case",
    label="Unassigned case",
    test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
)
CASE_STATUSES: list[CaseStatusChoice] = [
    CASE_STATUS_UNASSIGNED,
    CaseStatusChoice(
        name="PSB_INFO_REQ",
        value="010-initial-psb-info-requested",
        label="Requested information",
        test_types=[TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="PSB_INFO_CHASING",
        value="020-initial-psb-info-chasing",
        label="Chasing initial response",
        test_types=[TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="PSB_INFO_REQ_ACK",
        value="030-initial-psb-info-req-ack",
        label="Acknowledged our request",
        test_types=[TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="PSB_INFO_RECEIVED",
        value="040-initial-psb-info-received",
        label="Received details and access",
        test_types=[TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="TEST_IN_PROGRESS",
        value="050-test-in-progress",
        label="Test in progress",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="REPORT_IN_PROGRESS",
        value="060-report-in-progress",
        label="Report in progress",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="READY_TO_QA",
        value="070-unassigned-qa-case",
        label="Report ready to QA",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="QA_IN_PROGRESS",
        value="080-qa-in-progress",
        label="QA in progress",
        test_types=[TestType.SIMPLIFIED],
    ),
    CaseStatusChoice(
        name="REPORT_READY_TO_SEND",
        value="090-report-ready-to-send",
        label="Report ready to send",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="IN_REPORT_CORES",
        value="100-in-report-correspondence",
        label="Report sent",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="AWAITING_REPORT_ACK",
        value="110-awaiting-report-ack",
        label="Waiting for report response",
        test_types=[TestType.DETAILED],
    ),
    CaseStatusChoice(
        name="AWAITING_12_WEEK_DEADLINE",
        value="120-in-12-week-period",
        label="Waiting for 12-week deadline",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="REQUESTED_12_WEEK_UPDATE",
        value="130-12-week-requested-update",
        label="Requested update at 12 weeks",
        test_types=[TestType.DETAILED],
    ),
    CaseStatusChoice(
        name="AFTER_12_WEEK_CORES",
        value="140-after-12-week-correspondence",
        label="After 12-week correspondence",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="REVIEWING_CHANGES",
        value="150-reviewing-changes",
        label="Reviewing changes",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="FINAL_DECISION_DUE",
        value="160-final-decision-due",
        label="Final decision due",
        test_types=[TestType.SIMPLIFIED],
    ),
    CaseStatusChoice(
        name="CASE_CLOSED_WAITING_TO_SEND",
        value="170-case-closed-waiting-to-be-sent",
        label="Waiting to be sent to equalities body",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY",
        value="180-case-closed-sent-to-equalities-body",
        label="Sent to equalities body",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="IN_CORES_WITH_ENFORCEMENT_BODY",
        value="190-in-correspondence-with-equalities-body",
        label="In correspondence with equalities body",
        test_types=[TestType.SIMPLIFIED],
    ),
    CaseStatusChoice(
        name="COMPLETE",
        value="200-complete",
        label="Complete",
        test_types=[TestType.SIMPLIFIED, TestType.DETAILED, TestType.MOBILE],
    ),
    CaseStatusChoice(
        name="BLOCKED",
        value="210-blocked",
        label="Blocked",
        test_types=[TestType.DETAILED],
    ),
    CaseStatusChoice(
        name="DEACTIVATED",
        value="900-deactivated",
        label="Deactivated",
        test_types=[TestType.SIMPLIFIED],
    ),
    CASE_STATUS_UNKNOWN,
]
ALL_CASE_STATUS_SEARCH_CHOICES: list[tuple[str, str]] = [
    (case_status.value, case_status.search_cases_choices_label)
    for case_status in CASE_STATUSES
]
ALL_CASE_STATUS_CHOICES: list[tuple[str, str]] = [
    (case_status.value, case_status.label) for case_status in CASE_STATUSES
]


class CaseStatusChoices:
    choices: list[tuple[str, str]] | None = None

    def __init__(self, test_type: str):
        self.choices = []
        for status in CASE_STATUSES:
            if test_type in status.test_types:
                setattr(self, status.name, status.value)
                self.choices.append((status.value, status.label))


SimplifiedCaseStatus: CaseStatusChoices | None = None
DetailedCaseStatus: CaseStatusChoices | None = None
MobileCaseStatus: CaseStatusChoices | None = None

if SimplifiedCaseStatus is None:
    SimplifiedCaseStatus: CaseStatusChoices | None = CaseStatusChoices(
        test_type=TestType.SIMPLIFIED
    )
if DetailedCaseStatus is None:
    DetailedCaseStatus: CaseStatusChoices = CaseStatusChoices(
        test_type=TestType.DETAILED
    )
if MobileCaseStatus is None:
    MobileCaseStatus: CaseStatusChoices = CaseStatusChoices(test_type=TestType.MOBILE)


class Complaint(models.TextChoices):
    ALL = "", "All"
    NO = "no", "No complaints"
    YES = "yes", "Only complaints"


class Sort(models.TextChoices):
    NEWEST = "", "Newest, Unassigned first"
    OLDEST = "id", "Oldest"
    NAME = "organisation_name", "Alphabetic"


class BaseCase(VersionModel):
    """
    Model for Case
    """

    TestType = TestType

    class PsbLocation(models.TextChoices):
        ENGLAND = "england", "England"
        SCOTLAND = "scotland", "Scotland"
        WALES = "wales", "Wales"
        NI = "northern_ireland", "Northern Ireland"
        UK = "uk_wide", "UK-wide or multiple countries"
        UNKNOWN = "unknown", "Unknown"

    class EnforcementBody(models.TextChoices):
        EHRC = "ehrc", "Equality and Human Rights Commission"
        ECNI = "ecni", "Equality Commission for Northern Ireland"

    class RecommendationForEnforcement(models.TextChoices):
        NO_FURTHER_ACTION = "no-further-action", "No further action"
        OTHER = "other", "For enforcement consideration"
        UNKNOWN = "unknown", "Not selected"

    CLOSED_CASE_STATUSES: list[str] = [
        SimplifiedCaseStatus.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
        SimplifiedCaseStatus.COMPLETE,
        SimplifiedCaseStatus.CASE_CLOSED_WAITING_TO_SEND,
        SimplifiedCaseStatus.IN_CORES_WITH_ENFORCEMENT_BODY,
        SimplifiedCaseStatus.DEACTIVATED,
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
        max_length=200,
        choices=ALL_CASE_STATUS_CHOICES,
        default=SimplifiedCaseStatus.UNASSIGNED,
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

    @property
    def name_prefix(self):
        name_prefix: str = self.website_name if self.website_name else self.domain
        return name_prefix

    @property
    def name_suffix(self):
        return self.organisation_name

    @property
    def full_name(self):
        return mark_safe(f"{self.name_prefix} &middot; {self.name_suffix}")

    @property
    def domain_clean(self):
        return self.domain.replace("www.", "")

    @property
    def reminder(self):
        return self.task_set.filter(type="reminder", read=False).first()

    @property
    def reminder_history(self):
        return self.task_set.filter(type="reminder", read=True)

    @property
    def qa_comments(self):
        return self.comment_basecase.filter(hidden=False).order_by("-created_date")

    @property
    def qa_comments_count(self):
        return self.qa_comments.count()

    def get_case(self):
        if self.test_type == TestType.SIMPLIFIED:
            return self.simplifiedcase
        if self.test_type == TestType.DETAILED:
            return self.detailedcase
        if self.test_type == TestType.MOBILE:
            return self.mobilecase
