"""
Forms - cases
"""
import re
from typing import Any, List, Tuple

import requests

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from ..common.forms import (
    VersionForm,
    AMPChoiceCheckboxWidget,
    AMPModelChoiceField,
    AMPAuditorModelChoiceField,
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
    CASE_COMPLETED_CHOICES,
    PREFERRED_CHOICES,
    BOOLEAN_CHOICES,
    TWELVE_WEEK_RESPONSE_CHOICES,
    ENFORCEMENT_BODY_CHOICES,
    ENFORCEMENT_BODY_PURSUING_CHOICES,
    PSB_LOCATION_CHOICES,
    REPORT_REVIEW_STATUS_CHOICES,
    REPORT_APPROVED_STATUS_CHOICES,
    RECOMMENDATION_CHOICES,
)

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

DEFAULT_SORT: str = "-id"
SORT_CHOICES: List[Tuple[str, str]] = [
    (DEFAULT_SORT, "Newest"),
    ("id", "Oldest"),
    ("organisation_name", "Alphabetic"),
]
IS_COMPLAINT_DEFAULT: str = ""
IS_COMPLAINT_CHOICES: List[Tuple[str, str]] = [
    (IS_COMPLAINT_DEFAULT, "All"),
    ("no", "No complaints"),
    ("yes", "Only complaints"),
]

DATE_TYPE_CHOICES: List[Tuple[str, str]] = [
    ("sent_to_enforcement_body_sent_date", "Date sent to EB"),
]


def get_search_user_choices(user_query: QuerySet[User]) -> List[Tuple[str, str]]:
    """Return a list of user ids and names, with an additional none option, for use in search"""
    user_choices_with_none: List[Tuple[str, str]] = [
        ("", "-----"),
        ("none", "Unassigned"),
    ]
    for user in user_query.order_by("first_name", "last_name"):
        user_choices_with_none.append((user.id, user.get_full_name()))  # type: ignore
    return user_choices_with_none


class CaseSearchForm(AMPDateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    case_search = AMPCharField(
        label="Search", help_text="Matches on URL, organisation, sector or location"
    )
    auditor = AMPChoiceField(label="Auditor")
    reviewer = AMPChoiceField(label="QA Auditor")
    status = AMPChoiceField(label="Status", choices=status_choices)
    date_type = AMPChoiceField(label="Date filter", choices=DATE_TYPE_CHOICES)
    date_start = AMPDateField(label="Date start")
    date_end = AMPDateField(label="Date end")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    is_complaint = AMPChoiceField(
        label="Filter complaints", choices=IS_COMPLAINT_CHOICES
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        auditor_choices: List[Tuple[str, str]] = get_search_user_choices(
            User.objects.filter(groups__name="Historic auditor")
        )
        self.fields["auditor"].choices = auditor_choices  # type: ignore
        self.fields["reviewer"].choices = auditor_choices  # type: ignore


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
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=PSB_LOCATION_CHOICES,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
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
            "psb_location",
            "sector",
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


class CaseDetailUpdateForm(CaseCreateForm, VersionForm):
    """
    Form for updating case details fields
    """

    auditor = AMPAuditorModelChoiceField(
        label="Auditor", help_text="This field affects the case status"
    )
    previous_case_url = AMPURLField(
        label="URL to previous case",
        help_text="If the website has been previously audited, include a link to the case below",
    )
    trello_url = AMPURLField(label="Trello ticket URL")
    notes = AMPTextField(label="Notes")
    case_details_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"  # type: ignore

    def clean_previous_case_url(self):
        """Check url contains case number"""
        previous_case_url = self.cleaned_data.get("previous_case_url")

        # Check if URL was entered
        if not previous_case_url:
            return previous_case_url

        # Check if URL exists
        if requests.head(previous_case_url, timeout=10).status_code >= 400:
            raise ValidationError("Previous case URL does not exist")

        # Extract case id from view case URL
        try:
            case_id: str = re.search(".*/cases/(.+?)/view/?", previous_case_url).group(  # type: ignore
                1
            )
        except AttributeError:
            raise ValidationError(  # pylint: disable=raise-missing-from
                "Previous case URL did not contain case id"
            )

        # Check if Case exists matching id from URL
        if case_id.isdigit() and Case.objects.filter(id=case_id).exists():
            return previous_case_url
        else:
            raise ValidationError("Previous case not found in platform")

    class Meta:
        model = Case
        fields = [
            "version",
            "auditor",
            "home_page_url",
            "organisation_name",
            "enforcement_body",
            "psb_location",
            "sector",
            "is_complaint",
            "previous_case_url",
            "trello_url",
            "notes",
            "case_details_complete_date",
        ]


class CaseTestResultsUpdateForm(VersionForm):
    """
    Form for updating test results
    """

    testing_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "testing_details_complete_date",
        ]


class CaseReportDetailsUpdateForm(VersionForm):
    """
    Form for updating report details
    """

    report_draft_url = AMPURLField(label="Link to report draft")
    report_notes = AMPTextField(label="Report details notes")
    reporting_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_draft_url",
            "report_notes",
            "reporting_details_complete_date",
        ]


class CaseQAProcessUpdateForm(VersionForm):
    """
    Form for updating QA process
    """

    report_review_status = AMPChoiceRadioField(
        label="Report ready to be reviewed?",
        choices=REPORT_REVIEW_STATUS_CHOICES,
        help_text="This field affects the case status",
    )
    reviewer = AMPAuditorModelChoiceField(
        label="QA Auditor",
        help_text="This field affects the case status",
    )
    report_approved_status = AMPChoiceRadioField(
        label="Report approved?",
        choices=REPORT_APPROVED_STATUS_CHOICES,
        help_text="This field affects the case status",
    )
    reviewer_notes = AMPTextField(label="QA notes")
    report_final_odt_url = AMPURLField(label="Link to final ODT report")
    report_final_pdf_url = AMPURLField(label="Link to final PDF report")
    qa_process_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_review_status",
            "reviewer",
            "report_approved_status",
            "reviewer_notes",
            "report_final_odt_url",
            "report_final_pdf_url",
            "qa_process_complete_date",
        ]


class CaseContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    email = AMPCharFieldWide(label="Email")
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=PREFERRED_CHOICES
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = Case
        fields = [
            "name",
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


class CaseContactsUpdateForm(VersionForm):
    """
    Form for updating test results
    """

    contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "contact_details_complete_date",
        ]


class CaseReportCorrespondenceUpdateForm(VersionForm):
    """
    Form for updating report correspondence details
    """

    report_sent_date = AMPDateField(
        label="Report sent on", help_text="This field affects the case status"
    )
    report_followup_week_1_sent_date = AMPDateSentField(label="1-week followup date")
    report_followup_week_4_sent_date = AMPDateSentField(label="4-week followup date")
    report_acknowledged_date = AMPDateField(
        label="Report acknowledged", help_text="This field affects the case status"
    )
    zendesk_url = AMPURLField(label="Zendesk ticket URL")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_sent_date",
            "report_followup_week_1_sent_date",
            "report_followup_week_4_sent_date",
            "report_acknowledged_date",
            "zendesk_url",
            "correspondence_notes",
            "report_correspondence_complete_date",
        ]


class CaseReportFollowupDueDatesUpdateForm(VersionForm):
    """
    Form for updating report followup due dates
    """

    report_followup_week_1_due_date = AMPDateField(label="1-week followup")
    report_followup_week_4_due_date = AMPDateField(label="4-week followup")
    report_followup_week_12_due_date = AMPDateField(label="12-week deadline")

    class Meta:
        model = Case
        fields = [
            "version",
            "report_followup_week_1_due_date",
            "report_followup_week_4_due_date",
            "report_followup_week_12_due_date",
        ]


class CaseNoPSBContactUpdateForm(VersionForm):
    """
    Form for archiving a case
    """

    no_psb_contact = AMPChoiceCheckboxField(
        label="Do you want to mark the PSB as unresponsive to this case?",
        choices=BOOLEAN_CHOICES,
        help_text="This field affects the case status",
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the PSB as unresponsive to this case"}
        ),
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "no_psb_contact",
        ]


class CaseTwelveWeekCorrespondenceUpdateForm(VersionForm):
    """
    Form for updating week twelve correspondence details
    """

    twelve_week_update_requested_date = AMPDateField(
        label="12-week update requested", help_text="This field affects the case status"
    )
    twelve_week_1_week_chaser_sent_date = AMPDateSentField(label="1-week followup")
    twelve_week_correspondence_acknowledged_date = AMPDateField(
        label="12-week update received", help_text="This field affects the case status"
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    twelve_week_response_state = AMPChoiceRadioField(
        label="Mark the case as having no response to 12 week deadline",
        help_text="This field affects the case status",
        choices=TWELVE_WEEK_RESPONSE_CHOICES,
    )
    twelve_week_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "twelve_week_update_requested_date",
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_correspondence_acknowledged_date",
            "twelve_week_correspondence_notes",
            "twelve_week_response_state",
            "twelve_week_correspondence_complete_date",
        ]


class CaseTwelveWeekCorrespondenceDueDatesUpdateForm(VersionForm):
    """
    Form for updating twelve week correspondence followup due dates
    """

    report_followup_week_12_due_date = AMPDateField(label="12-week deadline")
    twelve_week_1_week_chaser_due_date = AMPDateField(label="1-week followup")

    class Meta:
        model = Case
        fields = [
            "version",
            "report_followup_week_12_due_date",
            "twelve_week_1_week_chaser_due_date",
        ]


class CaseTwelveWeekRetestUpdateForm(VersionForm):
    """
    Form for updating twelve week retest
    """

    twelve_week_retest_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "twelve_week_retest_complete_date",
        ]


class CaseReviewChangesUpdateForm(VersionForm):
    """
    Form to record review of changes made by PSB
    """

    retested_website_date = AMPDateField(
        label="Retested website?",
        help_text="There is no test spreadsheet for this case",
    )
    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    is_ready_for_final_decision = AMPChoiceRadioField(
        label="Is this case ready for final decision?",
        help_text="This field affects the case status",
        choices=BOOLEAN_CHOICES,
    )
    review_changes_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "retested_website_date",
            "psb_progress_notes",
            "is_ready_for_final_decision",
            "review_changes_complete_date",
        ]


class CaseCloseUpdateForm(VersionForm):
    """
    Form to record sending the compliance decision
    """

    compliance_email_sent_date = AMPDateField(
        label="Date when compliance decision email sent to public sector body"
    )
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Recommendation for equality body",
        choices=RECOMMENDATION_CHOICES,
    )
    recommendation_notes = AMPTextField(label="Enforcement recommendation notes")
    case_completed = AMPChoiceRadioField(
        label="Case completed",
        choices=CASE_COMPLETED_CHOICES,
        help_text="This field affects the case status",
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "compliance_email_sent_date",
            "recommendation_for_enforcement",
            "recommendation_notes",
            "case_completed",
            "case_close_complete_date",
        ]


class PostCaseUpdateForm(VersionForm):
    """
    Form to record post case notes
    """

    post_case_notes = AMPTextField(label="Summary of events after the case was closed")
    case_updated_date = AMPDateField(label="Case updated")
    post_case_complete_date = AMPDatePageCompleteField()
    psb_appeal_notes = AMPTextField(label="Public sector body statement appeal notes")

    class Meta:
        model = Case
        fields = [
            "version",
            "post_case_notes",
            "case_updated_date",
            "psb_appeal_notes",
            "post_case_complete_date",
        ]


class CaseEnforcementBodyCorrespondenceUpdateForm(VersionForm):
    """
    Form for recording correspondence with enforcement body
    """

    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to equality body",
        help_text="This field affects the case status",
    )
    enforcement_body_pursuing = AMPChoiceRadioField(
        label="Equality body pursuing this case?",
        choices=ENFORCEMENT_BODY_PURSUING_CHOICES,
        help_text="This field affects the case status",
    )
    enforcement_body_correspondence_notes = AMPTextField(
        label="Equality body correspondence notes"
    )
    enforcement_correspondence_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "sent_to_enforcement_body_sent_date",
            "enforcement_body_pursuing",
            "enforcement_body_correspondence_notes",
            "enforcement_correspondence_complete_date",
        ]


class CaseDeactivateForm(VersionForm):
    """
    Form for deactivating a case
    """

    deactivate_notes = AMPTextField(label="Reason why")

    class Meta:
        model = Case
        fields = [
            "version",
            "deactivate_notes",
        ]
