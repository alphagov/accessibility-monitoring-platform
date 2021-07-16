"""
Forms - cases
"""
from typing import Any

from django import forms
from django.contrib.auth.models import User

from ..common.forms import (
    AMPCheckboxWidget,
    AMPRadioSelectWidget,
    AMPUserModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPModelChoiceField,
    AMPModelMultipleChoiceField,
    AMPBooleanField,
    AMPNullableBooleanField,
    AMPDateField,
    AMPDateSentField,
    AMPDateRangeForm,
    AMPURLField,
)
from .models import (
    Case,
    Contact,
    CASE_ORIGIN_CHOICES,
    STATUS_CHOICES,
    TEST_TYPE_CHOICES,
    DEFAULT_WEBSITE_TYPE,
    WEBSITE_TYPE_CHOICES,
    TEST_STATUS_CHOICES,
    REPORT_REVIEW_STATUS_CHOICES,
    REPORT_APPROVED_STATUS_CHOICES,
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    COMPLIANCE_DECISION_CHOICES,
    ARCHIVE_DECISION_CHOICES,
)
from ..common.models import Region, Sector

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

DEFAULT_SORT: str = "-id"
SORT_CHOICES = [
    (DEFAULT_SORT, "Newest"),
    ("id", "Oldest"),
]


class CaseSearchForm(AMPDateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    search = AMPCharField(label="Search")
    auditor = AMPChoiceField(label="Auditor")
    reviewer = AMPChoiceField(label="QA Auditor")
    status = AMPChoiceField(label="Status", choices=status_choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_choices_with_none = [
            ("", "-----"),
            ("none", "Unassigned"),
        ]
        for user in User.objects.all().order_by("first_name", "last_name"):
            user_choices_with_none.append((user.id, user.get_full_name()))

        self.fields["auditor"].choices = user_choices_with_none
        self.fields["reviewer"].choices = user_choices_with_none


class CaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name",
        help_text="Enter the name of the organisation",
    )
    home_page_url = AMPURLField(
        label="Full URL",
        help_text="Enter a domain if test type is simple or complex",
        required=True,
    )
    test_type = AMPChoiceField(
        label="Test type",
        choices=TEST_TYPE_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    case_origin = AMPChoiceField(
        label="Case origin", choices=CASE_ORIGIN_CHOICES, widget=AMPRadioSelectWidget
    )
    auditor = AMPUserModelChoiceField(label="Auditor")

    class Meta:
        model = Case
        fields = [
            "organisation_name",
            "home_page_url",
            "test_type",
            "case_origin",
            "auditor",
        ]


class CaseDetailUpdateForm(CaseCreateForm):
    """
    Form for updating case details fields
    """

    domain = AMPCharFieldWide(label="Domain")
    service_name = AMPCharFieldWide(label="Website, App or Service name")
    website_type = AMPChoiceField(
        label="Type of site",
        choices=WEBSITE_TYPE_CHOICES,
        initial=DEFAULT_WEBSITE_TYPE,
        widget=AMPRadioSelectWidget,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    region = AMPModelMultipleChoiceField(
        label="Region",
        queryset=Region.objects.all(),
    )
    trello_url = AMPURLField(label="Trello ticket URL")
    zendesk_url = AMPURLField(label="Zendesk ticket URL")
    notes = AMPTextField(label="Notes")

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
        ]


class CaseContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    first_name = AMPCharFieldWide(label="First name")
    last_name = AMPCharFieldWide(label="Last name")
    job_title = AMPCharFieldWide(label="Job title")
    detail = AMPCharFieldWide(
        label="Detail", help_text="E.g. email address or telephone number"
    )
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

    test_results_url = AMPURLField(label="Link to test results")
    test_status = AMPChoiceField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    is_website_compliant = AMPNullableBooleanField(label="Is the website compliant?")
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

    report_draft_url = AMPURLField(label="Link to report draft")
    report_review_status = AMPChoiceField(
        label="Report ready to be reviewed?",
        choices=REPORT_REVIEW_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    reviewer = AMPUserModelChoiceField(label="QA Auditor")
    report_approved_status = AMPChoiceField(
        label="Report approved?",
        choices=REPORT_APPROVED_STATUS_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_url = AMPURLField(label="Link to final report")
    report_sent_date = AMPDateField(label="Report sent on")

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
        ]


class CaseReportCorrespondanceUpdateForm(forms.ModelForm):
    """
    Form for updating report correspondance details
    """

    report_followup_week_1_sent_date = AMPDateSentField(label="1 week followup date")
    report_followup_week_4_sent_date = AMPDateSentField(label="4 week followup date")
    report_followup_week_7_sent_date = AMPDateSentField(label="7 week followup date")
    report_followup_week_12_sent_date = AMPDateSentField(label="12 week deadline")
    report_acknowledged_date = AMPDateField(label="Report acknowledged")
    correspondance_notes = AMPTextField(label="Correspondance notes")

    class Meta:
        model = Case
        fields = [
            "report_followup_week_1_sent_date",
            "report_followup_week_4_sent_date",
            "report_followup_week_7_sent_date",
            "report_followup_week_12_sent_date",
            "report_acknowledged_date",
            "correspondance_notes",
        ]


class CaseTwelveWeekCorrespondanceUpdateForm(forms.ModelForm):
    """
    Form for updating week twelve correspondance details
    """

    twelve_week_update_requested_sent_date = AMPDateSentField(label="12 week update requested")
    twelve_week_1_week_chaser_sent_date = AMPDateSentField(label="1 week chaser")
    twelve_week_4_week_chaser_sent_date = AMPDateSentField(label="4 week chaser")
    twelve_week_correspondance_acknowledged_date = AMPDateField(label="12 week correspondance acknowledged")
    correspondance_notes = AMPTextField(label="Correspondance notes")

    class Meta:
        model = Case
        fields = [
            "twelve_week_update_requested_sent_date",
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_4_week_chaser_sent_date",
            "twelve_week_correspondance_acknowledged_date",
            "correspondance_notes",
        ]


class CaseReportFollowupDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating report followup due dates
    """

    report_followup_week_1_due_date = AMPDateField(label="1 week followup")
    report_followup_week_4_due_date = AMPDateField(label="4 week followup")
    report_followup_week_7_due_date = AMPDateField(label="7 week followup")
    report_followup_week_12_due_date = AMPDateField(label="12 week deadline")

    class Meta:
        model = Case
        fields = [
            "report_followup_week_1_due_date",
            "report_followup_week_4_due_date",
            "report_followup_week_7_due_date",
            "report_followup_week_12_due_date",
        ]


class CaseArchiveForm(forms.ModelForm):
    """
    Form for archiving a case
    """

    archive_reason = AMPChoiceField(
        label="Reason why?",
        choices=ARCHIVE_DECISION_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    archive_notes = AMPTextField(label="More information?")

    class Meta:
        model = Case
        fields = [
            "archive_reason",
            "archive_notes",
        ]


class CaseNoPSBContactUpdateForm(forms.ModelForm):
    """
    Form for archiving a case
    """

    no_psb_contact = AMPBooleanField(
        widget=AMPCheckboxWidget(
            attrs={"label": "Move case onto equality bodies correspondance stage?"}
        )
    )

    class Meta:
        model = Case
        fields = [
            "no_psb_contact",
        ]


class CaseEnforcementBodyCorrespondanceUpdateForm(forms.ModelForm):
    """
    Form for recording correspondance with enforcement body
    """

    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to equality body"
    )
    enforcement_body_correspondance_notes = AMPTextField(
        label="Equality body correspondance notes"
    )
    is_case_completed = AMPBooleanField(
        label="Case completed?",
        widget=AMPCheckboxWidget(
            attrs={
                "label": "No further action is required and the case can be marked as complete"
            }
        ),
    )

    class Meta:
        model = Case
        fields = [
            "sent_to_enforcement_body_sent_date",
            "enforcement_body_correspondance_notes",
            "is_case_completed",
        ]


class CaseFinalDecisionUpdateForm(forms.ModelForm):
    """
    Form for updating case final decision details
    """

    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    is_website_retested = AMPBooleanField(label="Retested website?")
    is_disproportionate_claimed = AMPNullableBooleanField(
        label="Disproportionate burden claimed?"
    )
    disproportionate_notes = AMPTextField(label="Disproportionate burden notes")
    accessibility_statement_decison = AMPChoiceField(
        label="Accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    accessibility_statement_notes = AMPTextField(label="Accessibility statement notes")
    compliance_decision = AMPChoiceField(
        label="Compliance decision",
        choices=COMPLIANCE_DECISION_CHOICES,
        widget=AMPRadioSelectWidget,
    )
    compliance_decision_notes = AMPTextField(label="Compliance decision notes")
    compliance_email_sent_date = AMPDateField(label="Compliance email sent to PSB?")

    class Meta:
        model = Case
        fields = [
            "psb_progress_notes",
            "is_website_retested",
            "is_disproportionate_claimed",
            "disproportionate_notes",
            "accessibility_statement_decison",
            "accessibility_statement_notes",
            "compliance_decision",
            "compliance_decision_notes",
            "compliance_email_sent_date",
        ]
