""""
Models - cases
"""
import json
import re
from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import List, Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..common.models import (
    BOOLEAN_CHOICES,
    BOOLEAN_DEFAULT,
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    Sector,
    SubCategory,
    VersionModel,
)
from ..common.utils import (
    extract_domain_from_url,
    format_outstanding_issues,
    format_statement_check_overview,
)

STATUS_READY_TO_QA: str = "unassigned-qa-case"
STATUS_QA_IN_PROGRESS: str = "qa-in-progress"
STATUS_UNASSIGNED: str = "unassigned-case"
STATUS_DEFAULT: str = STATUS_UNASSIGNED
STATUS_DEACTIVATED: str = "deactivated"
STATUS_CHOICES: List[Tuple[str, str]] = [
    (
        "unknown",
        "Unknown",
    ),
    (
        STATUS_DEFAULT,
        "Unassigned case",
    ),
    (
        "test-in-progress",
        "Test in progress",
    ),
    (
        "report-in-progress",
        "Report in progress",
    ),
    (
        STATUS_READY_TO_QA,
        "Report ready to QA",
    ),
    (
        STATUS_QA_IN_PROGRESS,
        "QA in progress",
    ),
    (
        "report-ready-to-send",
        "Report ready to send",
    ),
    (
        "in-report-correspondence",
        "Report sent",
    ),
    (
        "in-probation-period",
        "Report acknowledged waiting for 12-week deadline",
    ),
    (
        "in-12-week-correspondence",
        "After 12-week correspondence",
    ),
    (
        "reviewing-changes",
        "Reviewing changes",
    ),
    (
        "final-decision-due",
        "Final decision due",
    ),
    (
        "case-closed-waiting-to-be-sent",
        "Case closed and waiting to be sent to equalities body",
    ),
    (
        "case-closed-sent-to-equalities-body",
        "Case closed and sent to equalities body",
    ),
    (
        "in-correspondence-with-equalities-body",
        "In correspondence with equalities body",
    ),
    (
        "complete",
        "Complete",
    ),
    (
        STATUS_DEACTIVATED,
        "Deactivated",
    ),
]

DEFAULT_TEST_TYPE: str = "simplified"
TEST_TYPE_CHOICES: List[Tuple[str, str]] = [
    (DEFAULT_TEST_TYPE, "Simplified"),
    ("detailed", "Detailed"),
    ("mobile", "Mobile"),
]

ENFORCEMENT_BODY_DEFAULT: str = "ehrc"
ENFORCEMENT_BODY_CHOICES: List[Tuple[str, str]] = [
    (ENFORCEMENT_BODY_DEFAULT, "Equality and Human Rights Commission"),
    ("ecni", "Equality Commission Northern Ireland"),
]

STATEMENT_COMPLIANCE_STATE_DEFAULT: str = "unknown"
STATEMENT_COMPLIANCE_STATE_COMPLIANT: str = "compliant"
STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT: str = "not-compliant"
STATEMENT_COMPLIANCE_STATE_NOT_FOUND: str = "not-found"
STATEMENT_COMPLIANCE_STATE_CHOICES: List[Tuple[str, str]] = [
    (STATEMENT_COMPLIANCE_STATE_COMPLIANT, "Compliant"),
    (STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT, "Not compliant"),
    (STATEMENT_COMPLIANCE_STATE_NOT_FOUND, "Not found"),
    ("other", "Other"),
    (STATEMENT_COMPLIANCE_STATE_DEFAULT, "Not selected"),
]

WEBSITE_COMPLIANCE_STATE_DEFAULT: str = "not-known"
WEBSITE_COMPLIANCE_STATE_COMPLIANT: str = "compliant"
WEBSITE_COMPLIANCE_STATE_CHOICES: List[Tuple[str, str]] = [
    (WEBSITE_COMPLIANCE_STATE_COMPLIANT, "Fully compliant"),
    ("partially-compliant", "Partially compliant"),
    (WEBSITE_COMPLIANCE_STATE_DEFAULT, "Not known"),
]

RECOMMENDATION_DEFAULT: str = "unknown"
RECOMMENDATION_NO_ACTION: str = "no-further-action"
RECOMMENDATION_CHOICES: List[Tuple[str, str]] = [
    (RECOMMENDATION_NO_ACTION, "No further action"),
    ("other", "For enforcement consideration"),
    (RECOMMENDATION_DEFAULT, "Not selected"),
]

REPORT_APPROVED_STATUS_DEFAULT: str = "not-started"
REPORT_APPROVED_STATUS_APPROVED: str = "yes"
REPORT_APPROVED_STATUS_CHOICES: List[Tuple[str, str]] = [
    (REPORT_APPROVED_STATUS_APPROVED, "Yes"),
    ("in-progress", "Further work is needed"),
    (REPORT_APPROVED_STATUS_DEFAULT, "Not started"),
]

TWELVE_WEEK_RESPONSE_DEFAULT = "not-selected"
TWELVE_WEEK_RESPONSE_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (TWELVE_WEEK_RESPONSE_DEFAULT, "Not selected"),
]

IS_DISPROPORTIONATE_CLAIMED_DEFAULT: str = "unknown"
IS_DISPROPORTIONATE_CLAIMED_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (IS_DISPROPORTIONATE_CLAIMED_DEFAULT, "Not known"),
]

DEFAULT_CASE_COMPLETED: str = "no-decision"
CASE_COMPLETED_SEND: str = "complete-send"
CASE_COMPLETED_NO_SEND: str = "complete-no-send"
CASE_COMPLETED_CHOICES: List[Tuple[str, str]] = [
    (CASE_COMPLETED_SEND, "Case is complete and is ready to send to the equality body"),
    (CASE_COMPLETED_NO_SEND, "Case should not be sent to the equality body"),
    (DEFAULT_CASE_COMPLETED, "Case still in progress"),
]

QA_STATUS_UNKNOWN: str = "unknown"
QA_STATUS_UNASSIGNED: str = "unassigned-qa-case"
QA_STATUS_IN_QA: str = "in-qa"
QA_STATUS_QA_APPROVED: str = "qa-approved"
QA_STATUS_CHOICES: List[Tuple[str, str]] = [
    (QA_STATUS_UNKNOWN, "Unknown"),
    (QA_STATUS_UNASSIGNED, "Unassigned QA case"),
    (QA_STATUS_IN_QA, "In QA"),
    (QA_STATUS_QA_APPROVED, "QA approved"),
]

ENFORCEMENT_BODY_PURSUING_NO: str = "no"
ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS: str = "yes-in-progress"
ENFORCEMENT_BODY_PURSUING_YES_COMPLETED: str = "yes-completed"
ENFORCEMENT_BODY_PURSUING_CHOICES: List[Tuple[str, str]] = [
    (ENFORCEMENT_BODY_PURSUING_YES_COMPLETED, "Yes, completed"),
    (ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS, "Yes, in progress"),
    (ENFORCEMENT_BODY_PURSUING_NO, "No"),
]
ENFORCEMENT_BODY_CLOSED_NO: str = "no"
ENFORCEMENT_BODY_CLOSED_IN_PROGRESS: str = "in-progress"
ENFORCEMENT_BODY_CLOSED_YES: str = "yes"
ENFORCEMENT_BODY_CLOSED_CHOICES: List[Tuple[str, str]] = [
    (ENFORCEMENT_BODY_CLOSED_YES, "Yes"),
    (ENFORCEMENT_BODY_CLOSED_IN_PROGRESS, "Case in progress"),
    (ENFORCEMENT_BODY_CLOSED_NO, "No (or holding)"),
]

PREFERRED_DEFAULT: str = "unknown"
PREFERRED_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (PREFERRED_DEFAULT, "Not known"),
]

PSB_LOCATION_DEFAULT: str = "unknown"
PSB_LOCATION_CHOICES: List[Tuple[str, str]] = [
    ("england", "England"),
    ("scotland", "Scotland"),
    ("wales", "Wales"),
    ("northern_ireland", "Northern Ireland"),
    ("uk_wide", "UK-wide"),
    (PSB_LOCATION_DEFAULT, "Unknown"),
]

MAX_LENGTH_OF_FORMATTED_URL = 25
PSB_APPEAL_WINDOW_IN_DAYS = 28

CASE_EVENT_TYPE_CREATE: str = "create"
CASE_EVENT_AUDITOR: str = "auditor"
CASE_EVENT_CREATE_AUDIT: str = "create_audit"
CASE_EVENT_CREATE_REPORT: str = "create_report"
CASE_EVENT_READY_FOR_QA: str = "ready_for_qa"
CASE_EVENT_QA_AUDITOR: str = "qa_auditor"
CASE_EVENT_APPROVE_REPORT: str = "approve_report"
CASE_EVENT_START_RETEST: str = "retest"
CASE_EVENT_READY_FOR_FINAL_DECISION: str = "read_for_final_decision"
CASE_EVENT_CASE_COMPLETED: str = "completed"
CASE_EVENT_TYPE_CHOICES: List[Tuple[str, str]] = [
    (CASE_EVENT_TYPE_CREATE, "Create"),
    (CASE_EVENT_AUDITOR, "Change of auditor"),
    (CASE_EVENT_CREATE_AUDIT, "Start test"),
    (CASE_EVENT_CREATE_REPORT, "Create report"),
    (CASE_EVENT_READY_FOR_QA, "Report readiness for QA"),
    (CASE_EVENT_QA_AUDITOR, "Change of QA auditor"),
    (CASE_EVENT_APPROVE_REPORT, "Report approval"),
    (CASE_EVENT_START_RETEST, "Start retest"),
    (CASE_EVENT_READY_FOR_FINAL_DECISION, "Ready for final decision"),
    (CASE_EVENT_CASE_COMPLETED, "Completed"),
]
CLOSED_CASE_STATUSES: List[str] = [
    "case-closed-sent-to-equalities-body",
    "complete",
    "case-closed-waiting-to-be-sent",
    "in-correspondence-with-equalities-body",
    "deactivated",
]
COMPLIANCE_FIELDS: List[str] = [
    "website_compliance_state_initial",
    "website_compliance_notes_initial",
    "statement_compliance_state_initial",
    "statement_compliance_notes_initial",
    "website_compliance_state_12_week",
    "website_compliance_notes_12_week",
    "statement_compliance_state_12_week",
    "statement_compliance_notes_12_week",
]

EQUALITY_BODY_CORRESPONDENCE_QUESTION: str = "question"
EQUALITY_BODY_CORRESPONDENCE_RETEST: str = "retest"
EQUALITY_BODY_CORRESPONDENCE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (EQUALITY_BODY_CORRESPONDENCE_QUESTION, "Question"),
    (EQUALITY_BODY_CORRESPONDENCE_RETEST, "Retest request"),
]
EQUALITY_BODY_CORRESPONDENCE_UNRESOLVED: str = "outstanding"
EQUALITY_BODY_CORRESPONDENCE_RESOLVED: str = "resolved"
EQUALITY_BODY_CORRESPONDENCE_STATUS_CHOICES: List[Tuple[str, str]] = [
    (EQUALITY_BODY_CORRESPONDENCE_UNRESOLVED, "Unresolved"),
    (EQUALITY_BODY_CORRESPONDENCE_RESOLVED, "Resolved"),
]
CASE_VARIANT_EQUALITY_BODY_CLOSE_CASE: str = "close-case"
CASE_VARIANT_CHOICES: List[Tuple[str, str]] = [
    (CASE_VARIANT_EQUALITY_BODY_CLOSE_CASE, "Equality Body Close Case"),
    ("statement-content", "Statement content yes/no"),
    ("reporting", "Platform reports"),
    ("archived", "Archived"),
]


class Case(VersionModel):
    """
    Model for Case
    """

    archive = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="case_created_by_user",
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(null=True, blank=True)
    variant = models.CharField(
        max_length=20,
        choices=CASE_VARIANT_CHOICES,
        default=CASE_VARIANT_EQUALITY_BODY_CLOSE_CASE,
    )

    # Case details page
    created = models.DateTimeField(blank=True)
    auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="case_auditor_user",
        blank=True,
        null=True,
    )
    test_type = models.CharField(
        max_length=10, choices=TEST_TYPE_CHOICES, default=DEFAULT_TEST_TYPE
    )
    home_page_url = models.TextField(default="", blank=True)
    domain = models.TextField(default="", blank=True)
    organisation_name = models.TextField(default="", blank=True)
    psb_location = models.CharField(
        max_length=20,
        choices=PSB_LOCATION_CHOICES,
        default=PSB_LOCATION_DEFAULT,
    )
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, null=True, blank=True)
    enforcement_body = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_BODY_CHOICES,
        default=ENFORCEMENT_BODY_DEFAULT,
    )
    is_complaint = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    previous_case_url = models.TextField(default="", blank=True)
    trello_url = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)
    parental_organisation_name = models.TextField(default="", blank=True)
    website_name = models.TextField(default="", blank=True)
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    case_details_complete_date = models.DateField(null=True, blank=True)

    # Historic testing details page
    test_results_url = models.TextField(default="", blank=True)
    testing_details_complete_date = models.DateField(null=True, blank=True)

    # Report details page
    report_draft_url = models.TextField(default="", blank=True)
    report_notes = models.TextField(default="", blank=True)
    reporting_details_complete_date = models.DateField(null=True, blank=True)

    # QA process
    report_review_status = models.CharField(
        max_length=200,
        choices=BOOLEAN_CHOICES,
        default=BOOLEAN_FALSE,
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="case_reviewer_user",
        blank=True,
        null=True,
    )
    report_approved_status = models.CharField(
        max_length=200,
        choices=REPORT_APPROVED_STATUS_CHOICES,
        default=REPORT_APPROVED_STATUS_DEFAULT,
    )
    reviewer_notes = models.TextField(default="", blank=True)
    report_final_pdf_url = models.TextField(default="", blank=True)
    report_final_odt_url = models.TextField(default="", blank=True)
    qa_process_complete_date = models.DateField(null=True, blank=True)

    # Contact details page
    contact_notes = models.TextField(default="", blank=True)
    contact_details_complete_date = models.DateField(null=True, blank=True)

    # Report correspondence page
    seven_day_no_contact_email_sent_date = models.DateField(null=True, blank=True)
    report_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_1_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_4_sent_date = models.DateField(null=True, blank=True)
    report_acknowledged_date = models.DateField(null=True, blank=True)
    zendesk_url = models.TextField(default="", blank=True)
    correspondence_notes = models.TextField(default="", blank=True)
    report_correspondence_complete_date = models.DateField(null=True, blank=True)

    # Report followup dates page
    report_followup_week_1_due_date = models.DateField(null=True, blank=True)
    report_followup_week_4_due_date = models.DateField(null=True, blank=True)
    report_followup_week_12_due_date = models.DateField(null=True, blank=True)

    # Unable to send report or no response from public sector body page
    no_psb_contact = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )

    # 12-week correspondence page
    twelve_week_update_requested_date = models.DateField(null=True, blank=True)
    twelve_week_1_week_chaser_sent_date = models.DateField(null=True, blank=True)
    twelve_week_correspondence_acknowledged_date = models.DateField(
        null=True, blank=True
    )
    twelve_week_correspondence_notes = models.TextField(default="", blank=True)
    twelve_week_response_state = models.CharField(
        max_length=20,
        choices=TWELVE_WEEK_RESPONSE_CHOICES,
        default=TWELVE_WEEK_RESPONSE_DEFAULT,
    )
    twelve_week_correspondence_complete_date = models.DateField(null=True, blank=True)

    # 12-week correspondence dates
    # report_followup_week_12_due_date from report followup dates page
    twelve_week_1_week_chaser_due_date = models.DateField(null=True, blank=True)

    # Twelve week retest
    twelve_week_retest_complete_date = models.DateField(null=True, blank=True)

    # Review changes
    psb_progress_notes = models.TextField(default="", blank=True)
    retested_website_date = models.DateField(null=True, blank=True)
    is_ready_for_final_decision = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    review_changes_complete_date = models.DateField(null=True, blank=True)

    # Final website
    final_website_complete_date = models.DateField(null=True, blank=True)

    # Final statement
    is_disproportionate_claimed = models.CharField(
        max_length=20,
        choices=IS_DISPROPORTIONATE_CLAIMED_CHOICES,
        default=IS_DISPROPORTIONATE_CLAIMED_DEFAULT,
    )
    disproportionate_notes = models.TextField(default="", blank=True)
    accessibility_statement_screenshot_url = models.TextField(default="", blank=True)
    final_statement_complete_date = models.DateField(null=True, blank=True)

    # Case close
    recommendation_for_enforcement = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
        default=RECOMMENDATION_DEFAULT,
    )
    recommendation_notes = models.TextField(default="", blank=True)
    compliance_email_sent_date = models.DateField(null=True, blank=True)
    case_completed = models.CharField(
        max_length=30, choices=CASE_COMPLETED_CHOICES, default=DEFAULT_CASE_COMPLETED
    )
    completed_date = models.DateTimeField(null=True, blank=True)
    case_close_complete_date = models.DateField(null=True, blank=True)

    # Post case/Statement enforcement
    psb_appeal_notes = models.TextField(default="", blank=True)
    post_case_notes = models.TextField(default="", blank=True)
    post_case_complete_date = models.DateField(null=True, blank=True)

    # Equality body pursuit page
    case_updated_date = models.DateField(null=True, blank=True)
    enforcement_body_pursuing = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_BODY_PURSUING_CHOICES,
        default=ENFORCEMENT_BODY_PURSUING_NO,
    )
    enforcement_body_correspondence_notes = models.TextField(default="", blank=True)
    enforcement_retest_document_url = models.TextField(default="", blank=True)
    is_feedback_requested = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    enforcement_correspondence_complete_date = models.DateField(null=True, blank=True)

    # Equality body metadata
    sent_to_enforcement_body_sent_date = models.DateField(null=True, blank=True)
    enforcement_body_case_owner = models.TextField(default="", blank=True)
    enforcement_body_closed_case = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_BODY_CLOSED_CHOICES,
        default=ENFORCEMENT_BODY_CLOSED_NO,
    )
    enforcement_body_finished_date = models.DateField(null=True, blank=True)

    # Deactivate case page
    is_deactivated = models.BooleanField(default=False)
    deactivate_date = models.DateField(null=True, blank=True)
    deactivate_notes = models.TextField(default="", blank=True)

    # Dashboard page
    qa_status = models.CharField(
        max_length=200, choices=QA_STATUS_CHOICES, default=QA_STATUS_UNKNOWN
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.organisation_name} | #{self.id}")

    def get_absolute_url(self) -> str:
        return reverse("cases:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs) -> None:
        new_case: bool = not self.id
        now: datetime = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.case_completed != DEFAULT_CASE_COMPLETED and not self.completed_date:
            self.completed_date = now
        self.qa_status = self.calulate_qa_status()
        self.updated = now
        super().save(*args, **kwargs)
        if new_case:
            CaseCompliance.objects.create(case=self)
            CaseStatus.objects.create(case=self)
        else:
            self.status.calculate_and_save_status()

    @property
    def formatted_home_page_url(self) -> str:
        if self.home_page_url:
            formatted_url = re.sub(r"https?://(www[0-9]?\.|)", "", self.home_page_url)
            if len(formatted_url) <= MAX_LENGTH_OF_FORMATTED_URL:
                return formatted_url[:-1] if formatted_url[-1] == "/" else formatted_url
            return f"{formatted_url[:MAX_LENGTH_OF_FORMATTED_URL]}…"
        return ""

    @property
    def title(self) -> str:
        title: str = ""
        if self.website_name:
            title += f"{self.website_name} | "
        title += (
            f"{self.organisation_name} | {self.formatted_home_page_url} | #{self.id}"
        )
        return title

    @property
    def next_action_due_date(self) -> Optional[date]:
        if self.status.status == "report-ready-to-send":
            if self.seven_day_no_contact_email_sent_date:
                return self.seven_day_no_contact_email_sent_date + timedelta(days=7)

        if self.status.status == "in-report-correspondence":
            if self.report_followup_week_1_sent_date is None:
                return self.report_followup_week_1_due_date
            elif self.report_followup_week_4_sent_date is None:
                return self.report_followup_week_4_due_date
            elif self.report_followup_week_4_sent_date:
                return self.report_followup_week_4_sent_date + timedelta(days=5)
            raise Exception(
                "Case is in-report-correspondence but neither sent date is set"
            )

        if self.status.status == "in-probation-period":
            return self.report_followup_week_12_due_date

        if self.status.status == "in-12-week-correspondence":
            if self.twelve_week_1_week_chaser_sent_date is None:
                return self.twelve_week_1_week_chaser_due_date
            return self.twelve_week_1_week_chaser_sent_date + timedelta(days=5)

        return date(1970, 1, 1)

    @property
    def next_action_due_date_tense(self) -> str:
        today: date = date.today()
        if self.next_action_due_date and self.next_action_due_date < today:
            return "past"
        if self.next_action_due_date == today:
            return "present"
        return "future"

    @property
    def reminder(self):
        return self.reminder_case.filter(is_deleted=False).first()

    @property
    def qa_comments(self):
        return self.comment_case.filter(hidden=False).order_by("-created_date")

    def calulate_qa_status(self) -> str:
        if (
            self.reviewer is None
            and self.report_review_status == BOOLEAN_TRUE
            and self.report_approved_status != REPORT_APPROVED_STATUS_APPROVED
        ):
            return QA_STATUS_UNASSIGNED
        elif (
            self.report_review_status == BOOLEAN_TRUE
            and self.report_approved_status != REPORT_APPROVED_STATUS_APPROVED
        ):
            return QA_STATUS_IN_QA
        elif (
            self.report_review_status == BOOLEAN_TRUE
            and self.report_approved_status == REPORT_APPROVED_STATUS_APPROVED
        ):
            return QA_STATUS_QA_APPROVED
        return QA_STATUS_UNKNOWN

    def set_statement_compliance_states(self) -> None:
        if self.audit:
            old_statement_compliance_state_initial: str = (
                self.compliance.statement_compliance_state_initial
            )
            old_statement_compliance_state_12_week: str = (
                self.compliance.statement_compliance_state_12_week
            )
            new_statement_compliance_state_initial: str = (
                old_statement_compliance_state_initial
            )
            new_statement_compliance_state_12_week: str = (
                old_statement_compliance_state_12_week
            )
            if self.audit.accessibility_statement_initially_found:
                if self.audit.uses_statement_checks:
                    if self.audit.failed_statement_check_results.count() > 0:
                        new_statement_compliance_state_initial = (
                            STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
                        )
                    else:
                        new_statement_compliance_state_initial = (
                            STATEMENT_COMPLIANCE_STATE_COMPLIANT
                        )
            else:
                new_statement_compliance_state_initial = (
                    STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
                )
            if (
                self.audit.accessibility_statement_initially_found
                or self.audit.twelve_week_accessibility_statement_found
            ):
                if self.audit.uses_statement_checks:
                    if self.audit.failed_retest_statement_check_results.count() > 0:
                        new_statement_compliance_state_12_week = (
                            STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
                        )
                    else:
                        new_statement_compliance_state_12_week = (
                            STATEMENT_COMPLIANCE_STATE_COMPLIANT
                        )
            else:
                new_statement_compliance_state_12_week = (
                    STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
                )
            if (
                old_statement_compliance_state_initial
                != new_statement_compliance_state_initial
                or old_statement_compliance_state_12_week
                != new_statement_compliance_state_12_week
            ):
                self.compliance.statement_compliance_state_initial = (
                    new_statement_compliance_state_initial
                )
                self.compliance.statement_compliance_state_12_week = (
                    new_statement_compliance_state_12_week
                )
                self.compliance.save()
                self.save()

    @property
    def in_report_correspondence_progress(self) -> str:
        now: date = date.today()
        seven_days_ago = now - timedelta(days=7)
        if (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date > now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1-week followup to report coming up"
        elif (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date <= now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1-week followup to report due"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date > now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4-week followup to report coming up"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date <= now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4-week followup to report due"
        elif (
            self.report_followup_week_4_sent_date is not None
            and self.report_followup_week_4_sent_date > seven_days_ago
        ):
            return "4-week followup to report sent, waiting five days for response"
        elif (
            self.report_followup_week_4_sent_date is not None
            and self.report_followup_week_4_sent_date <= seven_days_ago
        ):
            return "4-week followup to report sent, case needs to progress"
        return "Unknown"

    @property
    def twelve_week_correspondence_progress(self) -> str:
        now: date = date.today()
        seven_days_ago = now - timedelta(days=5)
        if (
            self.twelve_week_1_week_chaser_due_date
            and self.twelve_week_1_week_chaser_due_date > now
            and self.twelve_week_1_week_chaser_sent_date is None
        ):
            return "1-week followup coming up"
        elif (
            self.twelve_week_update_requested_date
            and self.twelve_week_update_requested_date < now
            and self.twelve_week_1_week_chaser_sent_date is None
        ):
            return "1-week followup due"
        elif (
            self.twelve_week_1_week_chaser_sent_date is not None
            and self.twelve_week_1_week_chaser_sent_date > seven_days_ago
        ):
            return "1-week followup sent, waiting five days for response"
        elif (
            self.twelve_week_1_week_chaser_sent_date is not None
            and self.twelve_week_1_week_chaser_sent_date <= seven_days_ago
        ):
            return "1-week followup sent, case needs to progress"
        return "Unknown"

    @property
    def contact_exists(self) -> bool:
        return Contact.objects.filter(case_id=self.id).exists()

    @property
    def psb_appeal_deadline(self) -> Optional[date]:
        if self.compliance_email_sent_date is None:
            return None
        return self.compliance_email_sent_date + timedelta(
            days=PSB_APPEAL_WINDOW_IN_DAYS
        )

    @property
    def psb_response(self) -> bool:
        return self.no_psb_contact == BOOLEAN_FALSE

    @property
    def audit(self):
        try:
            return self.audit_case
        except ObjectDoesNotExist:
            return None

    @property
    def report(self):
        try:
            return self.report_case
        except ObjectDoesNotExist:
            return None

    @property
    def published_report_url(self):
        if self.report and self.report.latest_s3_report:
            return f"{settings.AMP_PROTOCOL}{settings.AMP_VIEWER_DOMAIN}/reports/{self.report.latest_s3_report.guid}"
        else:
            return ""

    @property
    def previous_case_number(self):
        result = re.search(r".*/cases/(\d+)/view.*", self.previous_case_url)
        if result:
            return result.group(1)
        return None

    @property
    def last_edited(self):
        """Return when case or related data was last changed"""
        updated_times: List[Optional[datetime]] = [self.created, self.updated]

        for contact in self.contact_set.all():
            updated_times.append(contact.created)
            updated_times.append(contact.updated)

        if self.audit is not None:
            updated_times.append(
                datetime(
                    self.audit.date_of_test.year,
                    self.audit.date_of_test.month,
                    self.audit.date_of_test.day,
                    tzinfo=datetime_timezone.utc,
                )
            )
            updated_times.append(self.audit.updated)
            for page in self.audit.page_audit.all():
                updated_times.append(page.updated)
            for check_result in self.audit.checkresult_audit.all():
                updated_times.append(check_result.updated)

        for comment in self.comment_case.all():
            updated_times.append(comment.created_date)
            updated_times.append(comment.updated)

        for reminder in self.reminder_case.all():
            updated_times.append(reminder.updated)

        if self.report is not None:
            updated_times.append(self.report.updated)

        for s3_report in self.s3report_set.all():
            updated_times.append(s3_report.created)

        return max([updated for updated in updated_times if updated is not None])

    @property
    def website_compliance_display(self):
        if (
            self.compliance.website_compliance_state_12_week
            == WEBSITE_COMPLIANCE_STATE_DEFAULT
        ):
            return self.compliance.get_website_compliance_state_initial_display()
        return self.compliance.get_website_compliance_state_12_week_display()

    @property
    def accessibility_statement_compliance_display(self):
        if (
            self.compliance.statement_compliance_state_12_week
            == STATEMENT_COMPLIANCE_STATE_DEFAULT
        ):
            return self.compliance.get_statement_compliance_state_initial_display()
        return self.compliance.get_statement_compliance_state_12_week_display()

    @property
    def percentage_website_issues_fixed(self) -> int:
        if self.audit is None:
            return "n/a"
        failed_checks_count: int = self.audit.failed_check_results.count()
        if failed_checks_count == 0:
            return "n/a"
        fixed_checks_count: int = self.audit.fixed_check_results.count()
        return int(fixed_checks_count * 100 / failed_checks_count)

    @property
    def overview_issues_website(self) -> str:
        if self.audit is None:
            return "No test exists"
        return format_outstanding_issues(
            failed_checks_count=self.audit.failed_check_results.count(),
            fixed_checks_count=self.audit.fixed_check_results.count(),
        )

    @property
    def overview_issues_statement(self) -> str:
        if self.audit is None:
            return "No test exists"
        if self.audit.uses_statement_checks:
            return format_statement_check_overview(
                tests_passed=self.audit.passed_statement_check_results.count(),
                tests_failed=self.audit.failed_statement_check_results.count(),
                retests_passed=self.audit.passed_retest_statement_check_results.count(),
                retests_failed=self.audit.failed_retest_statement_check_results.count(),
            )
        return format_outstanding_issues(
            failed_checks_count=self.audit.accessibility_statement_initially_invalid_checks_count,
            fixed_checks_count=self.audit.fixed_accessibility_statement_checks_count,
        )

    @property
    def statement_checks_still_initial(self):
        if self.audit and self.audit.uses_statement_checks:
            return not self.audit.overview_statement_checks_complete
        return (
            self.compliance.statement_compliance_state_initial
            == STATEMENT_COMPLIANCE_STATE_DEFAULT
        )

    @property
    def archived_sections(self):
        if self.archive:
            archive = json.loads(self.archive)
        else:
            return None
        return archive["sections"] if "sections" in archive else None

    @property
    def retests(self):
        return self.retest_set.filter(is_deleted=False)

    @property
    def number_retests(self):
        return self.retest_set.filter(is_deleted=False, id_within_case__gt=0).count()

    @property
    def incomplete_retests(self):
        return self.retests.filter(retest_compliance_state="not-known")

    @property
    def latest_retest(self):
        return self.retests.first()

    @property
    def equality_body_correspondences(self):
        return self.equalitybodycorrespondence_set.filter(is_deleted=False)

    @property
    def equality_body_questions(self):
        return self.equality_body_correspondences.filter(
            type=EQUALITY_BODY_CORRESPONDENCE_QUESTION
        )

    @property
    def equality_body_questions_unresolved(self):
        return self.equality_body_correspondences.filter(
            type=EQUALITY_BODY_CORRESPONDENCE_QUESTION,
            status=EQUALITY_BODY_CORRESPONDENCE_UNRESOLVED,
        )

    @property
    def equality_body_correspondence_retests(self):
        return self.equality_body_correspondences.filter(
            type=EQUALITY_BODY_CORRESPONDENCE_RETEST
        )

    @property
    def equality_body_correspondence_retests_unresolved(self):
        return self.equality_body_correspondences.filter(
            type=EQUALITY_BODY_CORRESPONDENCE_RETEST,
            status=EQUALITY_BODY_CORRESPONDENCE_UNRESOLVED,
        )


class CaseStatus(models.Model):
    """
    Model for case status
    """

    case = models.OneToOneField(Case, on_delete=models.PROTECT, related_name="status")
    status = models.CharField(
        max_length=200, choices=STATUS_CHOICES, default=STATUS_DEFAULT
    )

    class Meta:
        verbose_name_plural = "Case statuses"

    def save(self, *args, **kwargs) -> None:
        self.status = self.calculate_status()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.status

    def calculate_and_save_status(self) -> None:
        self.status = self.calculate_status()
        self.save()

    def calculate_status(self) -> str:  # noqa: C901
        try:
            compliance: CaseCompliance = self.case.compliance
        except CaseCompliance.DoesNotExist:
            compliance = None

        if self.case.is_deactivated:
            return STATUS_DEACTIVATED
        elif (
            self.case.case_completed == CASE_COMPLETED_NO_SEND
            or self.case.enforcement_body_pursuing
            == ENFORCEMENT_BODY_PURSUING_YES_COMPLETED
            or self.case.enforcement_body_closed_case == ENFORCEMENT_BODY_CLOSED_YES
        ):
            return "complete"
        elif (
            self.case.enforcement_body_pursuing
            == ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS
            or self.case.enforcement_body_closed_case
            == ENFORCEMENT_BODY_CLOSED_IN_PROGRESS
        ):
            return "in-correspondence-with-equalities-body"
        elif self.case.sent_to_enforcement_body_sent_date is not None:
            return "case-closed-sent-to-equalities-body"
        elif self.case.case_completed == "complete-send":
            return "case-closed-waiting-to-be-sent"
        elif self.case.no_psb_contact == "yes":
            return "final-decision-due"
        elif self.case.auditor is None:
            return "unassigned-case"
        elif (
            compliance is None
            or self.case.compliance.website_compliance_state_initial
            == WEBSITE_COMPLIANCE_STATE_DEFAULT
            or self.case.statement_checks_still_initial
        ):
            return "test-in-progress"
        elif (
            self.case.compliance.website_compliance_state_initial
            != WEBSITE_COMPLIANCE_STATE_DEFAULT
            and not self.case.statement_checks_still_initial
            and self.case.report_review_status != BOOLEAN_TRUE
        ):
            return "report-in-progress"
        elif (
            self.case.report_review_status == BOOLEAN_TRUE
            and self.case.report_approved_status != REPORT_APPROVED_STATUS_APPROVED
        ):
            return STATUS_QA_IN_PROGRESS
        elif (
            self.case.report_approved_status == REPORT_APPROVED_STATUS_APPROVED
            and self.case.report_sent_date is None
        ):
            return "report-ready-to-send"
        elif self.case.report_sent_date and self.case.report_acknowledged_date is None:
            return "in-report-correspondence"
        elif (
            self.case.report_acknowledged_date
            and self.case.twelve_week_update_requested_date is None
        ):
            return "in-probation-period"
        elif self.case.twelve_week_update_requested_date and (
            self.case.twelve_week_correspondence_acknowledged_date is None
            and self.case.twelve_week_response_state == TWELVE_WEEK_RESPONSE_DEFAULT
        ):
            return "in-12-week-correspondence"
        elif (
            self.case.twelve_week_correspondence_acknowledged_date
            or self.case.twelve_week_response_state != TWELVE_WEEK_RESPONSE_DEFAULT
        ) and self.case.is_ready_for_final_decision == BOOLEAN_FALSE:
            return "reviewing-changes"
        elif (
            self.case.is_ready_for_final_decision == BOOLEAN_TRUE
            and self.case.case_completed == DEFAULT_CASE_COMPLETED
        ):
            return "final-decision-due"
        return "unknown"


class CaseCompliance(VersionModel):
    """
    Model for website and accessibility statement compliance
    """

    case = models.OneToOneField(
        Case, on_delete=models.PROTECT, related_name="compliance"
    )
    website_compliance_state_initial = models.CharField(
        max_length=20,
        choices=WEBSITE_COMPLIANCE_STATE_CHOICES,
        default=WEBSITE_COMPLIANCE_STATE_DEFAULT,
    )
    website_compliance_notes_initial = models.TextField(default="", blank=True)
    statement_compliance_state_initial = models.CharField(
        max_length=200,
        choices=STATEMENT_COMPLIANCE_STATE_CHOICES,
        default=STATEMENT_COMPLIANCE_STATE_DEFAULT,
    )
    statement_compliance_notes_initial = models.TextField(default="", blank=True)
    website_compliance_state_12_week = models.CharField(
        max_length=200,
        choices=WEBSITE_COMPLIANCE_STATE_CHOICES,
        default=WEBSITE_COMPLIANCE_STATE_DEFAULT,
    )
    website_compliance_notes_12_week = models.TextField(default="", blank=True)
    statement_compliance_state_12_week = models.CharField(
        max_length=200,
        choices=STATEMENT_COMPLIANCE_STATE_CHOICES,
        default=STATEMENT_COMPLIANCE_STATE_DEFAULT,
    )
    statement_compliance_notes_12_week = models.TextField(default="", blank=True)

    def __str__(self) -> str:
        return (
            f"Website: {self.get_website_compliance_state_initial_display()}->"
            f"{self.get_website_compliance_state_12_week_display()}; "
            f"Statement: {self.get_statement_compliance_state_initial_display()}->"
            f"{self.get_statement_compliance_state_12_week_display()}"
        )


class Contact(models.Model):
    """
    Model for cases Contact
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    name = models.TextField(default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    email = models.CharField(max_length=200, default="", blank=True)
    preferred = models.CharField(
        max_length=20, choices=PREFERRED_CHOICES, default=PREFERRED_DEFAULT
    )
    created = models.DateTimeField()
    updated = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-preferred", "-id"]

    def __str__(self) -> str:
        return str(f"Contact {self.name} {self.email}")

    def get_absolute_url(self) -> str:
        return reverse("cases:edit-contact-details", kwargs={"pk": self.case.id})

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        if not self.id:
            self.created = timezone.now()
        super().save(*args, **kwargs)


class CaseEvent(models.Model):
    """
    Model to records events on a case
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=100, choices=CASE_EVENT_TYPE_CHOICES, default=CASE_EVENT_TYPE_CREATE
    )
    message = models.TextField(default="Created case", blank=True)
    done_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="case_event_done_by_user",
    )
    event_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event_time"]

    def __str__(self) -> str:
        return str(f"{self.case.organisation_name}: {self.message}")


class EqualityBodyCorrespondence(models.Model):
    """
    Model for cases equality body correspondence
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=1, blank=True)
    type = models.CharField(
        max_length=20,
        choices=EQUALITY_BODY_CORRESPONDENCE_TYPE_CHOICES,
        default=EQUALITY_BODY_CORRESPONDENCE_QUESTION,
    )
    message = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)
    zendesk_url = models.TextField(default="", blank=True)
    status = models.CharField(
        max_length=20,
        choices=EQUALITY_BODY_CORRESPONDENCE_STATUS_CHOICES,
        default=EQUALITY_BODY_CORRESPONDENCE_UNRESOLVED,
    )
    created = models.DateTimeField()
    updated = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"Equality body correspondence #{self.id_within_case}")

    def get_absolute_url(self) -> str:
        return reverse(
            "cases:list-equality-body-correspondence", kwargs={"pk": self.case.id}
        )

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        if not self.id:
            self.created = timezone.now()
            self.id_within_case = (
                self.case.equalitybodycorrespondence_set.all().count() + 1
            )
        super().save(*args, **kwargs)
