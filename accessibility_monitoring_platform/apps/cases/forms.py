"""
Forms - cases
"""
from typing import Any

from django import forms
from django.contrib.auth.models import User

from ..common.forms import (
    AMPBooleanCheckboxWidget,
    AMPChoiceCheckboxWidget,
    AMPDateCheckboxWidget,
    AMPModelChoiceField,
    AMPUserModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPDateField,
    AMPDateSentField,
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
    ARCHIVE_DECISION_CHOICES,
    CASE_COMPLETED_CHOICES,
    ESCALATION_STATE_CHOICES,
    PREFERRED_CHOICES,
    IS_WEBSITE_COMPLIANT_CHOICES,
    BOOLEAN_CHOICES,
    IS_DISPROPORTIONATE_CLAIMED_CHOICES,
    ENFORCEMENT_BODY_CHOICES,
    REPORT_REVIEW_STATUS_CHOICES,
    REPORT_APPROVED_STATUS_CHOICES,
)

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
    search = AMPCharField(
        label="Search", help_text="Searches in URLs and organisation names"
    )
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
    )
    home_page_url = AMPURLField(
        label="Full URL",
        required=True,
    )
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


class CaseDetailUpdateForm(CaseCreateForm):
    """
    Form for updating case details fields
    """

    auditor = AMPUserModelChoiceField(label="Auditor")
    service_name = AMPCharFieldWide(label="Website, app or service name")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    zendesk_url = AMPURLField(label="Zendesk ticket URL")
    trello_url = AMPURLField(label="Trello ticket URL")
    notes = AMPTextField(label="Notes")
    is_case_details_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Case details completed?"},
        ),
        required=False,
    )

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
            "sector",
            "is_complaint",
            "zendesk_url",
            "trello_url",
            "notes",
            "is_case_details_complete",
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

    is_contact_details_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Contact details completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "is_contact_details_complete",
        ]


class CaseTestResultsUpdateForm(forms.ModelForm):
    """
    Form for updating test results
    """

    test_results_url = AMPURLField(label="Link to test results")
    test_status = AMPChoiceRadioField(
        label="Test status",
        choices=TEST_STATUS_CHOICES,
    )
    accessibility_statement_decison = AMPChoiceRadioField(
        label="Is the accessibility statement compliant?",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes = AMPTextField(label="Accessibility statement notes")
    is_website_compliant = AMPChoiceRadioField(
        label="Is the website compliant?", choices=IS_WEBSITE_COMPLIANT_CHOICES
    )
    compliance_decision_notes = AMPTextField(label="Compliance notes")
    is_testing_details_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Testing details completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "test_results_url",
            "test_status",
            "accessibility_statement_decison",
            "accessibility_statement_notes",
            "is_website_compliant",
            "compliance_decision_notes",
            "is_testing_details_complete",
        ]


class CaseReportDetailsUpdateForm(forms.ModelForm):
    """
    Form for updating report details
    """

    report_draft_url = AMPURLField(label="Link to report draft")
    report_review_status = AMPChoiceRadioField(
        label="Report ready to be reviewed?", choices=REPORT_REVIEW_STATUS_CHOICES
    )
    reviewer = AMPUserModelChoiceField(label="QA Auditor")
    report_approved_status = AMPChoiceRadioField(
        label="Report approved?", choices=REPORT_APPROVED_STATUS_CHOICES
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_pdf_url = AMPURLField(label="Link to final PDF report")
    report_final_odt_url = AMPURLField(label="Link to final ODT report")
    is_reporting_details_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Reporting details completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "report_draft_url",
            "report_review_status",
            "reviewer",
            "report_approved_status",
            "reviewer_notes",
            "report_final_pdf_url",
            "report_final_odt_url",
            "is_reporting_details_complete",
        ]


class CaseReportCorrespondenceUpdateForm(forms.ModelForm):
    """
    Form for updating report correspondence details
    """

    report_sent_date = AMPDateField(label="Report sent on")
    report_followup_week_1_sent_date = AMPDateSentField(label="1 week followup date")
    report_followup_week_4_sent_date = AMPDateSentField(label="4 week followup date")
    report_followup_week_12_due_date = AMPDateSentField(
        label="12 week update", widget=AMPDateCheckboxWidget(attrs={"removed": "true"})
    )
    report_acknowledged_date = AMPDateField(label="Report acknowledged")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    is_report_correspondence_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Report correspondence completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "report_sent_date",
            "report_followup_week_1_sent_date",
            "report_followup_week_4_sent_date",
            "report_followup_week_12_due_date",
            "report_acknowledged_date",
            "correspondence_notes",
            "is_report_correspondence_complete",
        ]


class CaseReportFollowupDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating report followup due dates
    """

    report_followup_week_1_due_date = AMPDateField(label="1 week followup")
    report_followup_week_4_due_date = AMPDateField(label="4 week followup")
    report_followup_week_12_due_date = AMPDateField(label="12 week update")

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

    report_followup_week_12_due_date = AMPDateSentField(
        label="12 week update", widget=AMPDateCheckboxWidget(attrs={"removed": "true"})
    )
    twelve_week_update_requested_date = AMPDateField(label="12 week update requested")
    twelve_week_1_week_chaser_sent_date = AMPDateSentField(label="1 week chaser")
    twelve_week_4_week_chaser_sent_date = AMPDateSentField(label="4 week chaser")
    twelve_week_correspondence_acknowledged_date = AMPDateField(
        label="12 week update request acknowledged"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    twelve_week_response_state = AMPChoiceCheckboxField(
        label="Mark the case as having no response to 12 week update",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "No response?"}),
    )
    is_12_week_correspondence_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "12 week correspondence completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "report_followup_week_12_due_date",
            "twelve_week_update_requested_date",
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_4_week_chaser_sent_date",
            "twelve_week_correspondence_acknowledged_date",
            "correspondence_notes",
            "twelve_week_response_state",
            "is_12_week_correspondence_complete",
        ]


class CaseTwelveWeekCorrespondenceDueDatesUpdateForm(forms.ModelForm):
    """
    Form for updating twelve week correspondence followup due dates
    """

    report_followup_week_12_due_date = AMPDateField(label="12 week update")
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
    retested_website = AMPDateField(
        label="Retested website?",
        help_text="There is no test spreadsheet for this case",
    )
    is_disproportionate_claimed = AMPChoiceRadioField(
        label="Disproportionate burden claimed?",
        choices=IS_DISPROPORTIONATE_CLAIMED_CHOICES,
    )
    disproportionate_notes = AMPTextField(label="Disproportionate burden notes")
    accessibility_statement_decison_final = AMPChoiceRadioField(
        label="Final accessibility statement decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes_final = AMPTextField(
        label="Final accessibility statement notes"
    )
    is_website_compliant_final = AMPChoiceRadioField(
        label="Final compliance decision",
        choices=IS_WEBSITE_COMPLIANT_CHOICES,
    )
    compliance_decision_notes_final = AMPTextField(
        label="FInal compliance decision notes"
    )
    compliance_email_sent_date = AMPDateField(
        label="Compliance email sent to public sector body?"
    )
    case_completed = AMPChoiceRadioField(
        label="Case completed?",
        choices=CASE_COMPLETED_CHOICES,
    )
    is_final_decision_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Final decision completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "psb_progress_notes",
            "retested_website",
            "is_disproportionate_claimed",
            "disproportionate_notes",
            "accessibility_statement_decison_final",
            "accessibility_statement_notes_final",
            "is_website_compliant_final",
            "compliance_decision_notes_final",
            "compliance_email_sent_date",
            "case_completed",
            "is_final_decision_complete",
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
    )
    is_enforcement_correspondence_complete = forms.BooleanField(
        label="Mark this page as completed",
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Equality body correspondence completed?"},
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "psb_appeal_notes",
            "sent_to_enforcement_body_sent_date",
            "enforcement_body_correspondence_notes",
            "escalation_state",
            "is_enforcement_correspondence_complete",
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
