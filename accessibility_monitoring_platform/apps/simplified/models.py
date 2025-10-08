"""
Models - cases
"""

import json
import re
from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..cases.models import BaseCase, SimplifiedCaseStatus, get_previous_case_identifier
from ..common.models import Boolean, EmailTemplate, Link, VersionModel
from ..common.utils import (
    extract_domain_from_url,
    format_outstanding_issues,
    format_statement_check_overview,
)

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


class Sort(models.TextChoices):
    NEWEST = "", "Newest, Unassigned first"
    OLDEST = "id", "Oldest"
    NAME = "organisation_name", "Alphabetic"


class SimplifiedCase(BaseCase):
    """
    Model for Case
    """

    Status = SimplifiedCaseStatus

    class Variant(models.TextChoices):
        CLOSE_CASE = "close-case", "Equality Body Close Case"
        STATEMENT_CONTENT = "statement-content", "Statement content yes/no"
        REPORTING = "reporting", "Platform reports"
        ARCHIVED = "archived", "Archived"

    class ReportApprovedStatus(models.TextChoices):
        APPROVED = "yes", "Yes"
        IN_PROGRESS = "in-progress", "Further work is needed"
        NOT_STARTED = "not-started", "Not started"

    class ContactDetailsFound(models.TextChoices):
        FOUND = "found", "Contact details found"
        NOT_FOUND = "not-found", "No contact details found"
        NOT_CHECKED = "not-checked", "Not checked"

    class TwelveWeekResponse(models.TextChoices):
        YES = "yes"
        NO = "no"
        NOT_SELECTED = "not-selected", "Not selected"

    class IsDisproportionateClaimed(models.TextChoices):
        YES = "yes"
        NO = "no"
        NOT_KNOWN = "unknown", "Not known"

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

    class OrganisationResponse(models.TextChoices):
        NO_RESPONSE = "no-response", "Organisation did not respond to 12-week update"
        NOT_APPLICABLE = (
            "not-applicable",
            "Not applicable or organisation responded to 12-week update",
        )

    archive = models.TextField(default="", blank=True)
    variant = models.CharField(
        max_length=20,
        choices=Variant.choices,
        default=Variant.CLOSE_CASE,
    )

    # Case metadata page
    previous_case_url = models.TextField(default="", blank=True)
    trello_url = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)

    # Historic testing details page
    test_results_url = models.TextField(default="", blank=True)
    testing_details_complete_date = models.DateField(null=True, blank=True)

    # Report ready for QA page
    report_draft_url = models.TextField(default="", blank=True)
    report_notes = models.TextField(default="", blank=True)
    report_review_status = models.CharField(
        max_length=200,
        choices=Boolean.choices,
        default=Boolean.NO,
    )
    reporting_details_complete_date = models.DateField(null=True, blank=True)

    # QA process
    reviewer_notes = models.TextField(default="", blank=True)
    report_final_pdf_url = models.TextField(default="", blank=True)
    report_final_odt_url = models.TextField(default="", blank=True)
    qa_process_complete_date = models.DateField(null=True, blank=True)

    # QA auditor
    qa_auditor_complete_date = models.DateField(null=True, blank=True)

    # QA approval
    report_approved_status = models.CharField(
        max_length=200,
        choices=ReportApprovedStatus.choices,
        default=ReportApprovedStatus.NOT_STARTED,
    )
    qa_approval_complete_date = models.DateField(null=True, blank=True)

    # Publish report
    publish_report_complete_date = models.DateField(null=True, blank=True)

    # Correspondence overview page
    zendesk_url = models.TextField(default="", blank=True)
    cores_overview_complete_date = models.DateField(null=True, blank=True)

    # Manage contact details page
    contact_notes = models.TextField(default="", blank=True)
    manage_contact_details_complete_date = models.DateField(null=True, blank=True)

    # Find contact details page - Removed from UI
    contact_details_found = models.CharField(
        max_length=20,
        choices=ContactDetailsFound.choices,
        default=ContactDetailsFound.NOT_CHECKED,
    )

    # Correspondence process
    enable_correspondence_process = models.BooleanField(default=False)

    # Request contact details page
    seven_day_no_contact_email_sent_date = models.DateField(null=True, blank=True)
    seven_day_no_contact_request_sent_to = models.CharField(
        max_length=200, default="", blank=True
    )
    request_contact_details_complete_date = models.DateField(null=True, blank=True)

    # One week contact details page
    no_contact_one_week_chaser_due_date = models.DateField(null=True, blank=True)
    no_contact_one_week_chaser_sent_date = models.DateField(null=True, blank=True)
    no_contact_one_week_chaser_sent_to = models.CharField(
        max_length=200, default="", blank=True
    )
    one_week_contact_details_complete_date = models.DateField(null=True, blank=True)

    # Four week contact details page
    no_contact_four_week_chaser_due_date = models.DateField(null=True, blank=True)
    no_contact_four_week_chaser_sent_date = models.DateField(null=True, blank=True)
    no_contact_four_week_chaser_sent_to = models.CharField(
        max_length=200, default="", blank=True
    )
    correspondence_notes = models.TextField(default="", blank=True)
    four_week_contact_details_complete_date = models.DateField(null=True, blank=True)

    # Unresponsive PSB page
    no_psb_contact = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    no_psb_contact_notes = models.TextField(default="", blank=True)
    no_psb_contact_complete_date = models.DateField(null=True, blank=True)

    # Report sent on page
    report_sent_date = models.DateField(null=True, blank=True)
    report_sent_to_email = models.CharField(max_length=200, default="", blank=True)
    report_sent_on_complete_date = models.DateField(null=True, blank=True)

    # One week followup page
    report_followup_week_1_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_1_due_date = models.DateField(null=True, blank=True)
    one_week_followup_sent_to_email = models.CharField(
        max_length=200, default="", blank=True
    )
    one_week_followup_complete_date = models.DateField(null=True, blank=True)

    # Four week followup page
    report_followup_week_4_sent_date = models.DateField(null=True, blank=True)
    report_followup_week_4_due_date = models.DateField(null=True, blank=True)
    four_week_followup_sent_to_email = models.CharField(
        max_length=200, default="", blank=True
    )
    four_week_followup_complete_date = models.DateField(null=True, blank=True)

    # Report acknowledged page
    report_acknowledged_date = models.DateField(null=True, blank=True)
    report_acknowledged_by_email = models.CharField(
        max_length=200, default="", blank=True
    )
    report_acknowledged_complete_date = models.DateField(null=True, blank=True)

    # 12-week update requested page
    twelve_week_update_requested_date = models.DateField(null=True, blank=True)
    report_followup_week_12_due_date = models.DateField(null=True, blank=True)
    twelve_week_update_request_sent_to_email = models.CharField(
        max_length=200, default="", blank=True
    )
    twelve_week_correspondence_notes = models.TextField(default="", blank=True)
    twelve_week_update_requested_complete_date = models.DateField(null=True, blank=True)

    # One week followup for final update page
    twelve_week_1_week_chaser_sent_date = models.DateField(null=True, blank=True)
    twelve_week_1_week_chaser_due_date = models.DateField(null=True, blank=True)
    twelve_week_1_week_chaser_sent_to_email = models.CharField(
        max_length=200, default="", blank=True
    )
    one_week_followup_final_complete_date = models.DateField(null=True, blank=True)

    # 12-week update request acknowledged page
    twelve_week_correspondence_acknowledged_date = models.DateField(
        null=True, blank=True
    )
    twelve_week_correspondence_acknowledged_by_email = models.CharField(
        max_length=200, default="", blank=True
    )
    twelve_week_response_state = models.CharField(
        max_length=20,
        choices=TwelveWeekResponse.choices,
        default=TwelveWeekResponse.NOT_SELECTED,
    )
    organisation_response = models.CharField(
        max_length=20,
        choices=OrganisationResponse.choices,
        default=OrganisationResponse.NOT_APPLICABLE,
    )
    twelve_week_update_request_ack_complete_date = models.DateField(
        null=True, blank=True
    )

    # Report correspondence page
    report_correspondence_complete_date = models.DateField(null=True, blank=True)

    # 12-week correspondence page
    twelve_week_correspondence_complete_date = models.DateField(null=True, blank=True)

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

    # Recommendation
    compliance_email_sent_date = models.DateField(null=True, blank=True)
    compliance_decision_sent_to_email = models.CharField(
        max_length=200, default="", blank=True
    )
    # recommendation_for_enforcement from BaseCase
    recommendation_notes = models.TextField(default="", blank=True)
    enforcement_recommendation_complete_date = models.DateField(null=True, blank=True)

    # Case close
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
    enforcement_correspondence_complete_date = models.DateField(null=True, blank=True)

    # Equality body metadata
    sent_to_enforcement_body_sent_date = models.DateField(null=True, blank=True)
    equality_body_case_start_date = models.DateField(null=True, blank=True)
    enforcement_body_case_owner = models.TextField(default="", blank=True)
    enforcement_body_closed_case = models.CharField(
        max_length=20,
        choices=EnforcementBodyClosedCase.choices,
        default=EnforcementBodyClosedCase.NO,
    )
    enforcement_body_finished_date = models.DateField(null=True, blank=True)
    equality_body_notes = models.TextField(default="", blank=True)

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

    def save(self, *args, **kwargs) -> None:
        now: datetime = timezone.now()
        if (
            self.case_completed != SimplifiedCase.CaseCompleted.NO_DECISION
            and not self.completed_date
        ):
            self.completed_date = now
        self.qa_status = self.calulate_qa_status()
        if not self.domain:
            self.domain = extract_domain_from_url(self.home_page_url)
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
        title: str = ""
        if self.website_name:
            title += f"{self.website_name} &nbsp;|&nbsp; "
        title += f"{self.organisation_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    @property
    def next_action_due_date(self) -> date | None:
        if self.status == SimplifiedCase.Status.REPORT_READY_TO_SEND:
            if (
                self.no_contact_one_week_chaser_due_date
                and self.no_contact_one_week_chaser_sent_date is None
            ):
                return self.no_contact_one_week_chaser_due_date
            if (
                self.no_contact_four_week_chaser_due_date
                and self.no_contact_four_week_chaser_sent_date is None
            ):
                return self.no_contact_four_week_chaser_due_date
            if self.no_contact_four_week_chaser_sent_date is not None:
                return self.no_contact_four_week_chaser_sent_date + timedelta(
                    days=ONE_WEEK_IN_DAYS
                )

        if self.status == SimplifiedCase.Status.IN_REPORT_CORES:
            if self.report_followup_week_1_sent_date is None:
                return self.report_followup_week_1_due_date
            elif self.report_followup_week_4_sent_date is None:
                return self.report_followup_week_4_due_date
            elif self.report_followup_week_4_sent_date:
                return self.report_followup_week_4_sent_date + timedelta(
                    days=ONE_WEEK_IN_DAYS
                )
            raise Exception(
                "Case is in-report-correspondence but neither sent date is set"
            )

        if self.status == SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE:
            return self.report_followup_week_12_due_date

        if self.status == SimplifiedCase.Status.AFTER_12_WEEK_CORES:
            if self.twelve_week_1_week_chaser_sent_date is None:
                return self.twelve_week_1_week_chaser_due_date
            return self.twelve_week_1_week_chaser_sent_date + timedelta(
                days=ONE_WEEK_IN_DAYS
            )

        return date(1970, 1, 1)

    @property
    def next_action_due_date_tense(self) -> str:
        today: date = date.today()
        if self.next_action_due_date and self.next_action_due_date < today:
            return "past"
        if self.next_action_due_date == today:
            return "present"
        return "future"

    def calulate_qa_status(self) -> str:
        if (
            self.reviewer is None
            and self.report_review_status == Boolean.YES
            and self.report_approved_status
            != SimplifiedCase.ReportApprovedStatus.APPROVED
        ):
            return SimplifiedCase.QAStatus.UNASSIGNED
        elif (
            self.report_review_status == Boolean.YES
            and self.report_approved_status
            != SimplifiedCase.ReportApprovedStatus.APPROVED
        ):
            return SimplifiedCase.QAStatus.IN_QA
        elif (
            self.report_review_status == Boolean.YES
            and self.report_approved_status
            == SimplifiedCase.ReportApprovedStatus.APPROVED
        ):
            return SimplifiedCase.QAStatus.APPROVED
        return SimplifiedCase.QAStatus.UNKNOWN

    @property
    def in_report_correspondence_progress(self) -> Link:
        now: date = date.today()
        seven_days_ago = now - timedelta(days=ONE_WEEK_IN_DAYS)
        if (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date > now
            and self.report_followup_week_1_sent_date is None
        ):
            return Link(
                label="1-week follow-up to report coming up",
                url=reverse(
                    "simplified:edit-report-one-week-followup", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.report_followup_week_1_due_date
            and self.report_followup_week_1_due_date <= now
            and self.report_followup_week_1_sent_date is None
        ):
            return Link(
                label="1-week follow-up to report due",
                url=reverse(
                    "simplified:edit-report-one-week-followup", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date > now
            and self.report_followup_week_4_sent_date is None
        ):
            return Link(
                label="4-week follow-up to report coming up",
                url=reverse(
                    "simplified:edit-report-four-week-followup", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.report_followup_week_1_sent_date
            and self.report_followup_week_4_due_date
            and self.report_followup_week_4_due_date <= now
            and self.report_followup_week_4_sent_date is None
        ):
            return Link(
                label="4-week follow-up to report due",
                url=reverse(
                    "simplified:edit-report-four-week-followup", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.report_followup_week_4_sent_date is not None
            and self.report_followup_week_4_sent_date > seven_days_ago
        ):
            return Link(
                label="4-week follow-up to report sent, waiting seven days for response",
                url=reverse(
                    "simplified:edit-report-acknowledged", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.report_followup_week_4_sent_date is not None
            and self.report_followup_week_4_sent_date <= seven_days_ago
        ):
            return Link(
                label="4-week follow-up to report sent, case needs to progress",
                url=reverse(
                    "simplified:edit-report-acknowledged", kwargs={"pk": self.id}
                ),
            )
        return Link(
            label="Unknown",
            url=reverse("simplified:manage-contact-details", kwargs={"pk": self.id}),
        )

    @property
    def twelve_week_correspondence_progress(self) -> Link:
        now: date = date.today()
        seven_days_ago = now - timedelta(days=ONE_WEEK_IN_DAYS)
        if (
            self.twelve_week_1_week_chaser_due_date
            and self.twelve_week_1_week_chaser_due_date > now
            and self.twelve_week_1_week_chaser_sent_date is None
        ):
            return Link(
                label="1-week follow-up coming up",
                url=reverse(
                    "simplified:edit-12-week-one-week-followup-final",
                    kwargs={"pk": self.id},
                ),
            )
        elif (
            self.twelve_week_update_requested_date
            and self.twelve_week_update_requested_date < now
            and self.twelve_week_1_week_chaser_sent_date is None
        ):
            return Link(
                label="1-week follow-up due",
                url=reverse(
                    "simplified:edit-12-week-one-week-followup-final",
                    kwargs={"pk": self.id},
                ),
            )
        elif (
            self.twelve_week_1_week_chaser_sent_date is not None
            and self.twelve_week_1_week_chaser_sent_date > seven_days_ago
        ):
            return Link(
                label="1-week follow-up sent, waiting seven days for response",
                url=reverse(
                    "simplified:edit-12-week-update-request-ack", kwargs={"pk": self.id}
                ),
            )
        elif (
            self.twelve_week_1_week_chaser_sent_date is not None
            and self.twelve_week_1_week_chaser_sent_date <= seven_days_ago
        ):
            return Link(
                label="1-week follow-up sent, case needs to progress",
                url=reverse(
                    "simplified:edit-12-week-update-request-ack", kwargs={"pk": self.id}
                ),
            )
        return Link(
            label="Unknown",
            url=reverse("simplified:manage-contact-details", kwargs={"pk": self.id}),
        )

    @property
    def contacts(self) -> QuerySet["Contact"]:
        return self.contact_set.filter(is_deleted=False)

    @property
    def contact_exists(self) -> bool:
        return self.contacts.exists()

    @property
    def equality_body_export_contact_details(self) -> QuerySet["Contact"]:
        """
        Concatenate the values for all the contacts and return as a single string.
        """
        contact_details: str = ""
        for contact in self.contacts:
            if contact_details:
                contact_details += "\n"
            if contact.name:
                contact_details += f"{contact.name}\n"
            if contact.job_title:
                contact_details += f"{contact.job_title}\n"
            if contact.email:
                contact_details += f"{contact.email}\n"
        return contact_details
        return self.contact_set.filter(is_deleted=False)

    @property
    def psb_appeal_deadline(self) -> date | None:
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
            return self.audit_simplifiedcase
        except ObjectDoesNotExist:
            return None

    @property
    def not_archived(self) -> bool:
        return self.archive == ""

    @property
    def show_start_test(self) -> bool:
        return self.not_archived and self.audit is None

    @property
    def not_archived_has_audit(self) -> bool:
        return self.not_archived and self.audit is not None

    @property
    def report_acknowledged_yes_no(self) -> str:
        return "Yes" if self.report_acknowledged_date else "No"

    @property
    def show_start_12_week_retest(self) -> bool:
        return (
            self.not_archived
            and self.audit is not None
            and self.audit.retest_date is None
        )

    @property
    def show_12_week_retest(self) -> bool:
        return (
            self.not_archived
            and self.audit is not None
            and self.audit.retest_date is not None
        )

    @property
    def report(self):
        try:
            return self.report_basecase.first()
        except ObjectDoesNotExist:
            return None

    @property
    def show_create_report(self) -> bool:
        return self.not_archived and self.report is None

    @property
    def not_archived_has_report(self) -> bool:
        return self.not_archived and self.report is not None

    @property
    def published_report_url(self) -> str:
        if self.report and self.report.latest_s3_report:
            return f"{settings.AMP_PROTOCOL}{settings.AMP_VIEWER_DOMAIN}/reports/{self.report.latest_s3_report.guid}"
        else:
            return ""

    @property
    def previous_case_identifier(self) -> str | None:
        return get_previous_case_identifier(previous_case_url=self.previous_case_url)

    @property
    def last_edited(self) -> datetime:
        """Return when case or related data was last changed"""
        updated_times: list[datetime | None] = [self.created, self.updated]

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

        for comment in self.comment_basecase.all():
            updated_times.append(comment.created_date)
            updated_times.append(comment.updated)

        for task in self.task_set.all():
            updated_times.append(task.updated)

        if self.report is not None:
            updated_times.append(self.report.updated)

        for s3_report in self.s3report_set.all():
            updated_times.append(s3_report.created)

        return max([updated for updated in updated_times if updated is not None])

    @property
    def website_compliance_display(self):
        if (
            self.compliance.website_compliance_state_12_week
            == CaseCompliance.WebsiteCompliance.UNKNOWN
        ):
            return self.compliance.get_website_compliance_state_initial_display()
        return self.compliance.get_website_compliance_state_12_week_display()

    @property
    def accessibility_statement_compliance_display(self):
        if (
            self.compliance.statement_compliance_state_12_week
            == CaseCompliance.StatementCompliance.UNKNOWN
        ):
            return self.compliance.get_statement_compliance_state_initial_display()
        return self.compliance.get_statement_compliance_state_12_week_display()

    @property
    def total_website_issues(self) -> int:
        if self.audit is None:
            return 0
        return self.audit.failed_check_results.count()

    @property
    def total_website_issues_fixed(self) -> int:
        if self.audit is None:
            return 0
        return self.audit.fixed_check_results.count()

    @property
    def total_website_issues_unfixed(self) -> int:
        if self.audit is None or self.total_website_issues == 0:
            return 0
        return self.total_website_issues - self.total_website_issues_fixed

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
    def csv_export_statement_initially_found(self) -> str:
        if self.audit is None:
            return "unknown"
        if self.audit.statement_initially_found:
            return "Yes"
        return "No"

    @property
    def csv_export_statement_found_at_12_week_retest(self) -> str:
        if self.audit is None:
            return "unknown"
        if self.audit.statement_found_at_12_week_retest:
            return "Yes"
        return "No"

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
        return format_statement_check_overview(
            tests_passed=self.audit.passed_statement_check_results.count(),
            tests_failed=self.audit.failed_statement_check_results.count(),
            retests_passed=self.audit.passed_retest_statement_check_results.count(),
            retests_failed=self.audit.failed_retest_statement_check_results.count(),
        )

    @property
    def statement_checks_still_initial(self):
        if self.audit:
            return not self.audit.overview_statement_checks_complete
        return (
            self.compliance.statement_compliance_state_initial
            == CaseCompliance.StatementCompliance.UNKNOWN
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
        return self.retest_simplifiedcase.filter(is_deleted=False)

    @property
    def actual_retests(self):
        return self.retests.filter(id_within_case__gt=0)

    @property
    def number_retests(self):
        return self.actual_retests.count()

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
    def equality_body_correspondences_unresolved_count(self):
        return self.equality_body_correspondences.filter(
            status=EqualityBodyCorrespondence.Status.UNRESOLVED,
        ).count()

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

    @property
    def zendesk_tickets(self):
        return self.zendeskticket_set.filter(is_deleted=False)

    @property
    def latest_psb_zendesk_url(self) -> str:
        if self.zendesk_tickets:
            return self.zendesk_tickets.first().url
        return self.zendesk_url

    @property
    def email_templates(self):
        return EmailTemplate.objects.filter(is_deleted=False)

    @property
    def report_number_of_visits(self):
        return self.reportvisitsmetrics_set.all().count()

    @property
    def report_number_of_unique_visitors(self):
        return (
            self.reportvisitsmetrics_set.values_list("fingerprint_hash")
            .distinct()
            .count()
        )

    @property
    def website_contact_links_count(self):
        """
        Count how many links have been entered where the user can look for contacts
        """
        links_count: int = 0
        if self.audit is not None:
            if self.audit.contact_page is not None and self.audit.contact_page.url:
                links_count += 1
            if (
                self.audit.accessibility_statement_page is not None
                and self.audit.accessibility_statement_page.url
            ):
                links_count += 1
        return links_count

    @property
    def overdue_link(self) -> Link:
        """Return link to edit Case if it is overdue"""
        kwargs_case_pk: dict[str, int] = {"pk": self.id}
        start_date: date = date(2020, 1, 1)
        end_date: date = date.today()
        seven_days_ago = date.today() - timedelta(days=7)

        if (
            self.status == SimplifiedCase.Status.REPORT_READY_TO_SEND
            and self.enable_correspondence_process is True
        ):
            if (
                self.seven_day_no_contact_email_sent_date is not None
                and self.seven_day_no_contact_email_sent_date > start_date
                and self.seven_day_no_contact_email_sent_date <= seven_days_ago
                and self.no_contact_one_week_chaser_sent_date is None
                and self.no_contact_four_week_chaser_sent_date is None
            ):
                return Link(
                    label="No contact details response overdue",
                    url=reverse(
                        "simplified:edit-request-contact-details", kwargs=kwargs_case_pk
                    ),
                )
            if (
                self.no_contact_one_week_chaser_due_date is not None
                and self.no_contact_one_week_chaser_due_date > start_date
                and self.no_contact_one_week_chaser_due_date <= end_date
                and self.no_contact_one_week_chaser_sent_date is None
            ):
                return Link(
                    label="No contact details response overdue",
                    url=reverse(
                        "simplified:edit-request-contact-details", kwargs=kwargs_case_pk
                    ),
                )
            if (
                self.no_contact_four_week_chaser_due_date is not None
                and self.no_contact_four_week_chaser_due_date > start_date
                and self.no_contact_four_week_chaser_due_date <= end_date
                and self.no_contact_four_week_chaser_sent_date is None
            ):
                return Link(
                    label="No contact details response overdue",
                    url=reverse(
                        "simplified:edit-request-contact-details", kwargs=kwargs_case_pk
                    ),
                )

        if self.status == SimplifiedCase.Status.IN_REPORT_CORES:
            if (
                self.report_followup_week_1_due_date is not None
                and self.report_followup_week_1_due_date > start_date
                and self.report_followup_week_1_due_date <= end_date
                and self.report_followup_week_1_sent_date is None
            ):
                return self.in_report_correspondence_progress
            if (
                self.report_followup_week_4_due_date is not None
                and self.report_followup_week_4_due_date > start_date
                and self.report_followup_week_4_due_date <= end_date
                and self.report_followup_week_4_sent_date is None
            ):
                return self.in_report_correspondence_progress
            if (
                self.report_followup_week_4_sent_date is not None
                and self.report_followup_week_4_sent_date > start_date
                and self.report_followup_week_4_sent_date <= seven_days_ago
            ):
                return self.in_report_correspondence_progress

        if self.status == SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE:
            if (
                self.report_followup_week_12_due_date is not None
                and self.report_followup_week_12_due_date > start_date
                and self.report_followup_week_12_due_date <= end_date
            ):
                return Link(
                    label="12-week update due",
                    url=reverse(
                        "simplified:edit-12-week-update-requested",
                        kwargs=kwargs_case_pk,
                    ),
                )

        if self.status == SimplifiedCase.Status.AFTER_12_WEEK_CORES:
            if (
                self.twelve_week_1_week_chaser_due_date is not None
                and self.twelve_week_1_week_chaser_due_date > start_date
                and self.twelve_week_1_week_chaser_due_date <= end_date
                and self.twelve_week_1_week_chaser_sent_date is None
            ):
                return self.twelve_week_correspondence_progress
            if (
                self.twelve_week_1_week_chaser_sent_date is not None
                and self.twelve_week_1_week_chaser_sent_date > start_date
                and self.twelve_week_1_week_chaser_sent_date <= seven_days_ago
            ):
                return self.twelve_week_correspondence_progress
        return Link(
            label="Go to case",
            url=reverse("simplified:case-detail", kwargs=kwargs_case_pk),
        )

    def update_case_status(self):
        if hasattr(self, "casestatus") is False:
            CaseStatus.objects.create(simplified_case=self)
        status: str = self.casestatus.calculate_status()
        if self.status != status:
            self.status = status
            self.save()
        if self.casestatus.status != status:
            self.casestatus.status = status
            self.casestatus.save()

    @property
    def next_page_link(self) -> Link:
        """Return link to next page based on Case status"""
        return {
            CaseStatus.Status.UNASSIGNED: Link(
                label="Go to case metadata",
                url=reverse("simplified:edit-case-metadata", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.TEST_IN_PROGRESS: Link(
                label="Go to testing details",
                url=reverse("simplified:edit-test-results", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.REPORT_IN_PROGRESS: Link(
                label="Go to report ready for QA",
                url=reverse(
                    "simplified:edit-report-ready-for-qa", kwargs={"pk": self.id}
                ),
            ),
            CaseStatus.Status.READY_TO_QA: Link(
                label="Go to QA approval",
                url=reverse("simplified:edit-qa-approval", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.QA_IN_PROGRESS: Link(
                label="Go to QA approval",
                url=reverse("simplified:edit-qa-approval", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.REPORT_READY_TO_SEND: Link(
                label="Go to Report sent on",
                url=reverse("simplified:edit-report-sent-on", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.IN_REPORT_CORES: self.in_report_correspondence_progress,
            CaseStatus.Status.AWAITING_12_WEEK_DEADLINE: Link(
                label="Go to 12-week update requested",
                url=reverse(
                    "simplified:edit-12-week-update-requested", kwargs={"pk": self.id}
                ),
            ),
            CaseStatus.Status.AFTER_12_WEEK_CORES: self.twelve_week_correspondence_progress,
            CaseStatus.Status.REVIEWING_CHANGES: Link(
                label="Go to reviewing changes",
                url=reverse("simplified:edit-review-changes", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.FINAL_DECISION_DUE: Link(
                label="Go to closing the case",
                url=reverse("simplified:edit-case-close", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND: Link(
                label="Go to closing the case",
                url=reverse("simplified:edit-case-close", kwargs={"pk": self.id}),
            ),
            CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY: Link(
                label="Go to equality body metadata",
                url=reverse(
                    "simplified:edit-equality-body-metadata", kwargs={"pk": self.id}
                ),
            ),
            CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY: Link(
                label="Go to equality body metadata",
                url=reverse(
                    "simplified:edit-equality-body-metadata", kwargs={"pk": self.id}
                ),
            ),
            CaseStatus.Status.COMPLETE: Link(
                label="Go to statement enforcement",
                url=reverse(
                    "simplified:edit-statement-enforcement", kwargs={"pk": self.id}
                ),
            ),
            CaseStatus.Status.DEACTIVATED: Link(
                label="Go to case metadata",
                url=reverse("simplified:edit-case-metadata", kwargs={"pk": self.id}),
            ),
        }.get(
            self.status,
            Link(
                label="Go to case metadata",
                url=reverse("simplified:edit-case-metadata", kwargs={"pk": self.id}),
            ),
        )


class CaseStatus(models.Model):
    """
    Model for case status
    """

    Status = SimplifiedCaseStatus

    CLOSED_CASE_STATUSES: list[str] = [
        Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
        Status.COMPLETE,
        Status.CASE_CLOSED_WAITING_TO_SEND,
        Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        Status.DEACTIVATED,
    ]

    simplified_case = models.OneToOneField(SimplifiedCase, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=200, choices=Status.choices, default=Status.UNASSIGNED
    )

    class Meta:
        verbose_name_plural = "Case statuses"

    def __str__(self) -> str:
        return self.status

    def calculate_status(self) -> str:  # noqa: C901
        try:
            compliance: CaseCompliance = self.simplified_case.compliance
        except CaseCompliance.DoesNotExist:
            compliance = None

        if self.simplified_case.is_deactivated:
            return CaseStatus.Status.DEACTIVATED
        elif (
            self.simplified_case.case_completed
            == SimplifiedCase.CaseCompleted.COMPLETE_NO_SEND
            or self.simplified_case.enforcement_body_pursuing
            == SimplifiedCase.EnforcementBodyPursuing.YES_COMPLETED
            or self.simplified_case.enforcement_body_closed_case
            == SimplifiedCase.EnforcementBodyClosedCase.YES
        ):
            return CaseStatus.Status.COMPLETE
        elif (
            self.simplified_case.enforcement_body_pursuing
            == SimplifiedCase.EnforcementBodyPursuing.YES_IN_PROGRESS
            or self.simplified_case.enforcement_body_closed_case
            == SimplifiedCase.EnforcementBodyClosedCase.IN_PROGRESS
        ):
            return CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY
        elif self.simplified_case.sent_to_enforcement_body_sent_date is not None:
            return CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY
        elif (
            self.simplified_case.case_completed
            == SimplifiedCase.CaseCompleted.COMPLETE_SEND
        ):
            return CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND
        elif self.simplified_case.no_psb_contact == Boolean.YES:
            return CaseStatus.Status.FINAL_DECISION_DUE
        elif self.simplified_case.auditor is None:
            return CaseStatus.Status.UNASSIGNED
        elif (
            compliance is None
            or compliance.website_compliance_state_initial
            == CaseCompliance.WebsiteCompliance.UNKNOWN
            or bool(
                self.simplified_case.statement_checks_still_initial
                and self.simplified_case.compliance.statement_compliance_state_initial
                == CaseCompliance.StatementCompliance.UNKNOWN
            )
        ):
            return CaseStatus.Status.TEST_IN_PROGRESS
        elif (
            self.simplified_case.compliance.website_compliance_state_initial
            != CaseCompliance.WebsiteCompliance.UNKNOWN
            and (
                not self.simplified_case.statement_checks_still_initial
                or self.simplified_case.compliance.statement_compliance_state_initial
                != CaseCompliance.StatementCompliance.UNKNOWN
            )
            and self.simplified_case.report_review_status != Boolean.YES
        ):
            return CaseStatus.Status.REPORT_IN_PROGRESS
        elif (
            self.simplified_case.report_review_status == Boolean.YES
            and self.simplified_case.report_approved_status
            != SimplifiedCase.ReportApprovedStatus.APPROVED
        ):
            return CaseStatus.Status.QA_IN_PROGRESS
        elif (
            self.simplified_case.report_approved_status
            == SimplifiedCase.ReportApprovedStatus.APPROVED
            and self.simplified_case.report_sent_date is None
        ):
            return CaseStatus.Status.REPORT_READY_TO_SEND
        elif (
            self.simplified_case.report_sent_date
            and self.simplified_case.report_acknowledged_date is None
        ):
            return CaseStatus.Status.IN_REPORT_CORES
        elif self.simplified_case.report_acknowledged_date and (
            self.simplified_case.twelve_week_update_requested_date is None
            and self.simplified_case.twelve_week_correspondence_acknowledged_date
            is None
        ):
            return CaseStatus.Status.AWAITING_12_WEEK_DEADLINE
        elif self.simplified_case.twelve_week_update_requested_date and (
            self.simplified_case.twelve_week_correspondence_acknowledged_date is None
            and self.simplified_case.organisation_response
            == SimplifiedCase.OrganisationResponse.NOT_APPLICABLE
        ):
            return CaseStatus.Status.AFTER_12_WEEK_CORES
        elif (
            self.simplified_case.twelve_week_correspondence_acknowledged_date
            or self.simplified_case.organisation_response
            != SimplifiedCase.OrganisationResponse.NOT_APPLICABLE
        ) and self.simplified_case.is_ready_for_final_decision == Boolean.NO:
            return CaseStatus.Status.REVIEWING_CHANGES
        elif (
            self.simplified_case.is_ready_for_final_decision == Boolean.YES
            and self.simplified_case.case_completed
            == SimplifiedCase.CaseCompleted.NO_DECISION
        ):
            return CaseStatus.Status.FINAL_DECISION_DUE
        return CaseStatus.Status.UNKNOWN


class CaseCompliance(VersionModel):
    """
    Model for website and accessibility statement compliance
    """

    class WebsiteCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Fully compliant"
        PARTIALLY = "partially-compliant", "Partially compliant"
        UNKNOWN = "not-known", "Not known"

    class StatementCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NOT_COMPLIANT = "not-compliant", "Not compliant or no statement"
        UNKNOWN = "unknown", "Not assessed"

    simplified_case = models.OneToOneField(
        SimplifiedCase, on_delete=models.PROTECT, related_name="compliance"
    )
    website_compliance_state_initial = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    website_compliance_notes_initial = models.TextField(default="", blank=True)
    statement_compliance_state_initial = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    statement_compliance_notes_initial = models.TextField(default="", blank=True)
    website_compliance_state_12_week = models.CharField(
        max_length=200,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    website_compliance_notes_12_week = models.TextField(default="", blank=True)
    statement_compliance_state_12_week = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    statement_compliance_notes_12_week = models.TextField(default="", blank=True)

    def __str__(self) -> str:
        return (
            f"Website: {self.get_website_compliance_state_initial_display()}->"
            f"{self.get_website_compliance_state_12_week_display()}; "
            f"Statement: {self.get_statement_compliance_state_initial_display()}->"
            f"{self.get_statement_compliance_state_12_week_display()}"
        )


class Contact(VersionModel):
    """
    Model for cases Contact
    """

    class Preferred(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Not known"

    simplified_case = models.ForeignKey(SimplifiedCase, on_delete=models.PROTECT)
    name = models.TextField(default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    email = models.CharField(max_length=200, default="", blank=True)
    preferred = models.CharField(
        max_length=20, choices=Preferred.choices, default=Preferred.UNKNOWN
    )
    created = models.DateTimeField()
    updated = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-preferred", "-id"]

    def __str__(self) -> str:
        return f"{self.name} {self.email}".strip()

    def get_absolute_url(self) -> str:
        return reverse(
            "simplified:manage-contact-details", kwargs={"pk": self.simplified_case.id}
        )

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

    simplified_case = models.ForeignKey(SimplifiedCase, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=100, choices=EventType.choices, default=EventType.CREATE
    )
    message = models.TextField(default="Created case", blank=True)
    done_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
    )
    event_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event_time"]

    def __str__(self) -> str:
        return f"{self.simplified_case.organisation_name}: {self.message}"


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

    simplified_case = models.ForeignKey(SimplifiedCase, on_delete=models.PROTECT)
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
        return f"Equality body correspondence #{self.id_within_case}"

    def get_absolute_url(self) -> str:
        return reverse(
            "simplified:list-equality-body-correspondence",
            kwargs={"pk": self.simplified_case.id},
        )

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        if not self.id:
            self.created = timezone.now()
            self.id_within_case = (
                self.simplified_case.equalitybodycorrespondence_set.all().count() + 1
            )
        super().save(*args, **kwargs)


class ZendeskTicket(models.Model):
    """
    Model for simplified ZendeskTicket
    """

    simplified_case = models.ForeignKey(SimplifiedCase, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=1, blank=True)
    url = models.TextField(default="", blank=True)
    summary = models.TextField(default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.url

    def get_absolute_url(self) -> str:
        return reverse("simplified:update-zendesk-ticket", kwargs={"pk": self.id})

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.id_within_case = (
                self.simplified_case.zendeskticket_set.all().count() + 1
            )
        super().save(*args, **kwargs)


class SimplifiedEventHistory(models.Model):
    """Model to record events on platform"""

    class Type(models.TextChoices):
        UPDATE = "model_update", "Model update"
        CREATE = "model_create", "Model create"

    simplified_case = models.ForeignKey(
        SimplifiedCase, on_delete=models.PROTECT, null=True, blank=True
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    event_type = models.CharField(
        max_length=100, choices=Type.choices, default=Type.UPDATE
    )
    difference = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.simplified_case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Event histories"

    @property
    def variables(self):
        differences: dict[str, int | str] = json.loads(self.difference)

        variable_list: list[dict[str, int | str]] = []
        for key, value in differences.items():
            if self.event_type == SimplifiedEventHistory.Type.CREATE:
                old_value: str = ""
                new_value: int | str = value
            else:
                old_value, new_value = value.split(UPDATE_SEPARATOR, maxsplit=1)
            variable_list.append(
                {
                    "name": key,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )
        return variable_list
