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

from ..common.models import Boolean, Sector, SubCategory, VersionModel
from ..common.utils import (
    extract_domain_from_url,
    format_outstanding_issues,
    format_statement_check_overview,
)

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

PREFERRED_DEFAULT: str = "unknown"
PREFERRED_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (PREFERRED_DEFAULT, "Not known"),
]


MAX_LENGTH_OF_FORMATTED_URL = 25
PSB_APPEAL_WINDOW_IN_DAYS = 28

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


class Case(VersionModel):
    """
    Model for Case
    """

    class Variant(models.TextChoices):
        CLOSE_CASE = "close-case", "Equality Body Close Case"
        STATEMENT_CONTENT = "statement-content", "Statement content yes/no"
        REPORTING = "reporting", "Platform reports"
        ARCHIVED = "archived", "Archived"

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

    class ReportApprovedStatus(models.TextChoices):
        APPROVED = "yes", "Yes"
        IN_PROGRESS = "in-progress", "Further work is needed"
        NOT_STARTED = "not-started", "Not started"

    class TwelveWeekResponse(models.TextChoices):
        YES = "yes"
        NO = "no"
        NOT_SELECTED = "not-selected", "Not selected"

    class IsDisproportionateClaimed(models.TextChoices):
        YES = "yes"
        NO = "no"
        NOT_KNOWN = "unknown", "Not known"

    class RecommendationForEnforcement(models.TextChoices):
        NO_FURTHER_ACTION = "no-further-action", "No further action"
        OTHER = "other", "For enforcement consideration"
        UNKNOWN = "unknown", "Not selected"

    class CaseCompleted(models.TextChoices):
        COMPLETE_SEND = (
            "complete-send",
            "Case is complete and is ready to send to the equality body",
        )
        COMPLETE_NO_SEND = (
            "complete-no-send",
            "Case should not be sent to the equality body",
        )
        NO_DECISION = "no-decision", "Case still in progress"

    class EnforcementBodyPursuing(models.TextChoices):
        YES_COMPLETED = "yes-completed", "Yes, completed"
        YES_IN_PROGRESS = "yes-in-progress", "Yes, in progress"
        NO = "no", "No"

    class EnforcementBodyClosedCase(models.TextChoices):
        YES = "yes", "Yes"
        IN_PROGRESS = "in-progress", "Case in progress"
        NO = "no", "No (or holding)"

    class QAStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        UNASSIGNED = "unassigned-qa-case", "Unassigned QA case"
        IN_QA = "in-qa", "In QA"
        APPROVED = "qa-approved", "QA approved"

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
        choices=Variant.choices,
        default=Variant.CLOSE_CASE,
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
        choices=Boolean.choices,
        default=Boolean.NO,
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
        choices=ReportApprovedStatus.choices,
        default=ReportApprovedStatus.NOT_STARTED,
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
        max_length=20, choices=Boolean.choices, default=Boolean.NO
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
        choices=TwelveWeekResponse.choices,
        default=TwelveWeekResponse.NOT_SELECTED,
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
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    review_changes_complete_date = models.DateField(null=True, blank=True)

    # Final website
    final_website_complete_date = models.DateField(null=True, blank=True)

    # Final statement
    is_disproportionate_claimed = models.CharField(
        max_length=20,
        choices=IsDisproportionateClaimed.choices,
        default=IsDisproportionateClaimed.NOT_KNOWN,
    )
    disproportionate_notes = models.TextField(default="", blank=True)
    accessibility_statement_screenshot_url = models.TextField(default="", blank=True)
    final_statement_complete_date = models.DateField(null=True, blank=True)

    # Case close
    recommendation_for_enforcement = models.CharField(
        max_length=20,
        choices=RecommendationForEnforcement.choices,
        default=RecommendationForEnforcement.UNKNOWN,
    )
    recommendation_notes = models.TextField(default="", blank=True)
    compliance_email_sent_date = models.DateField(null=True, blank=True)
    case_completed = models.CharField(
        max_length=30, choices=CaseCompleted.choices, default=CaseCompleted.NO_DECISION
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
        choices=EnforcementBodyPursuing.choices,
        default=EnforcementBodyPursuing.NO,
    )
    enforcement_body_correspondence_notes = models.TextField(default="", blank=True)
    enforcement_retest_document_url = models.TextField(default="", blank=True)
    is_feedback_requested = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    enforcement_correspondence_complete_date = models.DateField(null=True, blank=True)

    # Equality body metadata
    sent_to_enforcement_body_sent_date = models.DateField(null=True, blank=True)
    enforcement_body_case_owner = models.TextField(default="", blank=True)
    enforcement_body_closed_case = models.CharField(
        max_length=20,
        choices=EnforcementBodyClosedCase.choices,
        default=EnforcementBodyClosedCase.NO,
    )
    enforcement_body_finished_date = models.DateField(null=True, blank=True)

    # Deactivate case page
    is_deactivated = models.BooleanField(default=False)
    deactivate_date = models.DateField(null=True, blank=True)
    deactivate_notes = models.TextField(default="", blank=True)

    # Dashboard page
    qa_status = models.CharField(
        max_length=200, choices=QAStatus.choices, default=QAStatus.UNKNOWN
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
        if (
            self.case_completed != Case.CaseCompleted.NO_DECISION
            and not self.completed_date
        ):
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
            and self.report_review_status == Boolean.YES
            and self.report_approved_status != Case.ReportApprovedStatus.APPROVED
        ):
            return Case.QAStatus.UNASSIGNED
        elif (
            self.report_review_status == Boolean.YES
            and self.report_approved_status != Case.ReportApprovedStatus.APPROVED
        ):
            return Case.QAStatus.IN_QA
        elif (
            self.report_review_status == Boolean.YES
            and self.report_approved_status == Case.ReportApprovedStatus.APPROVED
        ):
            return Case.QAStatus.APPROVED
        return Case.QAStatus.UNKNOWN

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
        return self.no_psb_contact == Boolean.NO

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
            type=EqualityBodyCorrespondence.Type.QUESTION
        )

    @property
    def equality_body_questions_unresolved(self):
        return self.equality_body_correspondences.filter(
            type=EqualityBodyCorrespondence.Type.QUESTION,
            status=EqualityBodyCorrespondence.Status.UNRESOLVED,
        )

    @property
    def equality_body_correspondence_retests(self):
        return self.equality_body_correspondences.filter(
            type=EqualityBodyCorrespondence.Type.RETEST
        )

    @property
    def equality_body_correspondence_retests_unresolved(self):
        return self.equality_body_correspondences.filter(
            type=EqualityBodyCorrespondence.Type.RETEST,
            status=EqualityBodyCorrespondence.Status.UNRESOLVED,
        )


class CaseStatus(models.Model):
    """
    Model for case status
    """

    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        UNASSIGNED = "unassigned-case", "Unassigned case"
        TEST_IN_PROGRESS = "test-in-progress", "Test in progress"
        REPORT_IN_PROGRESS = "report-in-progress", "Report in progress"
        READY_TO_QA = "unassigned-qa-case", "Report ready to QA"
        QA_IN_PROGRESS = "qa-in-progress", "QA in progress"
        REPORT_READY_TO_SEND = "report-ready-to-send", "Report ready to send"
        IN_REPORT_CORES = "in-report-correspondence", "Report sent"
        AWAITING_12_WEEK_DEADLINE = (
            "in-probation-period",
            "Report acknowledged waiting for 12-week deadline",
        )
        IN_12_WEEK_CORES = "in-12-week-correspondence", "After 12-week correspondence"
        REVIEWING_CHANGES = "reviewing-changes", "Reviewing changes"
        FINAL_DECISION_DUE = "final-decision-due", "Final decision due"
        CASE_CLOSED_WAITING_TO_SEND = (
            "case-closed-waiting-to-be-sent",
            "Case closed and waiting to be sent to equalities body",
        )
        CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY = (
            "case-closed-sent-to-equalities-body",
            "Case closed and sent to equalities body",
        )
        IN_CORES_WITH_ENFORCEMENT_BODY = (
            "in-correspondence-with-equalities-body",
            "In correspondence with equalities body",
        )
        COMPLETE = "complete", "Complete"
        DEACTIVATED = "deactivated", "Deactivated"

    case = models.OneToOneField(Case, on_delete=models.PROTECT, related_name="status")
    status = models.CharField(
        max_length=200, choices=Status.choices, default=Status.UNASSIGNED
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
            return CaseStatus.Status.DEACTIVATED
        elif (
            self.case.case_completed == Case.CaseCompleted.COMPLETE_NO_SEND
            or self.case.enforcement_body_pursuing
            == Case.EnforcementBodyPursuing.YES_COMPLETED
            or self.case.enforcement_body_closed_case
            == Case.EnforcementBodyClosedCase.YES
        ):
            return CaseStatus.Status.COMPLETE
        elif (
            self.case.enforcement_body_pursuing
            == Case.EnforcementBodyPursuing.YES_IN_PROGRESS
            or self.case.enforcement_body_closed_case
            == Case.EnforcementBodyClosedCase.IN_PROGRESS
        ):
            return CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY
        elif self.case.sent_to_enforcement_body_sent_date is not None:
            return CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY
        elif self.case.case_completed == Case.CaseCompleted.COMPLETE_SEND:
            return CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND
        elif self.case.no_psb_contact == Boolean.YES:
            return CaseStatus.Status.FINAL_DECISION_DUE
        elif self.case.auditor is None:
            return CaseStatus.Status.UNASSIGNED
        elif (
            compliance is None
            or self.case.compliance.website_compliance_state_initial
            == WEBSITE_COMPLIANCE_STATE_DEFAULT
            or self.case.statement_checks_still_initial
        ):
            return CaseStatus.Status.TEST_IN_PROGRESS
        elif (
            self.case.compliance.website_compliance_state_initial
            != WEBSITE_COMPLIANCE_STATE_DEFAULT
            and not self.case.statement_checks_still_initial
            and self.case.report_review_status != Boolean.YES
        ):
            return CaseStatus.Status.REPORT_IN_PROGRESS
        elif (
            self.case.report_review_status == Boolean.YES
            and self.case.report_approved_status != Case.ReportApprovedStatus.APPROVED
        ):
            return CaseStatus.Status.QA_IN_PROGRESS
        elif (
            self.case.report_approved_status == Case.ReportApprovedStatus.APPROVED
            and self.case.report_sent_date is None
        ):
            return CaseStatus.Status.REPORT_READY_TO_SEND
        elif self.case.report_sent_date and self.case.report_acknowledged_date is None:
            return CaseStatus.Status.IN_REPORT_CORES
        elif (
            self.case.report_acknowledged_date
            and self.case.twelve_week_update_requested_date is None
        ):
            return CaseStatus.Status.AWAITING_12_WEEK_DEADLINE
        elif self.case.twelve_week_update_requested_date and (
            self.case.twelve_week_correspondence_acknowledged_date is None
            and self.case.twelve_week_response_state
            == Case.TwelveWeekResponse.NOT_SELECTED
        ):
            return CaseStatus.Status.IN_12_WEEK_CORES
        elif (
            self.case.twelve_week_correspondence_acknowledged_date
            or self.case.twelve_week_response_state
            != Case.TwelveWeekResponse.NOT_SELECTED
        ) and self.case.is_ready_for_final_decision == Boolean.NO:
            return CaseStatus.Status.REVIEWING_CHANGES
        elif (
            self.case.is_ready_for_final_decision == Boolean.YES
            and self.case.case_completed == Case.CaseCompleted.NO_DECISION
        ):
            return CaseStatus.Status.FINAL_DECISION_DUE
        return CaseStatus.Status.UNKNOWN


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

    class EventType(models.TextChoices):
        CREATE = "create", "Create"
        AUDITOR = "auditor", "Change of auditor"
        CREATE_AUDIT = "create_audit", "Start test"
        CREATE_REPORT = "create_report", "Create report"
        READY_FOR_QA = "ready_for_qa", "Report readiness for QA"
        QA_AUDITOR = "qa_auditor", "Change of QA auditor"
        APPROVE_REPORT = "approve_report", "Report approval"
        START_RETEST = "retest", "Start retest"
        READY_FOR_FINAL_DECISION = "read_for_final_decision", "Ready for final decision"
        CASE_COMPLETED = "completed", "Completed"

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=100, choices=EventType.choices, default=EventType.CREATE
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

    class Type(models.TextChoices):
        QUESTION = "question", "Question"
        RETEST = "retest", "Retest request"

    class Status(models.TextChoices):
        UNRESOLVED = "outstanding", "Unresolved"
        RESOLVED = "resolved", "Resolved"

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=1, blank=True)
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.QUESTION,
    )
    message = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)
    zendesk_url = models.TextField(default="", blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNRESOLVED,
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
