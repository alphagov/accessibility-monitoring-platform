"""
Forms - cases
"""
from typing import Any

from django import forms
from django.contrib.auth.models import User

from ..common.forms import (
    AMPUserModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPModelChoiceField,
    AMPChoiceRadioField,
    AMPModelMultipleChoiceField,
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
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    COMPLIANCE_DECISION_CHOICES,
    ARCHIVE_DECISION_CHOICES,
    CASE_COMPLETED_CHOICES,
    ESCALATION_STATE_CHOICES,
    PREFERRED_CHOICES,
    IS_WEBSITE_COMPLIANT_CHOICES,
    BOOLEAN_CHOICES,
    IS_DISPROPORTIONATE_CLAIMED_CHOICES,
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
    test_type = AMPChoiceRadioField(
        label="Test type",
        choices=TEST_TYPE_CHOICES,
    )
    case_origin = AMPChoiceRadioField(label="Case origin", choices=CASE_ORIGIN_CHOICES)
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
    website_type = AMPChoiceRadioField(
        label="Type of site",
        choices=WEBSITE_TYPE_CHOICES,
        initial=DEFAULT_WEBSITE_TYPE,
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
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=PREFERRED_CHOICES
    )
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
    test_status = AMPChoiceRadioField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
    )
    is_website_compliant = AMPChoiceRadioField(
        label="Is the website compliant?", choices=IS_WEBSITE_COMPLIANT_CHOICES
    )
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
    report_is_ready_to_review = AMPChoiceRadioField(
        label="Is report ready to be reviewed?", choices=IS_WEBSITE_COMPLIANT_CHOICES
    )
    reviewer = AMPUserModelChoiceField(label="QA Auditor")
    report_is_approved = AMPChoiceRadioField(
        label="Is report approved", choices=BOOLEAN_CHOICES
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_url = AMPURLField(label="Link to final report")
    report_sent_date = AMPDateField(label="Report sent on")

    class Meta:
        model = Case
        fields = [
            "report_draft_url",
            "report_is_ready_to_review",
            "reviewer",
            "report_is_approved",
            "reviewer_notes",
            "report_final_url",
            "report_sent_date",
        ]


class CaseReportCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for updating report correspondence details
    """

    report_followup_week_1_sent_date = AMPDateSentField(label="1 week followup date")
    report_followup_week_4_sent_date = AMPDateSentField(label="4 week followup date")
    report_followup_week_7_sent_date = AMPDateSentField(label="7 week followup date")
    report_followup_week_12_sent_date = AMPDateSentField(label="12 week deadline")
    report_acknowledged_date = AMPDateField(label="Report acknowledged")
    correspondence_notes = AMPTextField(label="Correspondence notes")

    class Meta:
        model = Case
        fields = [
            "report_followup_week_1_sent_date",
            "report_followup_week_4_sent_date",
            "report_followup_week_7_sent_date",
            "report_followup_week_12_sent_date",
            "report_acknowledged_date",
            "correspondence_notes",
        ]


class CaseReportFollowupDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating report followup due dates
    """

    report_followup_week_1_due_date = AMPDateField(label="1 week followup")
    report_followup_week_4_due_date = AMPDateField(label="4 week followup")
    report_followup_week_12_due_date = AMPDateField(label="12 week deadline")

    class Meta:
        model = Case
        fields = [
            "report_followup_week_1_due_date",
            "report_followup_week_4_due_date",
            "report_followup_week_12_due_date",
        ]


class CaseTwelveWeekCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for updating week twelve correspondence details
    """

    report_followup_week_12_sent_date = AMPDateSentField(
        label="12 week update requested"
    )
    twelve_week_1_week_chaser_sent_date = AMPDateSentField(label="1 week chaser")
    twelve_week_4_week_chaser_sent_date = AMPDateSentField(label="4 week chaser")
    twelve_week_correspondence_acknowledged_date = AMPDateField(
        label="12 week correspondence acknowledged"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")

    class Meta:
        model = Case
        fields = [
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_4_week_chaser_sent_date",
            "twelve_week_correspondence_acknowledged_date",
            "correspondence_notes",
        ]


class CaseTwelveWeekCorrespondenceDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating twelve week correspondence followup due dates
    """

    twelve_week_1_week_chaser_due_date = AMPDateField(label="1 week followup")
    twelve_week_4_week_chaser_due_date = AMPDateField(label="4 week followup")

    class Meta:
        model = Case
        fields = [
            "twelve_week_1_week_chaser_due_date",
            "twelve_week_4_week_chaser_due_date",
        ]


class CaseArchiveForm(forms.ModelForm):
    """
    Form for archiving a case
    """

    archive_reason = AMPChoiceRadioField(
        label="Reason why?",
        choices=ARCHIVE_DECISION_CHOICES,
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

    no_psb_contact = AMPChoiceRadioField(
        label="Move case onto equality bodies correspondence stage?",
        choices=BOOLEAN_CHOICES,
    )

    class Meta:
        model = Case
        fields = [
            "no_psb_contact",
        ]


class CaseEnforcementBodyCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for recording correspondence with enforcement body
    """

    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to equality body"
    )
    enforcement_body_correspondence_notes = AMPTextField(
        label="Equality body correspondence notes"
    )
    escalation_state = AMPChoiceRadioField(
        label="Equalities body correspondence completed?",
        choices=ESCALATION_STATE_CHOICES,
    )

    class Meta:
        model = Case
        fields = [
            "sent_to_enforcement_body_sent_date",
            "enforcement_body_correspondence_notes",
            "escalation_state",
        ]


class CaseFinalDecisionUpdateForm(forms.ModelForm):
    """
    Form for updating case final decision details
    """

    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    retested_website = AMPDateField(
        label="Retested website?",
        help_text="The retest form can be found in the test results",
    )
    is_disproportionate_claimed = AMPChoiceRadioField(
        label="Disproportionate burden claimed?",
        choices=IS_DISPROPORTIONATE_CLAIMED_CHOICES,
    )
    disproportionate_notes = AMPTextField(label="Disproportionate burden notes")
    accessibility_statement_decison = AMPChoiceRadioField(
        label="Accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes = AMPTextField(label="Accessibility statement notes")
    compliance_decision = AMPChoiceRadioField(
        label="Compliance decision",
        choices=COMPLIANCE_DECISION_CHOICES,
    )
    compliance_decision_notes = AMPTextField(label="Compliance decision notes")
    compliance_email_sent_date = AMPDateField(label="Compliance email sent to PSB?")
    case_completed = AMPChoiceRadioField(
        label="Case completed?",
        choices=CASE_COMPLETED_CHOICES,
    )

    class Meta:
        model = Case
        fields = [
            "psb_progress_notes",
            "retested_website",
            "is_disproportionate_claimed",
            "disproportionate_notes",
            "accessibility_statement_decison",
            "accessibility_statement_notes",
            "compliance_decision",
            "compliance_decision_notes",
            "compliance_email_sent_date",
            "case_completed",
        ]
