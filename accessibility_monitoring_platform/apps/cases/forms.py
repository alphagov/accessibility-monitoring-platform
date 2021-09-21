"""
Forms - cases
"""
from typing import Any, List, Tuple

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from ..common.forms import (
    AMPChoiceCheckboxWidget,
    AMPModelChoiceField,
    AMPAuditorModelChoiceField,
    AMPQAAuditorModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPDateField,
    AMPDateSentField,
    AMPDatePageCompleteField,
    AMPDateRangeForm,
    AMPURLField,
)
from ..common.models import Sector
from .models import (
    Case,
    Contact,
    STATUS_CHOICES,
    TEST_STATUS_CHOICES,
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    DELETE_DECISION_CHOICES,
    CASE_COMPLETED_CHOICES,
    ESCALATION_STATE_CHOICES,
    PREFERRED_CHOICES,
    IS_WEBSITE_COMPLIANT_CHOICES,
    BOOLEAN_CHOICES,
    IS_DISPROPORTIONATE_CLAIMED_CHOICES,
    ENFORCEMENT_BODY_CHOICES,
    PSB_LOCATION_CHOICES,
    REPORT_REVIEW_STATUS_CHOICES,
    REPORT_READY_TO_REVIEW,
    REPORT_APPROVED_STATUS_CHOICES,
    RECOMMENDATION_CHOICES,
)

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

DEFAULT_SORT: str = "-id"
SORT_CHOICES = [
    (DEFAULT_SORT, "Newest"),
    ("id", "Oldest"),
]


def get_search_user_choices(user_query: QuerySet[User]) -> List[Tuple[int, str]]:
    """Return a list of user ids and names, with an additional none option, for use in search"""
    user_choices_with_none: List[Tuple[int, str]] = [
        ("", "-----"),
        ("none", "Unassigned"),
    ]
    for user in user_query.order_by("first_name", "last_name"):
        user_choices_with_none.append((user.id, user.get_full_name()))
    return user_choices_with_none


class CaseSearchForm(AMPDateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    search = AMPCharField(
        label="Search", help_text="Matches on URL, organisation, sector or location"
    )
    auditor = AMPChoiceField(label="Auditor")
    reviewer = AMPChoiceField(label="QA Auditor")
    status = AMPChoiceField(label="Status", choices=status_choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["auditor"].choices = get_search_user_choices(
            User.objects.filter(groups__name="Auditor")
        )
        self.fields["reviewer"].choices = get_search_user_choices(
            User.objects.filter(groups__name="QA auditor")
        )


class CaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name",
    )
    home_page_url = AMPURLField(label="Full URL")
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=ENFORCEMENT_BODY_CHOICES,
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )

    class Meta:
        model = Case
        fields = [
            "organisation_name",
            "home_page_url",
            "enforcement_body",
            "is_complaint",
        ]

    def clean_home_page_url(self):
        home_page_url = self.cleaned_data.get("home_page_url")
        if not home_page_url:
            raise ValidationError("Full URL is required")
        return home_page_url

    def clean_enforcement_body(self):
        enforcement_body = self.cleaned_data.get("enforcement_body")
        if not enforcement_body:
            raise ValidationError("Choose which equalities body will check the case")
        return enforcement_body


class CaseDetailUpdateForm(CaseCreateForm):
    """
    Form for updating case details fields
    """

    auditor = AMPAuditorModelChoiceField(
        label="Auditor", help_text="This field effects the case status"
    )
    service_name = AMPCharFieldWide(label="Website, app or service name")
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=PSB_LOCATION_CHOICES,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    trello_url = AMPURLField(label="Trello ticket URL")
    notes = AMPTextField(label="Notes")
    case_details_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"

    class Meta:
        model = Case
        fields = [
            "auditor",
            "home_page_url",
            "organisation_name",
            "service_name",
            "enforcement_body",
            "psb_location",
            "sector",
            "is_complaint",
            "trello_url",
            "notes",
            "case_details_complete_date",
        ]


class CaseTestResultsUpdateForm(forms.ModelForm):
    """
    Form for updating test results
    """

    test_results_url = AMPURLField(label="Link to test results")
    test_status = AMPChoiceRadioField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
        help_text="This field effects the case status",
    )
    accessibility_statement_state = AMPChoiceRadioField(
        label="Initial accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes = AMPTextField(label="Accessibility statement notes")
    is_website_compliant = AMPChoiceRadioField(
        label="Initial compliance decision", choices=IS_WEBSITE_COMPLIANT_CHOICES
    )
    compliance_decision_notes = AMPTextField(label="Compliance notes")
    testing_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "test_results_url",
            "test_status",
            "accessibility_statement_state",
            "accessibility_statement_notes",
            "is_website_compliant",
            "compliance_decision_notes",
            "testing_details_complete_date",
        ]


class CaseReportDetailsUpdateForm(forms.ModelForm):
    """
    Form for updating report details
    """

    report_draft_url = AMPURLField(label="Link to report draft")
    report_review_status = AMPChoiceRadioField(
        label="Report ready to be reviewed?",
        choices=REPORT_REVIEW_STATUS_CHOICES,
        help_text="This field effects the case status",
    )
    reviewer = AMPQAAuditorModelChoiceField(label="QA Auditor")
    report_approved_status = AMPChoiceRadioField(
        label="Report approved?", choices=REPORT_APPROVED_STATUS_CHOICES
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_odt_url = AMPURLField(label="Link to final ODT report")
    report_final_pdf_url = AMPURLField(label="Link to final PDF report")
    reporting_details_complete_date = AMPDatePageCompleteField()

    def clean(self):
        cleaned_data = super().clean()
        report_draft_url = cleaned_data.get("report_draft_url")
        report_review_status = cleaned_data.get("report_review_status")
        if report_review_status == REPORT_READY_TO_REVIEW and not report_draft_url:
            self.add_error(
                "report_draft_url",
                "Add link to report draft, if report is ready to be reviewed",
            )
            self.add_error(
                "report_review_status",
                "Report cannot be ready to be reviewed without a link to report draft",
            )
        return cleaned_data

    class Meta:
        model = Case
        fields = [
            "report_draft_url",
            "report_review_status",
            "reviewer",
            "report_approved_status",
            "reviewer_notes",
            "report_final_odt_url",
            "report_final_pdf_url",
            "reporting_details_complete_date",
        ]


class CaseContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    first_name = AMPCharFieldWide(label="First name")
    last_name = AMPCharFieldWide(label="Last name")
    job_title = AMPCharFieldWide(label="Job title")
    email = AMPCharFieldWide(label="Email")
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
            "email",
            "preferred",
            "notes",
        ]


CaseContactFormset: Any = forms.modelformset_factory(
    Contact, CaseContactUpdateForm, extra=0
)
CaseContactFormsetOneExtra: Any = forms.modelformset_factory(
    Contact, CaseContactUpdateForm, extra=1
)


class CaseContactsUpdateForm(forms.ModelForm):
    """
    Form for updating test results
    """

    contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "contact_details_complete_date",
        ]


class CaseReportCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for updating report correspondence details
    """

    report_sent_date = AMPDateField(
        label="Report sent on", help_text="This field effects the case status"
    )
    report_followup_week_1_sent_date = AMPDateSentField(label="1 week followup date")
    report_followup_week_4_sent_date = AMPDateSentField(label="4 week followup date")
    report_acknowledged_date = AMPDateField(
        label="Report acknowledged", help_text="This field effects the case status"
    )
    zendesk_url = AMPURLField(label="Zendesk ticket URL")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "report_sent_date",
            "report_followup_week_1_sent_date",
            "report_followup_week_4_sent_date",
            "report_acknowledged_date",
            "zendesk_url",
            "correspondence_notes",
            "report_correspondence_complete_date",
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


class CaseNoPSBContactUpdateForm(forms.ModelForm):
    """
    Form for archiving a case
    """

    no_psb_contact = AMPChoiceCheckboxField(
        label="Do you want to move this case to the equality bodies correspondence stage?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Move this case onto equality bodies correspondence stage?"}
        ),
    )

    class Meta:
        model = Case
        fields = [
            "no_psb_contact",
        ]


class CaseTwelveWeekCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for updating week twelve correspondence details
    """

    twelve_week_update_requested_date = AMPDateField(
        label="12 week update requested", help_text="This field effects the case status"
    )
    twelve_week_1_week_chaser_sent_date = AMPDateSentField(label="1 week followup")
    twelve_week_4_week_chaser_sent_date = AMPDateSentField(label="4 week followup")
    twelve_week_correspondence_acknowledged_date = AMPDateField(
        label="12 week update received", help_text="This field effects the case status"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    twelve_week_response_state = AMPChoiceCheckboxField(
        label="Mark the case as having no response to 12 week deadline",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "No response?"}),
    )
    twelve_week_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "twelve_week_update_requested_date",
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_4_week_chaser_sent_date",
            "twelve_week_correspondence_acknowledged_date",
            "correspondence_notes",
            "twelve_week_response_state",
            "twelve_week_correspondence_complete_date",
        ]


class CaseTwelveWeekCorrespondenceDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating twelve week correspondence followup due dates
    """

    report_followup_week_12_due_date = AMPDateField(label="12 week deadline")
    twelve_week_1_week_chaser_due_date = AMPDateField(label="1 week followup")
    twelve_week_4_week_chaser_due_date = AMPDateField(label="4 week followup")

    class Meta:
        model = Case
        fields = [
            "report_followup_week_12_due_date",
            "twelve_week_1_week_chaser_due_date",
            "twelve_week_4_week_chaser_due_date",
        ]


class CaseFinalDecisionUpdateForm(forms.ModelForm):
    """
    Form for updating case final decision details
    """

    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    retested_website_date = AMPDateField(
        label="Retested website?",
        help_text="There is no test spreadsheet for this case",
    )
    is_disproportionate_claimed = AMPChoiceRadioField(
        label="Disproportionate burden claimed?",
        choices=IS_DISPROPORTIONATE_CLAIMED_CHOICES,
    )
    disproportionate_notes = AMPTextField(label="Disproportionate burden notes")
    accessibility_statement_state_final = AMPChoiceRadioField(
        label="Final accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_screenshot_url = AMPURLField(
        label="Link to accessibility statement screenshot"
    )
    accessibility_statement_notes_final = AMPTextField(
        label="Final accessibility statement notes",
    )
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Enforcement recommendation",
        choices=RECOMMENDATION_CHOICES,
    )
    recommendation_notes = AMPTextField(label="Enforcement recommendation notes")
    compliance_email_sent_date = AMPDateField(
        label="Compliance email sent to public sector body?"
    )
    case_completed = AMPChoiceRadioField(
        label="Case completed and needs to be sent to EHRC or ECNI?",
        choices=CASE_COMPLETED_CHOICES,
        help_text="This field effects the case status",
    )
    final_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "psb_progress_notes",
            "retested_website_date",
            "is_disproportionate_claimed",
            "disproportionate_notes",
            "accessibility_statement_state_final",
            "accessibility_statement_screenshot_url",
            "accessibility_statement_notes_final",
            "recommendation_for_enforcement",
            "recommendation_notes",
            "compliance_email_sent_date",
            "case_completed",
            "final_decision_complete_date",
        ]


class CaseEnforcementBodyCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for recording correspondence with enforcement body
    """

    psb_appeal_notes = AMPTextField(label="Public sector body appeal notes")
    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to equality body"
    )
    enforcement_body_correspondence_notes = AMPTextField(
        label="Equality body correspondence notes"
    )
    escalation_state = AMPChoiceRadioField(
        label="Equalities body correspondence completed?",
        choices=ESCALATION_STATE_CHOICES,
        help_text="This field effects the case status",
    )
    enforcement_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "psb_appeal_notes",
            "sent_to_enforcement_body_sent_date",
            "enforcement_body_correspondence_notes",
            "escalation_state",
            "enforcement_correspondence_complete_date",
        ]


class CaseDeleteForm(forms.ModelForm):
    """
    Form for archiving a case
    """

    delete_reason = AMPChoiceRadioField(
        label="Reason why?",
        choices=DELETE_DECISION_CHOICES,
    )
    delete_notes = AMPTextField(label="More information?")

    class Meta:
        model = Case
        fields = [
            "delete_reason",
            "delete_notes",
        ]
