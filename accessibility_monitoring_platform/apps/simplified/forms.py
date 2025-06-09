"""
Forms - cases
"""

import re

import requests
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.safestring import mark_safe

from ..common.forms import (
    AMPAuditorModelChoiceField,
    AMPBooleanCheckboxWidget,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceRadioField,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from ..common.models import Sector, SubCategory
from ..exports.csv_export_utils import (
    EqualityBodyCSVColumn,
    populate_equality_body_columns,
)
from .models import (
    Boolean,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    ZendeskTicket,
)

ENFORCEMENT_BODY_FILTER_CHOICES = [("", "All")] + SimplifiedCase.EnforcementBody.choices
STATUS_CHOICES: list[tuple[str, str]] = [("", "All")] + CaseStatus.Status.choices
RECOMMENDATION_CHOICES: list[tuple[str, str]] = [
    ("", "All")
] + SimplifiedCase.RecommendationForEnforcement.choices


class DateType(models.TextChoices):
    START = "audit_basecase__date_of_test", "Date test started"
    SENT = "sent_to_enforcement_body_sent_date", "Date sent to EB"
    UPDATED = "case_updated_date", "Case updated"


class CaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name (included in equality body export)",
    )
    home_page_url = AMPURLField(label="Full URL (included in equality body export)")
    parental_organisation_name = AMPCharFieldWide(
        label="Parent organisation name (included in equality body export)"
    )
    website_name = AMPCharFieldWide(
        label="Website name (included in equality body export)"
    )
    subcategory = AMPModelChoiceField(
        label="Sub-category (included in equality body export)",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case? (included in equality body export)",
        choices=SimplifiedCase.EnforcementBody.choices,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=SimplifiedCase.PsbLocation.choices,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint? (included in equality body export)",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )
    previous_case_url = AMPURLField(
        label="URL to previous case (included in equality body export)",
        help_text="If the website has been previously audited, include a link to the case below",
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = SimplifiedCase
        fields = [
            "organisation_name",
            "home_page_url",
            "parental_organisation_name",
            "website_name",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "sector",
            "is_complaint",
            "previous_case_url",
            "notes",
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


class CaseMetadataUpdateForm(CaseCreateForm, VersionForm):
    """
    Form for updating case metadata fields
    """

    auditor = AMPAuditorModelChoiceField(
        label="Auditor", help_text="This field affects the case status"
    )
    previous_case_url = AMPURLField(
        label="URL to previous case",
        help_text="If the website has been previously audited, include a link to the case below",
    )
    trello_url = AMPURLField(label="Trello ticket URL")
    is_feedback_requested = AMPChoiceCheckboxField(
        label="Feedback survey sent?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Feedback survey sent to this organisation?"}
        ),
    )
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
        if case_id.isdigit() and SimplifiedCase.objects.filter(id=case_id).exists():
            return previous_case_url
        else:
            raise ValidationError("Previous case not found in platform")

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "auditor",
            "organisation_name",
            "home_page_url",
            "parental_organisation_name",
            "website_name",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "sector",
            "is_complaint",
            "previous_case_url",
            "notes",
            "trello_url",
            "is_feedback_requested",
            "case_details_complete_date",
        ]


class CaseTestResultsUpdateForm(VersionForm):
    """
    Form for updating test results
    """

    testing_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
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
        model = SimplifiedCase
        fields = [
            "version",
            "report_draft_url",
            "report_notes",
            "reporting_details_complete_date",
        ]


class CaseReportReadyForQAUpdateForm(VersionForm):
    """
    Form for updating report details
    """

    report_review_status = AMPChoiceRadioField(
        label="Report ready for QA process?",
        choices=Boolean.choices,
        help_text="This field affects the case status",
    )
    reporting_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "report_review_status",
            "reporting_details_complete_date",
        ]


class CaseQAAuditorUpdateForm(VersionForm):
    """
    Form for updating QA auditor
    """

    reviewer = AMPAuditorModelChoiceField(
        label="QA Auditor",
        help_text="This field affects the case status",
    )
    qa_auditor_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "reviewer",
            "qa_auditor_complete_date",
        ]


class CaseQACommentsUpdateForm(VersionForm):
    """
    Form for updating QA comments page
    """

    body: AMPTextField = AMPTextField(
        label="Add comment",
        widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "12"}),
    )

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "body",
        ]


class CaseQAApprovalUpdateForm(VersionForm):
    """
    Form for updating QA auditor and report approval
    """

    report_approved_status = AMPChoiceRadioField(
        label="Report approved?",
        choices=SimplifiedCase.ReportApprovedStatus.choices,
        help_text="This field affects the case status",
    )
    qa_approval_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "report_approved_status",
            "qa_approval_complete_date",
        ]


class CasePublishReportUpdateForm(VersionForm):
    """
    Form for publishing reporti after QA approval
    """

    publish_report_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "publish_report_complete_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        case: SimplifiedCase = self.instance
        if case:
            if (
                not case.published_report_url
                or not case.report
                or case.report_review_status != Boolean.YES
                or case.report_approved_status
                != SimplifiedCase.ReportApprovedStatus.APPROVED
            ):
                self.fields["publish_report_complete_date"].widget = forms.HiddenInput()


class ManageContactDetailsUpdateForm(VersionForm):
    """
    Form for updating test results
    """

    contact_notes = AMPTextField(label="Contact detail notes")
    manage_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "contact_notes",
            "manage_contact_details_complete_date",
        ]


class ContactCreateForm(forms.ModelForm):
    """
    Form for creating a contact
    """

    name = AMPCharFieldWide(label="Name (included in equality body export)")
    job_title = AMPCharFieldWide(label="Job title (included in equality body export)")
    email = AMPCharFieldWide(label="Email (included in equality body export)")
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=Contact.Preferred.choices
    )

    class Meta:
        model = Contact
        fields = ["name", "job_title", "email", "preferred"]


class ContactUpdateForm(VersionForm):
    """
    Form for updating a contact
    """

    name = AMPCharFieldWide(label="Name (included in equality body export)")
    job_title = AMPCharFieldWide(label="Job title (included in equality body export)")
    email = AMPCharFieldWide(label="Email (included in equality body export)")
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=Contact.Preferred.choices
    )

    class Meta:
        model = Contact
        fields = ["version", "name", "job_title", "email", "preferred"]


class CaseRequestContactDetailsUpdateForm(VersionForm):
    """
    Form to update Find contact details
    """

    seven_day_no_contact_email_sent_date = AMPDateField(
        label="No contact details request sent",
    )
    seven_day_no_contact_request_sent_to = AMPCharFieldWide(
        label="Initial request sent to"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    request_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "seven_day_no_contact_email_sent_date",
            "seven_day_no_contact_request_sent_to",
            "correspondence_notes",
            "request_contact_details_complete_date",
        ]


class CaseOneWeekContactDetailsUpdateForm(VersionForm):
    """
    Form to update One week contact details
    """

    no_contact_one_week_chaser_sent_date = AMPDateField(
        label="No contact details 1-week chaser sent date",
    )
    no_contact_one_week_chaser_due_date = AMPDateField(
        label="No contact details 1-week chaser due date"
    )
    no_contact_one_week_chaser_sent_to = AMPCharFieldWide(label="1-week chaser sent to")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    one_week_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "no_contact_one_week_chaser_sent_date",
            "no_contact_one_week_chaser_due_date",
            "no_contact_one_week_chaser_sent_to",
            "correspondence_notes",
            "one_week_contact_details_complete_date",
        ]


class CaseFourWeekContactDetailsUpdateForm(VersionForm):
    """
    Form to update Four week contact details
    """

    no_contact_four_week_chaser_sent_date = AMPDateField(
        label="No contact details 4-week chaser sent date",
    )
    no_contact_four_week_chaser_due_date = AMPDateField(
        label="No contact details 4-week chaser due date"
    )
    no_contact_four_week_chaser_sent_to = AMPCharFieldWide(
        label="4-week chaser sent to"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    four_week_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "no_contact_four_week_chaser_sent_date",
            "no_contact_four_week_chaser_due_date",
            "no_contact_four_week_chaser_sent_to",
            "correspondence_notes",
            "four_week_contact_details_complete_date",
        ]


class CaseReportSentOnUpdateForm(VersionForm):
    """
    Form to update Report sent on
    """

    report_sent_date = AMPDateField(
        label="Report sent on (included in equality body export)",
        help_text="This field affects the case status",
    )
    report_sent_to_email = AMPCharFieldWide(label="Report sent to (email address)")
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_sent_on_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "report_sent_date",
            "report_sent_to_email",
            "correspondence_notes",
            "report_sent_on_complete_date",
        ]


class CaseReportOneWeekFollowupUpdateForm(VersionForm):
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
        model = SimplifiedCase
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
        simplified_case: SimplifiedCase = self.instance
        if simplified_case and simplified_case.report_acknowledged_date:
            self.fields["report_followup_week_1_sent_date"].widget = forms.HiddenInput()
            self.fields["report_followup_week_1_due_date"].widget = forms.HiddenInput()
            self.fields["one_week_followup_sent_to_email"].widget = forms.HiddenInput()


class CaseReportFourWeekFollowupUpdateForm(VersionForm):
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
        model = SimplifiedCase
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
        simplified_case: SimplifiedCase = self.instance
        if simplified_case and simplified_case.report_acknowledged_date:
            self.fields["report_followup_week_4_sent_date"].widget = forms.HiddenInput()
            self.fields["report_followup_week_4_due_date"].widget = forms.HiddenInput()
            self.fields["four_week_followup_sent_to_email"].widget = forms.HiddenInput()


class CaseReportAcknowledgedUpdateForm(VersionForm):
    """
    Form to update Report acknowledged
    """

    report_acknowledged_date = AMPDateField(
        label="Report acknowledged date (included in equality body export)",
        help_text="This field affects the case status",
    )
    report_acknowledged_by_email = AMPCharFieldWide(
        label="Report acknowledged by (email address)"
    )
    correspondence_notes = AMPTextField(label="Correspondence notes")
    report_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
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
    report_followup_week_12_due_date = AMPDateField(
        label="12-week deadline (included in equality body export)"
    )
    twelve_week_update_request_sent_to_email = AMPCharFieldWide(
        label="12-week request sent to (email address)"
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    twelve_week_update_requested_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
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
        model = SimplifiedCase
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
        simplified_case: SimplifiedCase = self.instance
        if (
            simplified_case
            and simplified_case.twelve_week_correspondence_acknowledged_date
        ):
            self.fields["twelve_week_1_week_chaser_sent_date"].widget = (
                forms.HiddenInput()
            )
            self.fields["twelve_week_1_week_chaser_due_date"].widget = (
                forms.HiddenInput()
            )
            self.fields["twelve_week_1_week_chaser_sent_to_email"].widget = (
                forms.HiddenInput()
            )


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
        choices=SimplifiedCase.OrganisationResponse.choices,
    )
    twelve_week_correspondence_notes = AMPTextField(
        label="12-week correspondence notes"
    )
    twelve_week_update_request_ack_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
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
        model = SimplifiedCase
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
        model = SimplifiedCase
        fields = [
            "version",
            "twelve_week_retest_complete_date",
        ]


class CaseReviewChangesUpdateForm(VersionForm):
    """
    Form to record review of changes made by PSB
    """

    retested_website_date = AMPDateField(
        label="Retested website? (included in equality body export)"
    )
    psb_progress_notes = AMPTextField(
        label="Summary of progress made from public sector body (included in equality body export)"
    )
    is_ready_for_final_decision = AMPChoiceRadioField(
        label="Is this case ready for final decision?",
        help_text="This field affects the case status",
        choices=Boolean.choices,
    )
    review_changes_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "retested_website_date",
            "psb_progress_notes",
            "is_ready_for_final_decision",
            "review_changes_complete_date",
        ]


class CaseEnforcementRecommendationUpdateForm(VersionForm):
    """
    Form to record sending the enforcement recommendation decision
    """

    compliance_email_sent_date = AMPDateField(
        label="Date when compliance decision email sent to public sector body (included in equality body export)"
    )
    compliance_decision_sent_to_email = AMPCharFieldWide(
        label="Compliance decision sent to (email address)"
    )
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Recommendation for equality body (included in equality body export)",
        choices=SimplifiedCase.RecommendationForEnforcement.choices,
    )
    recommendation_notes = AMPTextField(
        label="Enforcement recommendation notes including exemptions (included in equality body export)",
        help_text=mark_safe(
            '<span id="amp-copy-text-control" class="amp-control" tabindex="0">Fill text field</span>'
            " with notes from Summary of progress made from public sector body"
        ),
    )
    enforcement_recommendation_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "compliance_email_sent_date",
            "compliance_decision_sent_to_email",
            "recommendation_for_enforcement",
            "recommendation_notes",
            "enforcement_recommendation_complete_date",
        ]


class CaseCloseUpdateForm(VersionForm):
    """
    Form to record the case close decision
    """

    case_completed = AMPChoiceRadioField(
        label="Case completed",
        choices=SimplifiedCase.CaseCompleted.choices,
        help_text="This field affects the case status",
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "case_completed",
            "case_close_complete_date",
        ]

    def clean(self):
        case_completed: str = self.cleaned_data["case_completed"]
        if case_completed == SimplifiedCase.CaseCompleted.COMPLETE_SEND:
            case: SimplifiedCase = self.instance
            equality_body_columns: list[EqualityBodyCSVColumn] = (
                populate_equality_body_columns(case=case)
            )
            required_data_missing_columns: list[EqualityBodyCSVColumn] = [
                column
                for column in equality_body_columns
                if column.required_data_missing
            ]
            if required_data_missing_columns:
                raise ValidationError(
                    "Ensure all the required fields are complete before you close the case to send to the equalities body"
                )
        return self.cleaned_data


class PostCaseUpdateForm(VersionForm):
    """
    Form to record post case notes
    """

    post_case_notes = AMPTextField(label="Summary of events after the case was closed")
    case_updated_date = AMPDateField(label="Case updated")
    post_case_complete_date = AMPDatePageCompleteField()
    psb_appeal_notes = AMPTextField(label="Public sector body statement appeal notes")

    class Meta:
        model = SimplifiedCase
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
        model = SimplifiedCase
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
        model = SimplifiedCase
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
        choices=SimplifiedCase.EnforcementBodyClosedCase.choices,
    )
    enforcement_body_finished_date = AMPDateField(
        label="Date equality body completed the case",
    )
    equality_body_notes = AMPTextField(label="Equality body notes")

    class Meta:
        model = SimplifiedCase
        fields = [
            "version",
            "sent_to_enforcement_body_sent_date",
            "equality_body_case_start_date",
            "enforcement_body_case_owner",
            "enforcement_body_closed_case",
            "enforcement_body_finished_date",
            "equality_body_notes",
        ]


class ListCaseEqualityBodyCorrespondenceUpdateForm(VersionForm):
    """
    Form for list equality body correspondence page
    """

    class Meta:
        model = SimplifiedCase
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


class ZendeskTicketConfirmDeleteUpdateForm(forms.ModelForm):
    """
    Form for confirming the deletion of a zendesk ticket
    """

    is_deleted = forms.BooleanField(
        label="Conform you want to remove Zendest ticket",
        required=False,
        widget=AMPBooleanCheckboxWidget(attrs={"label": "Remove ticket"}),
    )

    class Meta:
        model = ZendeskTicket
        fields = ["is_deleted"]


class ZendeskTicketCreateUpdateForm(forms.ModelForm):
    """
    Form for updating a zendesk ticket
    """

    summary = AMPTextField(label="Summary")
    url = AMPURLField(label="Link to Zendesk ticket")

    class Meta:
        model = ZendeskTicket
        fields = ["summary", "url"]
