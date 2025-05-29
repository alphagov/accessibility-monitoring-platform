"""
Models - detailed cases
"""

import json
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..cases.models import UPDATE_SEPARATOR
from ..common.models import Boolean, Sector, SubCategory, VersionModel
from ..common.utils import extract_domain_from_url


class DetailedCase(VersionModel):
    """
    Model for DetailedCase
    """

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

    class Status(models.TextChoices):
        INITIAL = "010_initial", "Initial"
        CONTACTING = "020_contacting", "Seeking to contact"
        AUDITING = "030_auditing", "Testing"
        REPORTING = "040_reporting", "Writing report"
        QA_REPORT = "050_qa_report", "QA in progress"
        AWAIT_RESPONSE = "060_await_response", "Awaiting response"
        REVIEWING_UPDATE = "070_reviewing_update", "Reviewing update"
        REQUIRES_DECISION = "080_requires_decision", "Requires decision"
        WAITING_12_WEEKS = "090_waiting_12_weeks", "Waiting for 12-weeks"

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

    case_number = models.IntegerField(default=1)
    created = models.DateTimeField(blank=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="detailed_case_created_by",
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="detailed_case_reviewer",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.INITIAL,
    )

    # Case details - Case metadata
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
    is_feedback_requested = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
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
    auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="detailed_case_auditor",
        blank=True,
        null=True,
    )
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

    # Initial test - disproportionate burden
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

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.organisation_name} | {self.case_identifier}"

    def get_absolute_url(self) -> str:
        return reverse("detailed:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs) -> None:
        now: datetime = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.home_page_url)
            max_case_number = DetailedCase.objects.aggregate(
                models.Max("case_number")
            ).get("case_number__max")
            if max_case_number is not None:
                self.case_number = max_case_number + 1
        self.updated = now
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title: str = ""
        if self.website_name:
            title += f"{self.website_name} &nbsp;|&nbsp; "
        title += f"{self.organisation_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    @property
    def case_identifier(self) -> str:
        return f"#D-{self.case_number}"

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


class EventHistory(models.Model):
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
        return f"{self.case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

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
