"""
Forms - cases
"""
from datetime import datetime
import pytz
from typing import Union

from django import forms

from ..common.forms import (
    AMPRadioSelectWidget,
    AMPCheckboxWidget,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
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

DEFAULT_START_DATE = datetime(year=1900, month=1, day=1, tzinfo=pytz.UTC)
DEFAULT_END_DATE = datetime(year=2100, month=1, day=1, tzinfo=pytz.UTC)

AUDITOR_CHOICES = [
    ("", ""),
    ("Andrew Hick", "Andrew Hick"),
    ("Jessica Eley", "Jessica Eley"),
    ("Katherine Badger", "Katherine Badger"),
    ("Kelly Clarkson", "Kelly Clarkson"),
    ("Keeley Robertson", "Keeley Robertson"),
    ("Nesha Russo", "Nesha Russo"),
]

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

SORT_CHOICES = [
    ("-id", "Newest"),
    ("id", "Oldest"),
]

StringOrNone = Union[str, None]


class CaseSearchForm(AMPDateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    case_number = AMPCharField(label="Case number", required=False)
    domain = AMPCharField(label="Domain", required=False)
    organisation = AMPCharField(label="Organisation", required=False)
    auditor = AMPChoiceField(label="Auditor", choices=AUDITOR_CHOICES, required=False)
    status = AMPChoiceField(label="Status", choices=status_choices, required=False)


class CaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    auditor = AMPCharFieldWide(label="Auditor", required=False)
    test_type = AMPChoiceField(
        label="Test type",
        choices=TEST_TYPE_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    home_page_url = AMPCharFieldWide(
        label="Full URL",
        required=False,
        help_text="Enter a domain if test type is simple or complex",
    )
    organisation_name = AMPCharFieldWide(label="Organisation name", required=False)
    website_type = AMPChoiceField(
        label="Type of site",
        choices=WEBSITE_TYPE_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    sector = AMPCharFieldWide(label="Sector", required=False)
    region = AMPCharFieldWide(label="Region", required=False)
    case_origin = AMPChoiceField(
        label="Case origin", choices=CASE_ORIGIN_CHOICES, widget=AMPRadioSelectWidget
    )
    zendesk_url = AMPCharFieldWide(label="Zendesk ticket URL", required=False)
    trello_url = AMPCharFieldWide(label="Trello ticket URL", required=False)
    notes = AMPTextField(label="Notes", required=False)
    is_public_sector_body = AMPBooleanField(
        label="Public sector body?",
        help_text="If you later find out the organisation is not a public sector body, unmark the checkbox, then save and exit to unlist the case.",
        widget=AMPCheckboxWidget(
            attrs={
                "label": "Untick this box to unlist the case",
            }
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "auditor",
            "test_type",
            "home_page_url",
            "organisation_name",
            "website_type",
            "sector",
            "region",
            "case_origin",
            "zendesk_url",
            "trello_url",
            "notes",
            "is_public_sector_body",
        ]


class CaseWebsiteDetailUpdateForm(CaseCreateForm):
    """
    Form for updating website details fields of cases
    """

    domain = AMPCharFieldWide(
        label="Domain",
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "auditor",
            "test_type",
            "home_page_url",
            "organisation_name",
            "domain",
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

    first_name = AMPCharFieldWide(label="First name", required=False)
    last_name = AMPCharFieldWide(label="Last name", required=False)
    job_title = AMPCharFieldWide(label="Job title", required=False)
    detail = AMPCharFieldWide(label="Detail", required=False)
    preferred = AMPBooleanField(
        label="Preferred contact?", widget=AMPCheckboxWidget(), required=False
    )
    notes = AMPTextField(label="Notes", required=False)

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


CaseContactFormset = forms.modelformset_factory(Contact, CaseContactUpdateForm, extra=0)
CaseContactFormsetOneExtra = forms.modelformset_factory(
    Contact, CaseContactUpdateForm, extra=1
)


class CaseTestResultsUpdateForm(forms.ModelForm):
    """
    Form for updating test results
    """

    test_results_url = AMPCharFieldWide(label="Link to test results", required=False)
    test_status = AMPChoiceField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    is_website_compliant = AMPBooleanField(
        label="Is the website compliant?", widget=AMPCheckboxWidget(), required=False
    )
    test_notes = AMPTextField(label="Compliance notes", required=False)

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

    report_draft_url = AMPCharFieldWide(label="Link to report draft", required=False)
    report_review_status = AMPChoiceField(
        label="Report ready to be reviewed?",
        choices=REPORT_REVIEW_STATUS_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    reviewer = AMPCharFieldWide(label="QA auditor", required=False)
    report_approved_status = AMPChoiceField(
        label="Report approved?",
        choices=REPORT_APPROVED_STATUS_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    reviewer_notes = AMPTextField(label="QA notes", required=False)
    report_final_url = AMPCharFieldWide(label="Link to final report", required=False)
    report_sent_date = AMPDateField(label="Report sent on", required=False)
    report_acknowledged_date = AMPDateField(label="Report acknowledged", required=False)

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

    week_12_followup_date = AMPDateField(label="12 week followup date", required=False)
    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body", required=False
    )
    week_12_followup_email_sent_date = AMPDateField(
        label="12 week followup email sent", required=False
    )
    week_12_followup_email_acknowledgement_date = AMPDateField(
        label="12 week followup acknowledge", required=False
    )
    is_website_retested = AMPBooleanField(
        label="Retested website?", widget=AMPCheckboxWidget(), required=False
    )
    is_disproportionate_claimed = AMPBooleanField(
        label="Disproportionate burden claimed?",
        widget=AMPCheckboxWidget(),
        required=False,
    )
    disproportionate_notes = AMPTextField(
        label="Disproportionate burden notes", required=False
    )
    accessibility_statement_decison = AMPChoiceField(
        label="Accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    accessibility_statement_url = AMPCharFieldWide(
        label="Link to new accessibility statement", required=False
    )
    accessibility_statement_notes = AMPTextField(
        label="Accessibility statement notes", required=False
    )
    compliance_decision = AMPChoiceField(
        label="Compliance decision",
        choices=COMPLIANCE_DECISION_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    compliance_decision_notes = AMPTextField(
        label="Compliance decision notes", required=False
    )
    compliance_email_sent_date = AMPDateField(
        label="Compliance email sent?", required=False
    )
    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to enforcement body",
        help_text="If case does not need to be sent to enforcement body, this step can be skipped.",
        required=False,
    )
    is_case_completed = AMPBooleanField(
        label="Case completed?", widget=AMPCheckboxWidget(), required=False
    )

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
