"""
Forms - cases
"""
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from ..common.forms import (
    AMPRadioSelectWidget,
    AMPCheckboxWidget,
    AMPUserModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPModelChoiceField,
    AMPModelMultipleChoiceField,
    AMPBooleanField,
    AMPDateField,
    AMPDateRangeForm,
)
from .models import (
    Case,
    Contact,
    CASE_ORIGIN_CHOICES,
    STATUS_CHOICES,
    TEST_TYPE_CHOICES,
    WEBSITE_TYPE_CHOICES,
    TEST_STATUS_CHOICES,
    REPORT_REVIEW_STATUS_CHOICES,
    REPORT_APPROVED_STATUS_CHOICES,
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    COMPLIANCE_DECISION_CHOICES,
)
from ..common.models import Region, Sector

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

SORT_CHOICES = [
    ("-id", "Newest"),
    ("id", "Oldest"),
]


class CaseSearchForm(AMPDateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    case_number = AMPCharField(label="Case number")
    domain = AMPCharField(label="Domain")
    organisation = AMPCharField(label="Organisation")
    auditor = AMPUserModelChoiceField(label="Auditor")
    status = AMPChoiceField(label="Status", choices=status_choices)


class CaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    auditor = AMPUserModelChoiceField(label="Auditor")
    test_type = AMPChoiceField(
        label="Test type",
        choices=TEST_TYPE_CHOICES,
        widget=AMPRadioSelectWidget,
        initial="simple",
    )
    home_page_url = AMPCharFieldWide(
        label="Full URL",
        help_text="E.g. https://example.com",
        required=True,
    )
    organisation_name = AMPCharFieldWide(label="Organisation name")
    service_name = AMPCharFieldWide(label="Service name")
    website_type = AMPChoiceField(
        label="Type of site",
        choices=WEBSITE_TYPE_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    region = AMPModelMultipleChoiceField(
        label="Region",
        queryset=Region.objects.all(),
    )
    case_origin = AMPChoiceField(
        label="Case origin", choices=CASE_ORIGIN_CHOICES, widget=AMPRadioSelectWidget
    )
    zendesk_url = AMPCharFieldWide(label="Zendesk ticket URL")
    trello_url = AMPCharFieldWide(label="Trello ticket URL")
    notes = AMPTextField(label="Notes")
    is_public_sector_body = AMPBooleanField(
        label="Public sector body?",
        help_text="If you later find out the organisation is not a public sector body,"
        " unmark the checkbox, then save and exit to unlist the case.",
        widget=AMPCheckboxWidget(
            attrs={
                "label": "Untick this box to unlist the case",
            }
        ),
        initial=True,
    )

    class Meta:
        model = Case
        fields = [
            "auditor",
            "test_type",
            "home_page_url",
            "organisation_name",
            "service_name",
            "website_type",
            "sector",
            "region",
            "case_origin",
            "zendesk_url",
            "trello_url",
            "notes",
            "is_public_sector_body",
        ]

    def clean_home_page_url(self):
        data = self.cleaned_data["home_page_url"]
        if not (data.startswith("http://") or data.startswith("https://")):
            raise ValidationError("URL must start with http:// or https://")
        return data


class CaseWebsiteDetailUpdateForm(CaseCreateForm):
    """
    Form for updating website details fields of cases
    """

    domain = AMPCharFieldWide(label="Domain")

    class Meta:
        model = Case
        fields = [
            "auditor",
            "test_type",
            "home_page_url",
            "domain",
            "organisation_name",
            "service_name",
            "website_type",
            "sector",
            "region",
            "case_origin",
            "zendesk_url",
            "trello_url",
            "notes",
            "is_public_sector_body",
        ]


class CaseContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    first_name = AMPCharFieldWide(label="First name")
    last_name = AMPCharFieldWide(label="Last name")
    job_title = AMPCharFieldWide(label="Job title")
    detail = AMPCharFieldWide(label="Detail")
    preferred = AMPBooleanField(label="Preferred contact?")
    notes = AMPTextField(label="Notes")

    class Meta:
        model = Case
        fields = [
            "first_name",
            "last_name",
            "job_title",
            "detail",
            "preferred",
            "notes",
        ]


CaseContactFormset: Any = forms.modelformset_factory(
    Contact, CaseContactUpdateForm, extra=0
)
CaseContactFormsetOneExtra: Any = forms.modelformset_factory(
    Contact, CaseContactUpdateForm, extra=1
)


class CaseTestResultsUpdateForm(forms.ModelForm):
    """
    Form for updating test results
    """

    test_results_url = AMPCharFieldWide(label="Link to test results")
    test_status = AMPChoiceField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    is_website_compliant = AMPBooleanField(label="Is the website compliant?")
    test_notes = AMPTextField(label="Compliance notes")

    class Meta:
        model = Case
        fields = [
            "test_results_url",
            "test_status",
            "is_website_compliant",
            "test_notes",
        ]


class CaseReportDetailsUpdateForm(forms.ModelForm):
    """
    Form for updating report details
    """

    report_draft_url = AMPCharFieldWide(label="Link to report draft")
    report_review_status = AMPChoiceField(
        label="Report ready to be reviewed?",
        choices=REPORT_REVIEW_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    reviewer = AMPCharFieldWide(label="QA auditor")
    report_approved_status = AMPChoiceField(
        label="Report approved?",
        choices=REPORT_APPROVED_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_url = AMPCharFieldWide(label="Link to final report")
    report_sent_date = AMPDateField(label="Report sent on")
    report_acknowledged_date = AMPDateField(label="Report acknowledged")

    class Meta:
        model = Case
        fields = [
            "report_draft_url",
            "report_review_status",
            "reviewer",
            "report_approved_status",
            "reviewer_notes",
            "report_final_url",
            "report_sent_date",
            "report_acknowledged_date",
        ]


class CasePostReportUpdateForm(forms.ModelForm):
    """
    Form for updating post report details
    """

    week_12_followup_date = AMPDateField(label="12 week followup date")
    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    week_12_followup_email_sent_date = AMPDateField(label="12 week followup email sent")
    week_12_followup_email_acknowledgement_date = AMPDateField(
        label="12 week followup acknowledge"
    )
    is_website_retested = AMPBooleanField(label="Retested website?")
    is_disproportionate_claimed = AMPBooleanField(
        label="Disproportionate burden claimed?"
    )
    disproportionate_notes = AMPTextField(label="Disproportionate burden notes")
    accessibility_statement_decison = AMPChoiceField(
        label="Accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    accessibility_statement_url = AMPCharFieldWide(
        label="Link to new accessibility statement"
    )
    accessibility_statement_notes = AMPTextField(label="Accessibility statement notes")
    compliance_decision = AMPChoiceField(
        label="Compliance decision",
        choices=COMPLIANCE_DECISION_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    compliance_decision_notes = AMPTextField(label="Compliance decision notes")
    compliance_email_sent_date = AMPDateField(label="Compliance email sent?")
    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to enforcement body",
        help_text="If case does not need to be sent to enforcement body, this step can be skipped.",
    )
    is_case_completed = AMPBooleanField(label="Case completed?")

    class Meta:
        model = Case
        fields = [
            "week_12_followup_date",
            "psb_progress_notes",
            "week_12_followup_email_sent_date",
            "week_12_followup_email_acknowledgement_date",
            "is_website_retested",
            "is_disproportionate_claimed",
            "disproportionate_notes",
            "accessibility_statement_decison",
            "accessibility_statement_url",
            "accessibility_statement_notes",
            "compliance_decision",
            "compliance_decision_notes",
            "compliance_email_sent_date",
            "sent_to_enforcement_body_sent_date",
            "is_case_completed",
        ]
