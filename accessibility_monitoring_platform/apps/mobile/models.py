"""
Models - mobile cases
"""

import json
from datetime import date

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
from ..common.models import ZENDESK_URL_PREFIX, Boolean, CaseHistory, VersionModel
from ..common.utils import extract_domain_from_url

IOS_ANDROID_SEPARATOR: str = "\n\n"


def format_ios_and_android_str(ios: str, android: str) -> str:
    """Return string combining iOS and Android string values"""
    if ios == "":
        ios = "n/a"
    if android == "":
        android = "n/a"
    return f"iOS: {ios}{IOS_ANDROID_SEPARATOR}Android: {android}"


class MobileCase(BaseCase):
    """
    Model for MobileCase
    """

    class TestIncluded(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        NOT_KNOWN = "not-known", "Not known"

    class AppCompliance(models.TextChoices):
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
    ios_test_included = models.CharField(
        max_length=20, choices=TestIncluded.choices, default=TestIncluded.NOT_KNOWN
    )
    ios_app_url = models.TextField(default="", blank=True)
    android_test_included = models.CharField(
        max_length=20, choices=TestIncluded.choices, default=TestIncluded.NOT_KNOWN
    )
    android_app_url = models.TextField(default="", blank=True)
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

    # Initial test - Auditor
    # auditor
    initial_auditor_complete_date = models.DateField(null=True, blank=True)

    # Initial test - iOS details
    # ios_test_included
    # ios_app_url
    initial_ios_test_start_date = models.DateField(null=True, blank=True)
    initial_ios_details_complete_date = models.DateField(null=True, blank=True)

    # Initial test - iOS outcome
    initial_ios_test_end_date = models.DateField(null=True, blank=True)
    initial_ios_total_number_of_screens = models.IntegerField(null=True, blank=True)
    initial_ios_total_number_of_issues = models.IntegerField(null=True, blank=True)
    initial_ios_app_compliance_state = models.CharField(
        max_length=20,
        choices=AppCompliance.choices,
        default=AppCompliance.UNKNOWN,
    )
    initial_ios_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    initial_ios_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    initial_ios_outcome_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Android details
    # android_test_included
    # android_app_url
    initial_android_test_start_date = models.DateField(null=True, blank=True)
    initial_android_details_complete_date = models.DateField(null=True, blank=True)

    # Initial test - Android outcome
    initial_android_test_end_date = models.DateField(null=True, blank=True)
    initial_android_total_number_of_screens = models.IntegerField(null=True, blank=True)
    initial_android_total_number_of_issues = models.IntegerField(null=True, blank=True)
    initial_android_app_compliance_state = models.CharField(
        max_length=20,
        choices=AppCompliance.choices,
        default=AppCompliance.UNKNOWN,
    )
    initial_android_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    initial_android_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    initial_android_outcome_complete_date = models.DateField(null=True, blank=True)

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
    equality_body_report_url_ios = models.TextField(default="", blank=True)
    equality_body_report_url_android = models.TextField(default="", blank=True)
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

    # Correspondence - Report received
    twelve_week_received_date = models.DateField(null=True, blank=True)
    twelve_week_received_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - iOS retesting
    retest_ios_start_date = models.DateField(null=True, blank=True)
    retest_ios_total_number_of_issues = models.IntegerField(null=True, blank=True)
    retest_ios_result_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - iOS retest result
    retest_ios_app_compliance_state = models.CharField(
        max_length=20,
        choices=AppCompliance.choices,
        default=AppCompliance.UNKNOWN,
    )
    retest_ios_app_compliance_information = models.TextField(default="", blank=True)
    retest_ios_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    retest_ios_statement_compliance_information = models.TextField(
        default="", blank=True
    )
    retest_ios_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    retest_ios_disproportionate_burden_information = models.TextField(
        default="", blank=True
    )
    retest_ios_compliance_decisions_complete_date = models.DateField(
        null=True, blank=True
    )

    # Reviewing changes - Android retesting
    retest_android_start_date = models.DateField(null=True, blank=True)
    retest_android_total_number_of_issues = models.IntegerField(null=True, blank=True)
    retest_android_result_complete_date = models.DateField(null=True, blank=True)

    # Reviewing changes - Android retest result
    retest_android_app_compliance_state = models.CharField(
        max_length=20,
        choices=AppCompliance.choices,
        default=AppCompliance.UNKNOWN,
    )
    retest_android_app_compliance_information = models.TextField(default="", blank=True)
    retest_android_statement_compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    retest_android_statement_compliance_information = models.TextField(
        default="", blank=True
    )
    retest_android_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    retest_android_disproportionate_burden_information = models.TextField(
        default="", blank=True
    )
    retest_android_compliance_decisions_complete_date = models.DateField(
        null=True, blank=True
    )

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
        return f"{self.organisation_name} | {self.case_identifier}"

    def save(self, *args, **kwargs) -> None:
        if not self.domain and self.home_page_url:
            self.domain = extract_domain_from_url(self.home_page_url)
        if self.test_type != BaseCase.TestType.MOBILE:
            self.test_type = BaseCase.TestType.MOBILE
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title = f"{self.app_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    @property
    def name_prefix(self) -> str:
        name_prefix: str = self.app_name if self.app_name else "None"
        return name_prefix

    def status_history(self) -> QuerySet["MobileCaseHistory"]:
        return self.mobilecasehistory_set.filter(
            event_type=MobileCaseHistory.EventType.STATUS
        )

    def notes_history(self) -> QuerySet["MobileCaseHistory"]:
        return self.mobilecasehistory_set.filter(
            event_type=MobileCaseHistory.EventType.NOTE
        )

    @property
    def zendesk_tickets(self) -> QuerySet["MobileZendeskTicket"]:
        return self.mobile_zendesktickets.filter(is_deleted=False)

    @property
    def most_recent_history(self):
        return self.mobilecasehistory_set.first()

    @property
    def contacts(self) -> QuerySet["MobileContact"]:
        return self.mobile_contacts.filter(is_deleted=False)

    @property
    def contact_exists(self) -> bool:
        return self.contacts.exists()

    @property
    def manage_contacts_url(self) -> str:
        return reverse("mobile:manage-contact-details", kwargs={"pk": self.id})

    @property
    def preferred_contacts(self) -> QuerySet["MobileContact"]:
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
    def retest_start_date(self) -> date | None:
        if self.retest_ios_start_date and self.retest_android_start_date:
            if self.retest_ios_start_date < self.retest_android_start_date:
                return self.retest_ios_start_date
            return self.retest_android_start_date
        if self.retest_ios_start_date:
            return self.retest_ios_start_date
        if self.retest_android_start_date:
            return self.retest_android_start_date

    @property
    def initial_total_number_of_issues(self) -> int:
        number_of_issues: int = 0
        if self.initial_ios_total_number_of_issues is not None:
            number_of_issues += self.initial_ios_total_number_of_issues
        if self.initial_android_total_number_of_issues is not None:
            number_of_issues += self.initial_android_total_number_of_issues
        return number_of_issues

    @property
    def retest_total_number_of_issues_unfixed(self) -> int:
        number_of_issues: int = 0
        if self.retest_ios_total_number_of_issues is not None:
            number_of_issues += self.retest_ios_total_number_of_issues
        if self.retest_android_total_number_of_issues is not None:
            number_of_issues += self.retest_android_total_number_of_issues
        return number_of_issues

    @property
    def number_of_issues_fixed(self) -> int:
        return (
            self.initial_total_number_of_issues
            - self.retest_total_number_of_issues_unfixed
        )

    @property
    def percentage_of_issues_fixed(self) -> int | None:
        if self.initial_total_number_of_issues > 0:
            return int(
                self.number_of_issues_fixed * 100 / self.initial_total_number_of_issues
            )
        return 0

    @property
    def percentage_of_ios_issues_fixed(self) -> int | str:
        if (
            self.initial_ios_total_number_of_issues is not None
            and self.retest_ios_total_number_of_issues is not None
        ):
            number_of_ios_issues_fixed: int = (
                self.initial_ios_total_number_of_issues
                - self.retest_ios_total_number_of_issues
            )
            if self.initial_ios_total_number_of_issues > 0:
                return int(
                    number_of_ios_issues_fixed
                    * 100
                    / self.initial_ios_total_number_of_issues
                )
            else:
                return 100
        return "None"

    @property
    def percentage_of_android_issues_fixed(self) -> int | str:
        if (
            self.initial_android_total_number_of_issues is not None
            and self.retest_android_total_number_of_issues is not None
        ):
            number_of_android_issues_fixed: int = (
                self.initial_android_total_number_of_issues
                - self.retest_android_total_number_of_issues
            )
            if self.initial_android_total_number_of_issues > 0:
                return int(
                    number_of_android_issues_fixed
                    * 100
                    / self.initial_android_total_number_of_issues
                )
            else:
                return 100
        return "None"

    @property
    def equality_body_export_statement_found_at_retest(self) -> str:
        if self.retest_ios_statement_compliance_state in [
            MobileCase.StatementCompliance.COMPLIANT,
            MobileCase.StatementCompliance.NOT_COMPLIANT,
        ]:
            ios: str = "Yes"
        else:
            ios: str = "No"
        if self.retest_android_statement_compliance_state in [
            MobileCase.StatementCompliance.COMPLIANT,
            MobileCase.StatementCompliance.NOT_COMPLIANT,
        ]:
            android: str = "Yes"
        else:
            android: str = "No"
        return format_ios_and_android_str(ios=ios, android=android)

    @property
    def equality_body_report_urls(self) -> str:
        return format_ios_and_android_str(
            ios=self.equality_body_report_url_ios,
            android=self.equality_body_report_url_android,
        )

    @property
    def retest_statement_compliance_state(self) -> str:
        return format_ios_and_android_str(
            ios=self.get_retest_ios_statement_compliance_state_display(),
            android=self.get_retest_android_statement_compliance_state_display(),
        )

    @property
    def retest_disproportionate_burden_claim(self) -> str:
        return format_ios_and_android_str(
            ios=self.get_retest_ios_disproportionate_burden_claim_display(),
            android=self.get_retest_android_disproportionate_burden_claim_display(),
        )

    @property
    def retest_disproportionate_burden_information(self) -> str:
        return format_ios_and_android_str(
            ios=self.retest_ios_disproportionate_burden_information,
            android=self.retest_android_disproportionate_burden_information,
        )

    @property
    def email_template_list_url(self) -> str:
        return reverse("mobile:email-template-list", kwargs={"case_id": self.id})

    @property
    def email_template_preview_url_name(self) -> str:
        return "mobile:email-template-preview"

    @property
    def target_of_test(self) -> str:
        if (
            self.ios_test_included == MobileCase.TestIncluded.YES
            and self.android_test_included == MobileCase.TestIncluded.YES
        ):
            return "iOS/Android mobile application"
        elif self.ios_test_included == MobileCase.TestIncluded.YES:
            return "iOS mobile application"
        elif self.android_test_included == MobileCase.TestIncluded.YES:
            return "Android mobile application"
        return "mobile application"


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


class MobileCaseHistory(CaseHistory):
    """Model to record history of changes to MobileCase"""

    mobile_case = models.ForeignKey(MobileCase, on_delete=models.PROTECT)
    mobile_case_status = models.CharField(
        max_length=200,
        choices=MobileCase.Status.choices,
        default=MobileCase.Status.UNASSIGNED,
    )

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.mobile_case_status = self.mobile_case.status
            if self.event_type == MobileCaseHistory.EventType.NOTE:
                self.id_within_case = self.mobile_case.notes_history().count() + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mobile_case} {self.event_type} {self.created} {self.created_by}"

    class Meta:
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

    @property
    def email(self) -> str:
        return self.contact_details


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
            self.id_within_case = (
                self.mobile_case.mobile_zendesktickets.all().count() + 1
            )
        if self.url.startswith(ZENDESK_URL_PREFIX):
            zendesk_id: str = self.url.replace(ZENDESK_URL_PREFIX, "").replace("/", "")
            if zendesk_id.isdigit():
                self.id_within_case = int(zendesk_id)
        super().save(*args, **kwargs)
