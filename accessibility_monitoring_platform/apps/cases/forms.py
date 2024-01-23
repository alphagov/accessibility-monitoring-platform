"""
Forms - cases
"""
import re
from typing import Any, List, Tuple

import requests
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils.safestring import mark_safe

from ..common.forms import (
    AMPAuditorModelChoiceField,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPDateRangeForm,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from ..common.models import Sector, SubCategory
from .models import Boolean, Case, CaseStatus, Contact, EqualityBodyCorrespondence

ENFORCEMENT_BODY_FILTER_CHOICES = [("", "All")] + Case.EnforcementBody.choices
STATUS_CHOICES: List[Tuple[str, str]] = [("", "All")] + CaseStatus.Status.choices


class Sort(models.TextChoices):
    NEWEST = "", "Newest, Unassigned first"
    OLDEST = "id", "Oldest"
    NAME = "organisation_name", "Alphabetic"


class Complaint(models.TextChoices):
    ALL = "", "All"
    NO = "no", "No complaints"
    YES = "yes", "Only complaints"


class DateType(models.TextChoices):
    START = "audit_case__date_of_test", "Date test started"
    SENT = "sent_to_enforcement_body_sent_date", "Date sent to EB"
    UPDATED = "case_updated_date", "Case updated"


def get_search_user_choices(user_query: QuerySet[User]) -> List[Tuple[str, str]]:
    """Return a list of user ids and names, with an additional none option, for use in search"""
    user_choices_with_none: List[Tuple[str, str]] = [
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

    sort_by = AMPChoiceField(label="Sort by", choices=Sort.choices)
    case_search = AMPCharFieldWide(label="Search")
    auditor = AMPChoiceField(label="Auditor")
    reviewer = AMPChoiceField(label="QA Auditor")
    status = AMPChoiceField(label="Status", choices=STATUS_CHOICES)
    date_type = AMPChoiceField(label="Date filter", choices=DateType.choices)
    date_start = AMPDateField(label="Date start")
    date_end = AMPDateField(label="Date end")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    is_complaint = AMPChoiceField(label="Filter complaints", choices=Complaint.choices)
    enforcement_body = AMPChoiceField(
        label="Enforcement body", choices=ENFORCEMENT_BODY_FILTER_CHOICES
    )
    subcategory = AMPModelChoiceField(
        label="Sub-category", queryset=SubCategory.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        auditor_choices: List[Tuple[str, str]] = get_search_user_choices(
            User.objects.filter(groups__name="Historic auditor")
        )
        self.fields["auditor"].choices = auditor_choices
        self.fields["reviewer"].choices = auditor_choices


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
        choices=Case.EnforcementBody.choices,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=Case.PsbLocation.choices,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    previous_case_url = AMPURLField(
        label="URL to previous case",
        help_text="If the website has been previously audited, include a link to the case below",
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    website_name = AMPCharFieldWide(label="Website name")
    subcategory = AMPModelChoiceField(
        label="Sub-category", queryset=SubCategory.objects.all()
    )

    class Meta:
        model = Case
        fields = [
            "organisation_name",
            "home_page_url",
            "enforcement_body",
            "psb_location",
            "sector",
            "previous_case_url",
            "is_complaint",
            "parental_organisation_name",
            "website_name",
            "subcategory",
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
        self.fields["sector"].empty_label = "Unknown"

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
            "parental_organisation_name",
            "website_name",
            "subcategory",
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
        label="Report ready for QA process?",
        choices=Boolean.choices,
        help_text="This field affects the case status",
    )
    reviewer = AMPAuditorModelChoiceField(
        label="QA Auditor",
        help_text="This field affects the case status",
    )
    report_approved_status = AMPChoiceRadioField(
        label="Report approved?",
        choices=Case.ReportApprovedStatus.choices,
        help_text="This field affects the case status",
    )
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
            "report_final_odt_url",
            "report_final_pdf_url",
            "qa_process_complete_date",
        ]


class CaseCorrespondenceOverviewUpdateForm(VersionForm):
    """
    Form to update Correspondence overview
    """

    zendesk_url = AMPURLField(label="Zendesk ticket URL")
    cores_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "zendesk_url",
            "cores_overview_complete_date",
        ]


class CaseFindContactDetailsUpdateForm(VersionForm):
    """
    Form to update Find contact details
    """

    contact_details_found = AMPChoiceRadioField(
        label="Contact details found?", choices=Case.ContactDetailsFound.choices
    )
    seven_day_no_contact_email_sent_date = AMPDateField(
        label="Seven day 'no contact details' email sent",
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    find_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "contact_details_found",
            "seven_day_no_contact_email_sent_date",
            "correspondence_notes",
            "find_contact_details_complete_date",
        ]


class CaseContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    email = AMPCharFieldWide(label="Email")
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=Contact.Preferred.choices
    )

    class Meta:
        model = Case
        fields = ["name", "job_title", "email", "preferred"]


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

    contact_notes = AMPTextField(label="Contact detail notes")
    contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "contact_notes",
            "contact_details_complete_date",
        ]


class CaseReportSentOnUpdateForm(VersionForm):
    """
    Form to update Report sent on
    """

    report_sent_date = AMPDateField(
        label="Report sent on", help_text="This field affects the case status"
    )
    report_sent_to_email = AMPCharFieldWide(label="Report sent to (email address)")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_sent_on_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_sent_date",
            "report_sent_to_email",
            "correspondence_notes",
            "report_sent_on_complete_date",
        ]


class CaseOneWeekFollowupUpdateForm(VersionForm):
    """
    Form to update One week followup
    """

    report_followup_week_1_sent_date = AMPDateField(
        label="One-week follow-up sent date"
    )
    report_followup_week_1_due_date = AMPDateField(
        label="Initial report follow-up one-week due date"
    )
    one_week_followup_sent_to_email = AMPCharFieldWide(
        label="One week follow-up sent to (email address)"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    one_week_followup_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_followup_week_1_sent_date",
            "report_followup_week_1_due_date",
            "one_week_followup_sent_to_email",
            "correspondence_notes",
            "one_week_followup_complete_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        case: Case = self.instance
        if case and case.report_acknowledged_date:
            self.fields["report_followup_week_1_sent_date"].widget = forms.HiddenInput()
            self.fields["report_followup_week_1_due_date"].widget = forms.HiddenInput()
            self.fields["one_week_followup_sent_to_email"].widget = forms.HiddenInput()


class CaseFourWeekFollowupUpdateForm(VersionForm):
    """
    Form to update Four week followup
    """

    report_followup_week_4_sent_date = AMPDateField(
        label="Four-week follow-up sent date"
    )
    report_followup_week_4_due_date = AMPDateField(
        label="Initial report follow-up four-week due date"
    )
    four_week_followup_sent_to_email = AMPCharFieldWide(
        label="Four week follow-up sent to (email address)"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    four_week_followup_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_followup_week_4_sent_date",
            "report_followup_week_4_due_date",
            "four_week_followup_sent_to_email",
            "correspondence_notes",
            "four_week_followup_complete_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        case: Case = self.instance
        if case and case.report_acknowledged_date:
            self.fields["report_followup_week_4_sent_date"].widget = forms.HiddenInput()
            self.fields["report_followup_week_4_due_date"].widget = forms.HiddenInput()
            self.fields["four_week_followup_sent_to_email"].widget = forms.HiddenInput()


class CaseReportAcknowledgedUpdateForm(VersionForm):
    """
    Form to update Report acknowledged
    """

    report_acknowledged_date = AMPDateField(
        label="Report acknowledged date", help_text="This field affects the case status"
    )
    report_acknowledged_by_email = AMPCharFieldWide(
        label="Report acknowledged by (email address)"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "report_acknowledged_date",
            "report_acknowledged_by_email",
            "correspondence_notes",
            "report_acknowledged_complete_date",
        ]


class CaseTwelveWeekUpdateRequestedUpdateForm(VersionForm):
    """
    Form to update 12-week update requested
    """

    twelve_week_update_requested_date = AMPDateField(
        label="12-week update requested date",
        help_text="This field affects the case status",
    )
    report_followup_week_12_due_date = AMPDateField(label="12-week deadline")
    twelve_week_update_request_sent_to_email = AMPCharFieldWide(
        label="12-week request sent to (email address)"
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    twelve_week_update_requested_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "twelve_week_update_requested_date",
            "report_followup_week_12_due_date",
            "twelve_week_update_request_sent_to_email",
            "twelve_week_correspondence_notes",
            "twelve_week_update_requested_complete_date",
        ]


class CaseOneWeekFollowupFinalUpdateForm(VersionForm):
    """
    Form to update One week followup for final update
    """

    twelve_week_1_week_chaser_sent_date = AMPDateField(
        label="One week follow-up for final update sent date"
    )
    twelve_week_1_week_chaser_due_date = AMPDateField(
        label="Final update one-week follow-up due date"
    )
    twelve_week_1_week_chaser_sent_to_email = AMPCharFieldWide(
        label="One week follow-up for final update sent to (email address)"
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    one_week_followup_final_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "twelve_week_1_week_chaser_sent_date",
            "twelve_week_1_week_chaser_due_date",
            "twelve_week_1_week_chaser_sent_to_email",
            "twelve_week_correspondence_notes",
            "one_week_followup_final_complete_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        case: Case = self.instance
        if case and case.twelve_week_correspondence_acknowledged_date:
            self.fields[
                "twelve_week_1_week_chaser_sent_date"
            ].widget = forms.HiddenInput()
            self.fields[
                "twelve_week_1_week_chaser_due_date"
            ].widget = forms.HiddenInput()
            self.fields[
                "twelve_week_1_week_chaser_sent_to_email"
            ].widget = forms.HiddenInput()


class CaseTwelveWeekUpdateAcknowledgedUpdateForm(VersionForm):
    """
    Form to update 12-week update request acknowledged
    """

    twelve_week_correspondence_acknowledged_date = AMPDateField(
        label="12-week update received", help_text="This field affects the case status"
    )
    twelve_week_correspondence_acknowledged_by_email = AMPCharFieldWide(
        label="12-week update request acknowledged by (email address)"
    )
    organisation_response = AMPChoiceRadioField(
        label="If the organisation did not respond to the 12 week update request, select ‘Organisation did not respond to 12-week update’",
        help_text="This field affects the case status",
        choices=Case.OrganisationResponse.choices,
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    twelve_week_update_request_ack_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "twelve_week_correspondence_acknowledged_date",
            "twelve_week_correspondence_acknowledged_by_email",
            "organisation_response",
            "twelve_week_correspondence_notes",
            "twelve_week_update_request_ack_complete_date",
        ]


class CaseNoPSBContactUpdateForm(VersionForm):
    """
    Form for archiving a case
    """

    no_psb_contact = AMPChoiceCheckboxField(
        label="Do you want to mark the PSB as unresponsive to this case?",
        choices=Boolean.choices,
        help_text="This field affects the case status",
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the PSB as unresponsive to this case"}
        ),
    )
    no_psb_contact_notes = AMPTextField(
        label="Public sector body is unresponsive notes"
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "no_psb_contact",
            "no_psb_contact_notes",
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

    retested_website_date = AMPDateField(label="Retested website?")
    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body"
    )
    is_ready_for_final_decision = AMPChoiceRadioField(
        label="Is this case ready for final decision?",
        help_text="This field affects the case status",
        choices=Boolean.choices,
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
    compliance_decision_sent_to_email = AMPCharFieldWide(
        label="Compliance decision sent to (email address)"
    )
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Recommendation for equality body",
        choices=Case.RecommendationForEnforcement.choices,
    )
    recommendation_notes = AMPTextField(
        label="Enforcement recommendation notes including exemptions",
        help_text=mark_safe(
            '<span id="amp-copy-text-control" class="amp-control" tabindex="0">Fill text field</span>'
            " with notes from Summary of progress made from public sector body"
        ),
    )
    case_completed = AMPChoiceRadioField(
        label="Case completed",
        choices=Case.CaseCompleted.choices,
        help_text="This field affects the case status",
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields = [
            "version",
            "compliance_email_sent_date",
            "compliance_decision_sent_to_email",
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


class CaseStatementEnforcementUpdateForm(VersionForm):
    """
    Form to update statement enforcement
    """

    post_case_notes = AMPTextField(label="Summary of events after the case was closed")
    psb_appeal_notes = AMPTextField(label="Public sector body appeal notes")

    class Meta:
        model = Case
        fields = [
            "version",
            "post_case_notes",
            "psb_appeal_notes",
        ]


class CaseEqualityBodyMetadataUpdateForm(VersionForm):
    """
    Form to update equality body metadata
    """

    sent_to_enforcement_body_sent_date = AMPDateField(
        label="Date sent to equality body",
    )
    equality_body_case_start_date = AMPDateField(
        label="Date equality body started case",
    )
    enforcement_body_case_owner = AMPCharFieldWide(
        label="Equality body case owner (first name only)",
    )
    enforcement_body_closed_case = AMPChoiceRadioField(
        label="Equality body has officially closed the case?",
        choices=Case.EnforcementBodyClosedCase.choices,
    )
    enforcement_body_finished_date = AMPDateField(
        label="Date equality body completed the case",
    )
    is_feedback_requested = AMPChoiceCheckboxField(
        label="Feedback survey sent?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Feedback survey sent to this organisation?"}
        ),
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "sent_to_enforcement_body_sent_date",
            "equality_body_case_start_date",
            "enforcement_body_case_owner",
            "enforcement_body_closed_case",
            "enforcement_body_finished_date",
            "is_feedback_requested",
        ]


class ListCaseEqualityBodyCorrespondenceUpdateForm(VersionForm):
    """
    Form for list equality body correspondence page
    """

    class Meta:
        model = Case
        fields = [
            "version",
        ]


class EqualityBodyCorrespondenceCreateForm(forms.ModelForm):
    """
    Form for creating an EqualityBodyCorrespondence
    """

    type = AMPChoiceRadioField(
        label="Type",
        choices=EqualityBodyCorrespondence.Type.choices,
        initial=EqualityBodyCorrespondence.Type.QUESTION,
    )
    message = AMPTextField(label="Message/content")
    notes = AMPTextField(label="Notes")
    zendesk_url = AMPURLField(label="Link to Zendesk ticket")

    class Meta:
        model = EqualityBodyCorrespondence
        fields = [
            "type",
            "message",
            "notes",
            "zendesk_url",
        ]
