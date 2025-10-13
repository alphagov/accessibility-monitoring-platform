"""
Models - mobile cases
"""

import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.safestring import mark_safe

from ..cases.models import (
    UPDATE_SEPARATOR,
    BaseCase,
    MobileCaseStatus,
    get_previous_case_identifier,
)
from ..common.models import ZENDESK_URL_PREFIX, Boolean, VersionModel
from ..common.utils import extract_domain_from_url


class MobileCase(BaseCase):
    """
    Model for MobileCase
    """

    class AppOS(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    class WebsiteCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Fully compliant"
        PARTIALLY = "partially-compliant", "Partially compliant"
        NOT = "not-compliant", "Not compliant"
        UNKNOWN = "not-known", "Not known"

    class StatementCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NOT_COMPLIANT = "not-compliant", "Not compliant"
        NO_STATEMENT = "no-statement", "No statement"
        UNKNOWN = "unknown", "Not assessed"

    class DisproportionateBurden(models.TextChoices):
        NO_ASSESSMENT = "no-assessment", "Claim with no assessment"
        ASSESSMENT = "assessment", "Claim with assessment"
        NO_CLAIM = "no-claim", "No claim"
        NO_STATEMENT = "no-statement", "No statement"
        NOT_CHECKED = "not-checked", "Not checked"

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

    Status = MobileCaseStatus

    # Case metadata page
    app_name = models.TextField(default="", blank=True)
    app_store_url = models.TextField(default="", blank=True)
    app_os = models.CharField(
        max_length=20,
        choices=AppOS.choices,
        default=AppOS.IOS,
    )
    case_folder_url = models.TextField(default="", blank=True)
    previous_case_url = models.TextField(default="", blank=True)
    trello_url = models.TextField(default="", blank=True)
    case_metadata_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Manage contact details
    manage_contacts_complete_date = models.DateField(null=True, blank=True)

    # Initial contact - Request contact details
    contact_information_request_start_date = models.DateField(null=True, blank=True)
    contact_information_request_end_date = models.DateField(null=True, blank=True)
    contact_information_request_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Testing details
    initial_test_start_date = models.DateField(null=True, blank=True)
    initial_testing_details_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Testing outcome
    initial_test_end_date = models.DateField(null=True, blank=True)
    initial_total_number_of_pages = models.IntegerField(null=True, blank=True)
    initial_total_number_of_issues = models.IntegerField(null=True, blank=True)
    initial_website_compliance_state = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    initial_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    initial_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    initial_testing_outcome_complete_date = models.DateField(null=True, blank=True)

    # Report - Report ready for QA
    report_ready_for_qa = models.CharField(
        max_length=20,
        choices=Boolean.choices,
        default=Boolean.NO,
    )
    report_ready_for_qa_complete_date = models.DateField(null=True, blank=True)

    # Report - QA auditor
    qa_auditor_complete_date = models.DateField(null=True, blank=True)

    # Report - QA comments

    # Report - QA approval
    report_approved_status = models.CharField(
        max_length=200,
        choices=ReportApprovedStatus.choices,
        default=ReportApprovedStatus.NOT_STARTED,
    )
    qa_approval_complete_date = models.DateField(null=True, blank=True)

    # Report - Final report
    equality_body_report_url = models.TextField(default="", blank=True)
    final_report_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report sent
    report_sent_date = models.DateField(null=True, blank=True)
    report_sent_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report acknowledged
    report_acknowledged_date = models.DateField(null=True, blank=True)
    report_acknowledged_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - 12-week deadline
    twelve_week_deadline_date = models.DateField(null=True, blank=True)
    twelve_week_deadline_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - 12-week update request
    twelve_week_update_date = models.DateField(null=True, blank=True)
    twelve_week_update_complete_date = models.DateField(null=True, blank=True)

    # Correspondence - Report acknowledged
    twelve_week_acknowledged_date = models.DateField(null=True, blank=True)
    twelve_week_acknowledged_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Retest result
    retest_start_date = models.DateField(null=True, blank=True)
    retest_total_number_of_issues = models.IntegerField(null=True, blank=True)
    retest_result_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Retest compliance decisions
    retest_website_compliance_state = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    retest_website_compliance_information = models.TextField(default="", blank=True)
    retest_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    retest_statement_compliance_information = models.TextField(default="", blank=True)
    retest_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    retest_disproportionate_burden_information = models.TextField(
        default="", blank=True
    )
    retest_compliance_decisions_complete_date = models.DateField(null=True, blank=True)

    # Closing the case - Recommendation
    psb_progress_info = models.TextField(default="", blank=True)
    recommendation_decision_sent_date = models.DateField(null=True, blank=True)
    recommendation_decision_sent_to = models.CharField(
        max_length=200, default="", blank=True
    )
    recommendation_info = models.TextField(default="", blank=True)
    case_close_decision_notes = models.TextField(default="", blank=True)
    # is_feedback_requested from case metadata
    case_recommendation_complete_date = models.DateField(null=True, blank=True)

    # Closing the case - Closing the case
    case_close_decision_state = models.CharField(
        max_length=30,
        choices=CaseCloseDecision.choices,
        default=CaseCloseDecision.NO_DECISION,
    )
    case_close_complete_date = models.DateField(null=True, blank=True)

    # Post case - statement enforcement
    psb_statement_appeal_information = models.TextField(default="", blank=True)
    statement_enforcement_complete_date = models.DateField(null=True, blank=True)

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

    # Unresponsive PSB page
    no_psb_contact = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    no_psb_contact_info = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.app_name} | {self.case_identifier}"

    def save(self, *args, **kwargs) -> None:
        if not self.domain:
            self.domain = extract_domain_from_url(self.app_store_url)
        if self.test_type != BaseCase.TestType.MOBILE:
            self.test_type = BaseCase.TestType.MOBILE
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title = f"{self.app_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    def status_history(self) -> QuerySet["MobileCaseHistory"]:
        return self.detailedcasehistory_set.filter(
            event_type=MobileCaseHistory.EventType.STATUS
        )

    def notes_history(self) -> QuerySet["MobileCaseHistory"]:
        return self.detailedcasehistory_set.filter(
            event_type=MobileCaseHistory.EventType.NOTE
        )

    @property
    def zendesk_tickets(self) -> QuerySet["ZendeskTicket"]:
        return self.mobile_zendesktickets.filter(is_deleted=False)

    @property
    def most_recent_history(self):
        return self.detailedcasehistory_set.first()

    @property
    def contacts(self) -> QuerySet["Contact"]:
        return self.mobile_contacts.filter(is_deleted=False)

    @property
    def preferred_contacts(self) -> QuerySet["Contact"]:
        return self.contacts.filter(preferred=MobileContact.Preferred.YES)

    @property
    def previous_case_identifier(self) -> str:
        return get_previous_case_identifier(previous_case_url=self.previous_case_url)

    @property
    def equality_body_export_contact_details(self) -> str:
        """
        Concatenate the values for all the contacts and return as a single string.
        """
        contacts_string: str = ""
        for contact in self.contacts:
            if contacts_string:
                contacts_string += "\n"
            if contact.name:
                contacts_string += f"{contact.name}\n"
            if contact.job_title:
                contacts_string += f"{contact.job_title}\n"
            if contact.contact_details:
                contacts_string += f"{contact.contact_details}\n"
            if contact.information:
                contacts_string += f"{contact.information}\n"
        return contacts_string

    @property
    def report_acknowledged_yes_no(self) -> str:
        return (
            "Yes"
            if self.report_acknowledged_date and self.no_psb_contact == Boolean.NO
            else "No"
        )

    @property
    def number_of_issues_fixed(self) -> int | None:
        if self.initial_total_number_of_issues and self.retest_total_number_of_issues:
            return (
                self.initial_total_number_of_issues - self.retest_total_number_of_issues
            )

    @property
    def percentage_of_issues_fixed(self) -> int | None:
        if self.initial_total_number_of_issues and self.number_of_issues_fixed:
            return int(
                self.number_of_issues_fixed * 100 / self.initial_total_number_of_issues
            )

    @property
    def equality_body_export_statement_found_at_retest(self) -> str:
        if self.retest_statement_compliance_state in [
            MobileCase.StatementCompliance.COMPLIANT,
            MobileCase.StatementCompliance.NOT_COMPLIANT,
        ]:
            return "Yes"
        return "No"


class EventHistory(models.Model):
    """Model to record events on platform"""

    class Type(models.TextChoices):
        UPDATE = "model_update", "Model update"
        CREATE = "model_create", "Model create"

    mobile_case = models.ForeignKey(
        MobileCase, on_delete=models.PROTECT, null=True, blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="mobile_case_event_content_type",
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
        related_name="mobile_case_event_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.mobile_case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Event histories"

    @property
    def variables(self):
        differences: dict[str, int | str] = json.loads(self.difference)

        variable_list: list[dict[str, int | str]] = []
        for key, value in differences.items():
            if self.event_type == EventHistory.Type.CREATE:
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


class MobileCaseHistory(models.Model):
    """Model to record history of changes to MobileCase"""

    class EventType(models.TextChoices):
        NOTE = "note", "Entered note"
        STATUS = "status", "Changed status"
        RECOMMENDATION = "recommendation", "Entered enforcement recommendation"

    mobile_case = models.ForeignKey(MobileCase, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.NOTE
    )
    value = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.mobile_case} {self.event_type} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-id"]
        verbose_name_plural = "Mobile Case history"


class MobileContact(VersionModel):
    """Model for mobile Contact"""

    class Preferred(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Not known"

    mobile_case = models.ForeignKey(
        MobileCase, on_delete=models.PROTECT, related_name="mobile_contacts"
    )
    name = models.TextField(default="", blank=True)
    job_title = models.CharField(max_length=200, default="", blank=True)
    contact_details = models.TextField(default="", blank=True)
    information = models.TextField(default="", blank=True)
    preferred = models.CharField(
        max_length=20, choices=Preferred.choices, default=Preferred.UNKNOWN
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
        if self.contact_details:
            string += f" {self.contact_details}"
        return string

    def get_absolute_url(self) -> str:
        return reverse(
            "mobile:manage-contact-details", kwargs={"pk": self.mobile_case.id}
        )


class MobileZendeskTicket(models.Model):
    """
    Model for mobile ZendeskTicket
    """

    mobile_case = models.ForeignKey(
        MobileCase, on_delete=models.PROTECT, related_name="mobile_zendesktickets"
    )
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
        return reverse("mobile:update-zendesk-ticket", kwargs={"pk": self.id})

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.id_within_case = self.mobile_case.zendeskticket_set.all().count() + 1
        if self.url.startswith(ZENDESK_URL_PREFIX):
            zendesk_id: str = self.url.replace(ZENDESK_URL_PREFIX, "").replace("/", "")
            if zendesk_id.isdigit():
                self.id_within_case = int(zendesk_id)
        super().save(*args, **kwargs)
