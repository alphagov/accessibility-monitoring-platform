"""
Models - cases
"""
from datetime import date, timedelta
import re
from typing import Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..common.utils import extract_domain_from_url
from ..common.models import (
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    Sector,
    VersionModel,
    BOOLEAN_CHOICES,
    BOOLEAN_DEFAULT,
)

STATUS_READY_TO_QA: str = "unassigned-qa-case"
STATUS_DEFAULT: str = "unassigned-case"
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
        "qa-in-progress",
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
        "Report acknowledged waiting for 12 week deadline",
    ),
    (
        "in-12-week-correspondence",
        "After 12 week correspondence",
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
        "deleted",
        "Deleted",
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

TESTING_METHODOLOGY_PLATFORM: str = "platform"
TESTING_METHODOLOGY_DEFAULT: str = "spreadsheet"
TESTING_METHODOLOGY_CHOICES: List[Tuple[str, str]] = [
    (TESTING_METHODOLOGY_PLATFORM, "Platform"),
    (TESTING_METHODOLOGY_DEFAULT, "Testing spreadsheet"),
]

REPORT_METHODOLOGY_PLATFORM: str = "platform"
REPORT_METHODOLOGY_DEFAULT: str = "odt"
REPORT_METHODOLOGY_CHOICES: List[Tuple[str, str]] = [
    (
        REPORT_METHODOLOGY_PLATFORM,
        "Platform (requires Platform in testing methodology)",
    ),
    (REPORT_METHODOLOGY_DEFAULT, "ODT templates"),
]

TEST_STATUS_DEFAULT: str = "not-started"
TEST_STATUS_COMPLETE: str = "complete"
TEST_STATUS_CHOICES: List[Tuple[str, str]] = [
    (TEST_STATUS_COMPLETE, "Complete"),
    ("in-progress", "In progress"),
    (TEST_STATUS_DEFAULT, "Not started"),
]

ACCESSIBILITY_STATEMENT_DECISION_DEFAULT: str = "unknown"
ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT: str = "compliant"
ACCESSIBILITY_STATEMENT_DECISION_CHOICES: List[Tuple[str, str]] = [
    (ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT, "Compliant"),
    ("not-compliant", "Not compliant"),
    ("not-found", "Not found"),
    ("other", "Other"),
    (ACCESSIBILITY_STATEMENT_DECISION_DEFAULT, "Not selected"),
]

IS_WEBSITE_COMPLIANT_DEFAULT: str = "unknown"
IS_WEBSITE_COMPLIANT_COMPLIANT: str = "compliant"
IS_WEBSITE_COMPLIANT_CHOICES: List[Tuple[str, str]] = [
    (IS_WEBSITE_COMPLIANT_COMPLIANT, "Compliant"),
    ("not-compliant", "Not compliant"),
    ("partially-compliant", "Partially compliant"),
    ("other", "Other"),
    (IS_WEBSITE_COMPLIANT_DEFAULT, "Not selected"),
]

RECOMMENDATION_DEFAULT: str = "unknown"
RECOMMENDATION_NO_ACTION: str = "no-further-action"
RECOMMENDATION_CHOICES: List[Tuple[str, str]] = [
    (RECOMMENDATION_NO_ACTION, "No further action"),
    ("other", "No recommendation made"),
    (RECOMMENDATION_DEFAULT, "Not selected"),
]

REPORT_REVIEW_STATUS_DEFAULT: str = "not-started"
REPORT_READY_TO_REVIEW = "ready-to-review"
REPORT_REVIEW_STATUS_CHOICES: List[Tuple[str, str]] = [
    (REPORT_READY_TO_REVIEW, "Yes"),
    ("in-progress", "In progress"),
    (REPORT_REVIEW_STATUS_DEFAULT, "Not started"),
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

WEBSITE_STATE_FINAL_DEFAULT: str = "not-known"
WEBSITE_STATE_FINAL_CHOICES: List[Tuple[str, str]] = [
    ("compliant", "Compliant"),
    ("partially-compliant", "Partially compliant"),
    (WEBSITE_STATE_FINAL_DEFAULT, "Not known"),
]

DEFAULT_CASE_COMPLETED: str = "no-decision"
CASE_COMPLETED_SEND: str = "complete-send"
CASE_COMPLETED_NO_SEND: str = "complete-no-send"
CASE_COMPLETED_CHOICES: List[Tuple[str, str]] = [
    (CASE_COMPLETED_SEND, "Case is complete and is ready to send to the equality body"),
    (CASE_COMPLETED_NO_SEND, "Case should not be sent to the equality body"),
    (DEFAULT_CASE_COMPLETED, "Case still in progress"),
]

DEFAULT_ESCALATION_STATE: str = "not-started"
ESCALATION_STATE_NO_ACTION: str = "no-action"
ESCALATION_STATE_CHOICES: List[Tuple[str, str]] = [
    (
        ESCALATION_STATE_NO_ACTION,
        "No further action is required and correspondence has closed regarding this issue",
    ),
    ("ongoing", "Correspondence ongoing"),
    (DEFAULT_ESCALATION_STATE, "Not started"),
]

DELETE_DECISION_DEFAULT: str = "not-psb"
DELETE_DECISION_CHOICES: List[Tuple[str, str]] = [
    (DELETE_DECISION_DEFAULT, "Organisation is not a public sector body"),
    ("mistake", "Case was opened by mistake"),
    ("duplicate", "This case was a duplicate case"),
    ("other", "Other"),
]

QA_STATUS_DEFAULT: str = "unknown"
QA_STATUS_CHOICES: List[Tuple[str, str]] = [
    (QA_STATUS_DEFAULT, "Unknown"),
    ("unassigned_qa_case", "Unassigned QA case"),
    ("in_qa", "In QA"),
    ("qa_approved", "QA approved"),
]

ENFORCEMENT_BODY_INTERESTED_DEFAULT: str = "not-selected"
ENFORCEMENT_BODY_INTERESTED_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (ENFORCEMENT_BODY_INTERESTED_DEFAULT, "Not selected"),
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


class Case(VersionModel):
    """
    Model for Case
    """

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="case_created_by_user",
        blank=True,
        null=True,
    )

    # Case details page
    created = models.DateTimeField(blank=True)
    status = models.CharField(
        max_length=200, choices=STATUS_CHOICES, default=STATUS_DEFAULT
    )
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
    testing_methodology = models.CharField(
        max_length=20,
        choices=TESTING_METHODOLOGY_CHOICES,
        default=TESTING_METHODOLOGY_DEFAULT,
    )
    report_methodology = models.CharField(
        max_length=20,
        choices=REPORT_METHODOLOGY_CHOICES,
        default=REPORT_METHODOLOGY_DEFAULT,
    )
    is_complaint = models.CharField(
        max_length=20, choices=BOOLEAN_CHOICES, default=BOOLEAN_DEFAULT
    )
    trello_url = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)
    case_details_complete_date = models.DateField(null=True, blank=True)

    # Testing details page
    test_results_url = models.TextField(default="", blank=True)
    test_status = models.CharField(
        max_length=200, choices=TEST_STATUS_CHOICES, default=TEST_STATUS_DEFAULT
    )
    accessibility_statement_state = models.CharField(
        max_length=200,
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        default=ACCESSIBILITY_STATEMENT_DECISION_DEFAULT,
    )
    accessibility_statement_notes = models.TextField(default="", blank=True)
    is_website_compliant = models.CharField(
        max_length=20,
        choices=IS_WEBSITE_COMPLIANT_CHOICES,
        default=IS_WEBSITE_COMPLIANT_DEFAULT,
    )
    compliance_decision_notes = models.TextField(default="", blank=True)
    testing_details_complete_date = models.DateField(null=True, blank=True)

    # Report details page
    report_draft_url = models.TextField(default="", blank=True)
    report_notes = models.TextField(default="", blank=True)
    reporting_details_complete_date = models.DateField(null=True, blank=True)

    # QA process
    report_review_status = models.CharField(
        max_length=200,
        choices=REPORT_REVIEW_STATUS_CHOICES,
        default=REPORT_REVIEW_STATUS_DEFAULT,
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
    contact_details_complete_date = models.DateField(null=True, blank=True)

    # Report correspondence page
    published_report_sent = models.ForeignKey(
        "reports.PublishedReport",
        on_delete=models.PROTECT,
        related_name="case_published_report_sent",
        blank=True,
        null=True,
    )
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
    twelve_week_4_week_chaser_due_date = models.DateField(null=True, blank=True)

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
    website_state_final = models.CharField(
        max_length=200,
        choices=WEBSITE_STATE_FINAL_CHOICES,
        default=WEBSITE_STATE_FINAL_DEFAULT,
    )
    website_state_notes_final = models.TextField(default="", blank=True)
    final_website_complete_date = models.DateField(null=True, blank=True)

    # Final statement
    is_disproportionate_claimed = models.CharField(
        max_length=20,
        choices=IS_DISPROPORTIONATE_CLAIMED_CHOICES,
        default=IS_DISPROPORTIONATE_CLAIMED_DEFAULT,
    )
    disproportionate_notes = models.TextField(default="", blank=True)
    accessibility_statement_screenshot_url = models.TextField(default="", blank=True)
    accessibility_statement_state_final = models.CharField(
        max_length=200,
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        default=ACCESSIBILITY_STATEMENT_DECISION_DEFAULT,
    )
    accessibility_statement_notes_final = models.TextField(default="", blank=True)
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

    # Post case
    psb_appeal_notes = models.TextField(default="", blank=True)
    post_case_notes = models.TextField(default="", blank=True)
    post_case_complete_date = models.DateField(null=True, blank=True)

    # Equality body correspondence page
    case_updated_date = models.DateField(null=True, blank=True)
    sent_to_enforcement_body_sent_date = models.DateField(null=True, blank=True)
    enforcement_body_interested = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_BODY_INTERESTED_CHOICES,
        default=ENFORCEMENT_BODY_INTERESTED_DEFAULT,
    )
    enforcement_body_correspondence_notes = models.TextField(default="", blank=True)
    escalation_state = models.CharField(
        max_length=20,
        choices=ESCALATION_STATE_CHOICES,
        default=DEFAULT_ESCALATION_STATE,
    )
    enforcement_correspondence_complete_date = models.DateField(null=True, blank=True)

    # Delete case page
    is_deleted = models.BooleanField(default=False)
    delete_reason = models.CharField(
        max_length=20,
        choices=DELETE_DECISION_CHOICES,
        default=DELETE_DECISION_DEFAULT,
    )
    delete_notes = models.TextField(default="", blank=True)

    # Suspended case page
    is_suspended = models.BooleanField(default=False)
    suspend_date = models.DateField(null=True, blank=True)
    suspend_notes = models.TextField(default="", blank=True)

    # Dashboard page
    qa_status = models.CharField(
        max_length=200, choices=QA_STATUS_CHOICES, default=QA_STATUS_DEFAULT
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.organisation_name} | #{self.id}")  # type: ignore

    def get_absolute_url(self) -> str:
        return reverse("cases:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.case_completed != DEFAULT_CASE_COMPLETED and not self.completed_date:
            self.completed_date = now
        self.status = self.set_status()
        self.qa_status = self.set_qa_status()
        super().save(*args, **kwargs)

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
        return str(f"{self.organisation_name} | {self.formatted_home_page_url} | #{self.id}")  # type: ignore

    @property
    def next_action_due_date(self) -> Optional[date]:
        if self.status == "in-report-correspondence":
            if self.report_followup_week_1_sent_date is None:
                return self.report_followup_week_1_due_date
            elif self.report_followup_week_4_sent_date is None:
                return self.report_followup_week_4_due_date
            elif self.report_followup_week_4_sent_date:
                return self.report_followup_week_4_sent_date + timedelta(days=5)
            raise Exception(
                "Case is in-report-correspondence but neither sent date is set"
            )

        if self.status == "in-probation-period":
            return self.report_followup_week_12_due_date

        if self.status == "in-12-week-correspondence":
            if self.twelve_week_1_week_chaser_sent_date is None:
                return self.twelve_week_1_week_chaser_due_date
            return self.twelve_week_4_week_chaser_due_date

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
        return self.reminder_case.filter(is_deleted=False).first()  # type: ignore

    def set_status(self) -> str:  # noqa: C901
        if self.is_deleted:
            return "deleted"
        elif (
            self.case_completed == "complete-no-send"
            or self.escalation_state == "no-action"
        ):
            return "complete"
        elif self.enforcement_body_interested == "yes":
            return "in-correspondence-with-equalities-body"
        elif self.sent_to_enforcement_body_sent_date is not None:
            return "case-closed-sent-to-equalities-body"
        elif self.no_psb_contact == "yes" or self.case_completed == "complete-send":
            return "case-closed-waiting-to-be-sent"
        elif self.auditor is None:
            return "unassigned-case"
        elif (
            self.is_website_compliant == IS_WEBSITE_COMPLIANT_DEFAULT
            or self.accessibility_statement_state
            == ACCESSIBILITY_STATEMENT_DECISION_DEFAULT
        ):
            return "test-in-progress"
        elif (
            self.is_website_compliant != IS_WEBSITE_COMPLIANT_DEFAULT
            and self.accessibility_statement_state
            != ACCESSIBILITY_STATEMENT_DECISION_DEFAULT
            and self.report_review_status != "ready-to-review"
        ):
            return "report-in-progress"
        elif (
            self.report_review_status == "ready-to-review"
            and self.report_approved_status != "yes"
        ):
            return "qa-in-progress"
        elif self.report_approved_status == "yes" and self.report_sent_date is None:
            return "report-ready-to-send"
        elif self.report_sent_date and self.report_acknowledged_date is None:
            return "in-report-correspondence"
        elif (
            self.report_acknowledged_date
            and self.twelve_week_update_requested_date is None
        ):
            return "in-probation-period"
        elif self.twelve_week_update_requested_date and (
            self.twelve_week_correspondence_acknowledged_date is None
            and self.twelve_week_response_state == TWELVE_WEEK_RESPONSE_DEFAULT
        ):
            return "in-12-week-correspondence"
        elif (
            self.twelve_week_correspondence_acknowledged_date
            or self.twelve_week_response_state != TWELVE_WEEK_RESPONSE_DEFAULT
        ) and self.is_ready_for_final_decision == BOOLEAN_FALSE:
            return "reviewing-changes"
        elif (
            self.is_ready_for_final_decision == BOOLEAN_TRUE
            and self.case_completed == DEFAULT_CASE_COMPLETED
        ):
            return "final-decision-due"
        return "unknown"

    def set_qa_status(self) -> str:
        if (
            self.reviewer is None
            and self.report_review_status == "ready-to-review"
            and self.report_approved_status != "yes"
        ):
            return STATUS_READY_TO_QA
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

    @property
    def status_requirements(self) -> List[Dict[str, str]]:  # noqa: C901
        if self.status == "complete":
            return [
                {
                    "text": "No additional requirements",
                    "url": "None",
                },
            ]
        elif self.status == "unassigned-case":
            return [
                {
                    "text": "Assign an auditor",
                    "url": "cases:edit-case-details",
                },
            ]
        elif self.status == "test-in-progress":
            test_in_progress_requirements = []
            if self.is_website_compliant == IS_WEBSITE_COMPLIANT_DEFAULT:
                test_in_progress_requirements.append(
                    {
                        "text": "Initial compliance decision decision is not filled in",
                        "url": "cases:edit-test-results",
                    }
                )
            if (
                self.accessibility_statement_state
                == ACCESSIBILITY_STATEMENT_DECISION_DEFAULT
            ):
                test_in_progress_requirements.append(
                    {
                        "text": "Initial accessibility statement decision is not filled in",
                        "url": "cases:edit-test-results",
                    }
                )
            return test_in_progress_requirements
        elif self.status == "report-in-progress":
            return [
                {
                    "text": "Report ready to be reviewed needs to be Yes",
                    "url": "cases:edit-report-details",
                },
            ]
        elif self.status == "qa-in-progress":
            return [
                {
                    "text": "Report approved needs to be Yes",
                    "url": "cases:edit-qa-process",
                },
            ]
        elif self.status == "report-ready-to-send":
            return [
                {
                    "text": "Report sent on requires a date",
                    "url": "cases:edit-report-correspondence",
                },
            ]
        elif self.status == "in-report-correspondence":
            return [
                {
                    "text": "Report acknowledged requires a date",
                    "url": "cases:edit-report-correspondence",
                },
            ]
        elif self.status == "in-probation-period":
            return [
                {
                    "text": "12 week update requested requires a date",
                    "url": "cases:edit-twelve-week-correspondence",
                },
            ]
        elif self.status == "in-12-week-correspondence":
            return [
                {
                    "text": "12 week update received requires a date or mark the case as having no response",
                    "url": "cases:edit-twelve-week-correspondence",
                },
            ]
        elif self.status == "reviewing-changes":
            return [
                {
                    "text": "Is this case ready for final decision? needs to be Yes",
                    "url": "cases:edit-review-changes",
                },
            ]
        elif self.status == "final-decision-due":
            return [
                {
                    "text": "Case completed requires a decision",
                    "url": "cases:edit-case-close",
                },
            ]
        elif self.status == "case-closed-waiting-to-be-sent":
            return [
                {
                    "text": "Date sent to equality body requires a date",
                    "url": "cases:edit-enforcement-body-correspondence",
                },
            ]
        elif self.status == "case-closed-sent-to-equalities-body":
            return [
                {
                    # pylint: disable-next=line-too-long
                    "text": "Equality body pursuing this case should be yes to move to 'In correspondence with equalities body'",
                    "url": "cases:edit-enforcement-body-correspondence",
                },
                {
                    # pylint: disable-next=line-too-long
                    "text": "Equalities body correspondence completed should be No further action to move to 'Complete'",
                    "url": "cases:edit-enforcement-body-correspondence",
                },
            ]
        elif self.status == "in-correspondence-with-equalities-body":
            return [
                {
                    # pylint: disable-next=line-too-long
                    "text": "Equalities body correspondence completed should be No further action to move to 'Complete'",
                    "url": "cases:edit-enforcement-body-correspondence",
                }
            ]
        return [
            {
                "text": "Something has gone wrong :(",
                "url": "None",
            },
        ]

    @property
    def in_report_correspondence_progress(self) -> str:
        now = date.today()
        five_days_ago = now - timedelta(days=5)
        if (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date > now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1-week followup coming up"
        elif (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date <= now
            and self.report_followup_week_1_sent_date is None
        ):
            return "1-week followup due"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date > now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4-week followup coming up"
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date <= now
            and self.report_followup_week_4_sent_date is None
        ):
            return "4-week followup due"
        elif self.report_followup_week_4_sent_date > five_days_ago:
            return "4-week followup sent, waiting five days for response"
        elif self.report_followup_week_4_sent_date <= five_days_ago:
            return "4-week followup sent, case needs to progress"
        return "Unknown"

    @property
    def twelve_week_correspondence_progress(self) -> str:
        now = date.today()
        five_days_ago = now - timedelta(days=5)
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
        elif self.twelve_week_1_week_chaser_sent_date > five_days_ago:
            return "1-week followup sent, waiting five days for response"
        elif self.twelve_week_1_week_chaser_sent_date <= five_days_ago:
            return "1-week followup sent, case needs to progress"
        return "Unknown"

    @property
    def contact_exists(self) -> bool:
        return Contact.objects.filter(case_id=self.id).exists()  # type: ignore

    @property
    def psb_appeal_deadline(self) -> Optional[timedelta]:
        if self.compliance_email_sent_date is None:
            return None
        return self.compliance_email_sent_date + timedelta(
            days=PSB_APPEAL_WINDOW_IN_DAYS
        )

    @property
    def audit(self):
        return self.audit_case.filter(is_deleted=False).first()  # type: ignore

    @property
    def report(self):
        return self.report_case.filter(is_deleted=False).first()  # type: ignore


class Contact(models.Model):
    """
    Model for cases Contact
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=200, default="", blank=True)
    last_name = models.CharField(max_length=200, default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    email = models.CharField(max_length=200, default="", blank=True)
    preferred = models.CharField(
        max_length=20, choices=PREFERRED_CHOICES, default=PREFERRED_DEFAULT
    )
    notes = models.TextField(default="", blank=True)
    created = models.DateTimeField()
    created_by = models.CharField(max_length=200, default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-preferred", "-id"]

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return str(f"Contact {self.name} {self.email}")

    def save(self, *args, **kwargs) -> None:
        if not self.id:  # type: ignore
            self.created = timezone.now()
        super().save(*args, **kwargs)
