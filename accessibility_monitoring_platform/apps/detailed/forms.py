"""
Forms - detailed
"""

from django import forms
from django.core.exceptions import ValidationError

from ..cases.forms import PreviousCaseURLForm
from ..common.forms import (
    AMPAuditorModelChoiceField,
    AMPBooleanCheckboxWidget,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPDateWidget,
    AMPIntegerField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from ..common.models import Boolean, Sector, SubCategory
from .models import Contact, DetailedCase, DetailedCaseHistory, ZendeskTicket


class DetailedCaseCreateForm(PreviousCaseURLForm):
    """
    Form for creating a case
    """

    home_page_url = AMPURLField(label="Full URL · Included in export")
    organisation_name = AMPCharFieldWide(
        label="Organisation name · Included in export",
    )
    parental_organisation_name = AMPCharFieldWide(
        label="Parent organisation name · Included in export"
    )
    website_name = AMPCharFieldWide(label="Website name · Included in export")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category · Included in export",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case? · Included in export",
        choices=DetailedCase.EnforcementBody.choices,
        initial=DetailedCase.EnforcementBody.EHRC,
    )
    service_type = AMPChoiceRadioField(
        label="Type",
        choices=DetailedCase.ServiceType,
        initial=DetailedCase.ServiceType.WEBSITE,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=DetailedCase.PsbLocation.choices,
        initial=DetailedCase.PsbLocation.ENGLAND,
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint? · Included in export",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )

    class Meta:
        model = DetailedCase
        fields = [
            "home_page_url",
            "organisation_name",
            "parental_organisation_name",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "service_type",
            "psb_location",
            "service_type",
            "previous_case_url",
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


class DetailedCaseMetadataUpdateForm(DetailedCaseCreateForm, VersionForm):
    case_folder_url = AMPURLField(label="Link to case folder")
    is_feedback_requested = AMPChoiceCheckboxField(
        label="Feedback survey sent?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Feedback survey sent to this organisation?"}
        ),
    )
    case_metadata_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "home_page_url",
            "organisation_name",
            "parental_organisation_name",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "service_type",
            "psb_location",
            "previous_case_url",
            "is_complaint",
            "case_folder_url",
            "is_feedback_requested",
            "case_metadata_complete_date",
        ]


class DetailedCaseStatusUpdateForm(VersionForm):
    status = AMPChoiceField(
        label="Status",
        choices=DetailedCase.Status.choices,
    )

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "status",
        ]


class DetailedCaseHistoryCreateForm(forms.ModelForm):
    value = AMPTextField(label="New note")

    class Meta:
        model = DetailedCaseHistory
        fields = [
            "value",
        ]


class DetailedCaseHistoryUpdateForm(forms.ModelForm):
    label = AMPCharFieldWide(label="Label")
    value = AMPTextField(label="New note")

    class Meta:
        model = DetailedCaseHistory
        fields = [
            "label",
            "value",
        ]


class DetailedManageContactsUpdateForm(VersionForm):
    """Form for updating contacts list page"""

    manage_contacts_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "manage_contacts_complete_date",
        ]


class DetailedContactCreateForm(forms.ModelForm):
    """Form for creating a contact"""

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    contact_details = AMPCharFieldWide(label="Contact details")
    preferred = AMPChoiceRadioField(
        label="Preferred contact",
        choices=Contact.Preferred.choices,
        initial=Contact.Preferred.UNKNOWN,
    )
    information = AMPTextField(label="Information about contact")

    class Meta:
        model = Contact
        fields = ["name", "job_title", "contact_details", "preferred", "information"]


class DetailedContactUpdateForm(VersionForm, DetailedContactCreateForm):
    """Form for updating a contact"""

    class Meta:
        model = Contact
        fields = [
            "version",
            "name",
            "job_title",
            "contact_details",
            "preferred",
            "information",
        ]


class DetailedContactInformationRequestUpdateForm(VersionForm):
    """Form for updating contact information request page"""

    contact_information_request_start_date = AMPDateField(
        label="Information request process started",
        help_text="This is when we first reach out to an organisation via any method regardless of whether we have a contact or not",
    )
    contact_information_request_end_date = AMPDateField(label="Information received")
    contact_information_request_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "contact_information_request_start_date",
            "contact_information_request_end_date",
            "contact_information_request_complete_date",
        ]


class DetailedInitialTestingDetailsUpdateForm(VersionForm):
    """Form for updating initial testing details page"""

    auditor = AMPAuditorModelChoiceField(label="Auditor")
    initial_test_start_date = AMPDateField(label="Test start date")
    initial_testing_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "auditor",
            "initial_test_start_date",
            "initial_testing_details_complete_date",
        ]


class DetailedInitialTestingOutcomeUpdateForm(VersionForm):
    """Form for updating initial testing outcome page"""

    initial_test_end_date = AMPDateField(label="Test end date")
    initial_total_number_of_pages = AMPIntegerField(label="Number of pages tested")
    initial_total_number_of_issues = AMPIntegerField(
        label="Number of issues found · Included in export",
        help_text="This does not include best practice issues",
    )
    initial_website_compliance_state = AMPChoiceRadioField(
        label="Initial website compliance decision",
        choices=DetailedCase.WebsiteCompliance.choices,
    )
    initial_statement_compliance_state = AMPChoiceRadioField(
        label="Initial statement compliance decision",
        choices=DetailedCase.StatementCompliance.choices,
    )
    initial_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Initial disproportionate burden claim",
        choices=DetailedCase.DisproportionateBurden.choices,
    )
    initial_testing_outcome_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "initial_test_end_date",
            "initial_total_number_of_pages",
            "initial_total_number_of_issues",
            "initial_website_compliance_state",
            "initial_statement_compliance_state",
            "initial_disproportionate_burden_claim",
            "initial_testing_outcome_complete_date",
        ]


class DetailedReportReadyForQAUpdateForm(VersionForm):
    """Form for updating report ready for QA page"""

    report_ready_for_qa = AMPChoiceRadioField(
        label="Report ready for QA process?",
        choices=Boolean.choices,
    )
    status = AMPChoiceField(
        label="Status",
        choices=DetailedCase.Status.choices,
    )
    report_ready_for_qa_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_ready_for_qa",
            "status",
            "report_ready_for_qa_complete_date",
        ]


class DetailedQAAuditorUpdateForm(VersionForm):
    """Form for updating report QA auditor page"""

    reviewer = AMPAuditorModelChoiceField(label="QA auditor")
    qa_auditor_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "reviewer",
            "qa_auditor_complete_date",
        ]


class DetailedQACommentsUpdateForm(VersionForm):
    """
    Form for updating QA comments page
    """

    body: AMPTextField = AMPTextField(
        label="Add comment",
        widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "12"}),
    )

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "body",
        ]


class DetailedQAApprovalUpdateForm(VersionForm):
    """Form for updating report QA approval page"""

    report_approved_status = AMPChoiceRadioField(
        label="Report approved?",
        choices=DetailedCase.ReportApprovedStatus.choices,
    )
    qa_approval_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_approved_status",
            "qa_approval_complete_date",
        ]


class DetailedFinalReportUpdateForm(VersionForm):
    """Form for updating publish report page"""

    equality_body_report_url = AMPURLField(
        label="Link to equality body PDF report · Included in export"
    )
    final_report_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "equality_body_report_url",
            "final_report_complete_date",
        ]


class DetailedReportSentUpdateForm(VersionForm):
    """Form for updating correspondence report sent page"""

    report_sent_date = AMPDateField(label="Report sent on · Included in export")
    report_sent_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_sent_date",
            "report_sent_complete_date",
        ]


class DetailedReportAcknowledgedUpdateForm(VersionForm):
    """Form for updating correspondence report acknowledged page"""

    report_acknowledged_date = AMPDateField(
        label="Report acknowledged on · Included in export"
    )
    report_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_acknowledged_date",
            "report_acknowledged_complete_date",
        ]


class DetailedTwelveWeekDeadlineUpdateForm(VersionForm):
    """Form for updating correspondence 12-week deadline page"""

    twelve_week_deadline_date = AMPDateField(
        label="12-week deadline · Included in export",
        widget=AMPDateWidget(attrs={"populate_with_12_week_only": True}),
    )
    twelve_week_deadline_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_deadline_date",
            "twelve_week_deadline_complete_date",
        ]


class DetailedTwelveWeekRequestUpdateForm(VersionForm):
    """Form for updating correspondence 12-week update request page"""

    twelve_week_update_date = AMPDateField(label="12-week update requested")
    twelve_week_update_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_update_date",
            "twelve_week_update_complete_date",
        ]


class DetailedTwelveWeekReceivedUpdateForm(VersionForm):
    """Form for updating correspondence 12-week update received page"""

    twelve_week_received_date = AMPDateField(label="12-week update received")
    twelve_week_received_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_received_date",
            "twelve_week_received_complete_date",
        ]


class DetailedRetestResultUpdateForm(VersionForm):
    """Form for updating reviewing changes retesting page"""

    retest_start_date = AMPDateField(label="Latest retest date · Included in export")
    retest_total_number_of_issues = AMPIntegerField(
        label="Total number of remaining issues · Included in export"
    )
    retest_result_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_start_date",
            "retest_total_number_of_issues",
            "retest_result_complete_date",
        ]


class DetailedRetestComplianceDecisionsUpdateForm(VersionForm):
    """Form for updating reviewing changes retest result page"""

    retest_website_compliance_state = AMPChoiceRadioField(
        label="Retest website compliance decision · Included in export",
        choices=DetailedCase.WebsiteCompliance.choices,
    )
    retest_website_compliance_information = AMPTextField(
        label="Retest website compliance decision information"
    )
    retest_statement_compliance_state = AMPChoiceRadioField(
        label="Retest statement compliance decision · Included in export",
        choices=DetailedCase.StatementCompliance.choices,
    )
    retest_statement_compliance_information = AMPTextField(
        label="Retest statement compliance decision information"
    )
    retest_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Retest disproportionate burden claim · Included in export",
        choices=DetailedCase.DisproportionateBurden.choices,
    )
    retest_disproportionate_burden_information = AMPTextField(
        label="Retest disproportionate burden information · Included in export"
    )
    retest_compliance_decisions_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_website_compliance_state",
            "retest_website_compliance_information",
            "retest_statement_compliance_state",
            "retest_statement_compliance_information",
            "retest_disproportionate_burden_claim",
            "retest_disproportionate_burden_information",
            "retest_compliance_decisions_complete_date",
        ]


class DetailedCaseRecommendationUpdateForm(VersionForm):
    """Form for updating the case recommendation page"""

    psb_progress_info = AMPTextField(label="Case progress notes")
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Enforcement recommendation · Included in export",
        choices=DetailedCase.RecommendationForEnforcement.choices,
    )
    recommendation_info = AMPTextField(
        label="Enforcement recommendation details · Included in export"
    )
    recommendation_decision_sent_date = AMPDateField(
        label="Date decision email sent · Included in export"
    )
    recommendation_decision_sent_to = AMPCharFieldWide(
        label="Decision sent to · Included in export"
    )
    is_case_added_to_stats = AMPChoiceCheckboxField(
        label="Case stats",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "Case added to stats tab?"}),
    )
    is_feedback_requested = AMPChoiceCheckboxField(
        label="Feedback survey sent",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Feedback survey sent to this organisation?"}
        ),
    )
    case_recommendation_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "psb_progress_info",
            "recommendation_for_enforcement",
            "recommendation_info",
            "recommendation_decision_sent_date",
            "recommendation_decision_sent_to",
            "is_case_added_to_stats",
            "is_feedback_requested",
            "case_recommendation_complete_date",
        ]


class DetailedCaseCloseUpdateForm(VersionForm):
    """Form for updating closing the case page"""

    case_close_decision_state = AMPChoiceRadioField(
        label="Case completed",
        choices=DetailedCase.CaseCloseDecision,
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "case_close_decision_state",
            "case_close_complete_date",
        ]


class DetailedStatementEnforcementUpdateForm(VersionForm):
    """Form for updating the statement enforcement page"""

    psb_statement_appeal_information = AMPTextField(
        label="Public sector body appeal information"
    )
    statement_enforcement_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "psb_statement_appeal_information",
            "statement_enforcement_complete_date",
        ]


class DetailedEnforcementBodyMetadataUpdateForm(VersionForm):
    """Form for updating closing the case page"""

    enforcement_body_sent_date = AMPDateField(label="Date sent to equality body")
    enforcement_body_started_date = AMPDateField(
        label="Date equality body started the case"
    )
    enforcement_body_case_owner = AMPCharFieldWide(
        label="Equality body case owner (first name only)"
    )
    enforcement_body_closed_case_state = AMPChoiceRadioField(
        label="Equality body has officially closed the case?",
        choices=DetailedCase.EnforcementBodyClosedCase.choices,
    )
    enforcement_body_completed_case_date = AMPDateField(
        label="Date equality body completed the case"
    )
    enforcement_body_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "enforcement_body_sent_date",
            "enforcement_body_started_date",
            "enforcement_body_case_owner",
            "enforcement_body_closed_case_state",
            "enforcement_body_completed_case_date",
            "enforcement_body_metadata_complete_date",
        ]


class DetailedZendeskTicketCreateUpdateForm(forms.ModelForm):
    """
    Form for updating a zendesk ticket
    """

    summary = AMPTextField(label="Summary")
    url = AMPURLField(label="Link to Zendesk ticket")

    class Meta:
        model = ZendeskTicket
        fields = ["summary", "url"]


class DetailedZendeskTicketConfirmDeleteUpdateForm(forms.ModelForm):
    """
    Form for confirming the deletion of a zendesk ticket
    """

    is_deleted = forms.BooleanField(
        label="Confirm you want to remove Zendesk ticket",
        required=False,
        widget=AMPBooleanCheckboxWidget(attrs={"label": "Remove ticket"}),
    )

    class Meta:
        model = ZendeskTicket
        fields = ["is_deleted"]


class DetailedUnresponsivePSBUpdateForm(VersionForm):
    """Form for recording an unresponsive PSB"""

    no_psb_contact = AMPChoiceCheckboxField(
        label="Do you want to mark the PSB as unresponsive to this case?",
        help_text="Also add a case note with more information",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the PSB as unresponsive to this case"}
        ),
    )
    no_psb_contact_info = AMPTextField(
        label="Public sector body is unresponsive information"
    )

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "no_psb_contact",
            "no_psb_contact_info",
        ]
