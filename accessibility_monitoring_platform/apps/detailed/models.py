"""
Models - detailed cases
"""

import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.safestring import mark_safe

from ..cases.models import UPDATE_SEPARATOR, BaseCase, DetailedCaseStatus
from ..common.models import Boolean, VersionModel
from ..common.utils import extract_domain_from_url


class DetailedCase(BaseCase):
    """
    Model for DetailedCase
    """

    Status = DetailedCaseStatus

    class WebsiteCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Fully compliant"
        PARTIALLY = "partially-compliant", "Partially compliant"
        UNKNOWN = "not-known", "Not known"

    class DisproportionateBurden(models.TextChoices):
        NO_ASSESSMENT = "no-assessment", "Claim with no assessment"
        ASSESSMENT = "assessment", "Claim with assessment"
        NO_CLAIM = "no-claim", "No claim"
        NO_STATEMENT = "no-statement", "No statement"
        NOT_CHECKED = "not-checked", "Not checked"

    class StatementCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NOT_COMPLIANT = "not-compliant", "Not compliant or no statement"
        UNKNOWN = "unknown", "Not assessed"

    class ReportApprovedStatus(models.TextChoices):
        APPROVED = "yes", "Yes"
        IN_PROGRESS = "in-progress", "Further work is needed"
        NOT_STARTED = "not-started", "Not started"

    class CaseCloseDecision(models.TextChoices):
        COMPLETE_SEND = (
            "complete-send",
            "Case is complete and is ready to send to the equality body",
        )
        COMPLETE_NO_SEND = (
            "complete-no-send",
            "Case should not be sent to the equality body",
        )
        NO_DECISION = "no-decision", "Case still in progress"

    class EnforcementBodyClosedCase(models.TextChoices):
        YES = "yes", "Yes"
        IN_PROGRESS = "in-progress", "Case in progress"
        NO = "no", "No (or holding)"

    # status = models.CharField(
    #     max_length=30,
    #     choices=Status.choices,
    #     default=Status.INITIAL,
    # )

    # Case details - Case metadata
    previous_case_url = models.TextField(default="", blank=True)
    trello_url = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)
    case_metadata_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Manage contact details
    manage_contacts_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Request contact details
    first_contact_date = models.DateField(null=True, blank=True)
    first_contact_sent_to = models.CharField(max_length=200, default="", blank=True)
    request_contact_details_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Chasing contact record
    chasing_record_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Information delivered
    contact_acknowledged_date = models.DateField(null=True, blank=True)
    contact_acknowledged_by = models.CharField(max_length=200, default="", blank=True)
    saved_to_google_drive = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    information_delivered_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Testing details
    monitor_folder_url = models.TextField(default="", blank=True)
    initial_testing_details_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Testing outcome
    initial_test_date = models.DateField(null=True, blank=True)
    initial_total_number_of_issues = models.IntegerField(null=True, blank=True)
    initial_testing_outcome_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Website compliance
    initial_website_compliance_state = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    initial_website_compliance_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Disproportionate burden
    initial_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    initial_disproportionate_burden_complete_date = models.DateField(
        null=True, blank=True
    )

    # Initial test - Statement compliance
    initial_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    initial_statement_compliance_complete_date = models.DateField(null=True, blank=True)

    # Report - Report draft
    report_draft_url = models.TextField(default="", blank=True)
    report_ready_for_qa = models.CharField(
        max_length=20,
        choices=Boolean.choices,
        default=Boolean.NO,
    )
    report_draft_complete_date = models.DateField(null=True, blank=True)

    # Report - QA approval
    report_approved_status = models.CharField(
        max_length=200,
        choices=ReportApprovedStatus.choices,
        default=ReportApprovedStatus.NOT_STARTED,
    )
    qa_approval_complete_date = models.DateField(null=True, blank=True)

    # Report - Publish report
    equality_body_report_url = models.TextField(default="", blank=True)
    public_report_url = models.TextField(default="", blank=True)
    publish_report_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report sent
    report_sent_date = models.DateField(null=True, blank=True)
    report_sent_to = models.CharField(max_length=200, default="", blank=True)
    report_sent_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report acknowledged
    report_acknowledged_date = models.DateField(null=True, blank=True)
    report_acknowledged_by = models.CharField(max_length=200, default="", blank=True)
    report_acknowledged_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - 12-week deadline
    twelve_week_deadline_date = models.DateField(null=True, blank=True)
    twelve_week_deadline_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - 12-week update request
    twelve_week_update_date = models.DateField(null=True, blank=True)
    twelve_week_update_to = models.CharField(max_length=200, default="", blank=True)
    twelve_week_update_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report acknowledged
    twelve_week_acknowledged_date = models.DateField(null=True, blank=True)
    twelve_week_acknowledged_by = models.CharField(
        max_length=200, default="", blank=True
    )
    twelve_week_acknowledged_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Retest result
    retest_date = models.DateField(null=True, blank=True)
    retest_total_number_of_issues = models.IntegerField(null=True, blank=True)
    retest_result_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Summary of changes
    summary_of_changes_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Website compliance decision
    retest_website_compliance_state = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    retest_website_compliance_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Disproportionate burden
    retest_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    retest_disproportionate_burden_complete_date = models.DateField(
        null=True, blank=True
    )

    # Reviewing changes - Statement compliance
    retest_statement_backup_url = models.TextField(default="", blank=True)
    retest_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    retest_statement_compliance_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Final metrics
    number_of_days_to_retest = models.IntegerField(null=True, blank=True)
    retest_metrics_complete_date = models.DateField(null=True, blank=True)

    # Closing the case - Closing the case
    case_close_decision_state = models.CharField(
        max_length=30,
        choices=CaseCloseDecision.choices,
        default=CaseCloseDecision.NO_DECISION,
    )
    case_close_decision_notes = models.TextField(default="", blank=True)
    case_close_decision_sent_date = models.DateField(null=True, blank=True)
    case_close_decision_sent_to = models.CharField(
        max_length=200, default="", blank=True
    )
    is_feedback_survey_sent = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    case_close_complete_date = models.DateField(null=True, blank=True)

    # Post case - Equality body metadata
    enforcement_body_sent_date = models.DateField(null=True, blank=True)
    enforcement_body_started_date = models.DateField(null=True, blank=True)
    enforcement_body_case_owner = models.CharField(
        max_length=200, default="", blank=True
    )
    enforcement_body_closed_case_state = models.CharField(
        max_length=20,
        choices=EnforcementBodyClosedCase.choices,
        default=EnforcementBodyClosedCase.NO,
    )
    enforcement_body_completed_case_date = models.DateField(null=True, blank=True)
    is_case_added_to_stats = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    enforcement_body_metadata_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs) -> None:
        if not self.domain:
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.test_type != BaseCase.TestType.DETAILED:
            self.test_type = BaseCase.TestType.DETAILED
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title: str = ""
        if self.website_name:
            title += f"{self.website_name} &nbsp;|&nbsp; "
        title += f"{self.organisation_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    def status_history(self) -> QuerySet["DetailedCaseHistory"]:
        return self.detailedcasehistory_set.filter(
            event_type=DetailedCaseHistory.EventType.STATUS
        )

    def contact_notes_history(self) -> QuerySet["DetailedCaseHistory"]:
        return self.detailedcasehistory_set.filter(
            event_type=DetailedCaseHistory.EventType.CONTACT_NOTE
        )

    @property
    def contacts(self) -> QuerySet["Contact"]:
        return self.contact_set.filter(is_deleted=False)


class DetailedEventHistory(models.Model):
    """Model to record events on platform"""

    class Type(models.TextChoices):
        UPDATE = "model_update", "Model update"
        CREATE = "model_create", "Model create"

    detailed_case = models.ForeignKey(
        DetailedCase, on_delete=models.PROTECT, null=True, blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="detailed_case_event_content_type",
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    event_type = models.CharField(
        max_length=100, choices=Type.choices, default=Type.UPDATE
    )
    difference = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="detailed_case_event_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.detailed_case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Event histories"

    @property
    def variables(self):
        differences: dict[str, int | str] = json.loads(self.difference)

        variable_list: list[dict[str, int | str]] = []
        for key, value in differences.items():
            if self.event_type == DetailedEventHistory.Type.CREATE:
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


class DetailedCaseHistory(models.Model):
    """Model to record history of changes to DetailedCase"""

    class EventType(models.TextChoices):
        NOTE = "note", "Entered note"
        REMINDER = "reminder", "Reminder set"
        STATUS = "status", "Changed status"
        CONTACT_NOTE = "contact_note", "Entered contact note"

    detailed_case = models.ForeignKey(DetailedCase, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.NOTE
    )
    value = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.detailed_case} {self.event_type} {self.created} {self.created_by}"
        )

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Detailed Case history"


class Contact(VersionModel):
    """Model for detailed Contact"""

    class Preferred(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Not known"

    class Type(models.TextChoices):
        ORGANISATION = "organisation", "Organisation"
        CONTRACTOR = "contractor", "Contractor"

    detailed_case = models.ForeignKey(DetailedCase, on_delete=models.PROTECT)
    name = models.TextField(default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    contact_point = models.CharField(max_length=200, default="", blank=True)
    preferred = models.CharField(
        max_length=20, choices=Preferred.choices, default=Preferred.UNKNOWN
    )
    type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.ORGANISATION
    )
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-preferred", "-id"]

    def __str__(self) -> str:
        string: str = ""
        if self.name:
            string = self.name
        if self.contact_point:
            string += f" {self.contact_point}"
        return string

    def get_absolute_url(self) -> str:
        return reverse(
            "detailed:manage-contact-details", kwargs={"pk": self.detailed_case.id}
        )
