"""
Forms - mobile
"""

from django import forms

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
from .models import MobileCase, MobileCaseHistory, MobileContact, MobileZendeskTicket


class MobileCaseCreateForm(PreviousCaseURLForm):
    """
    Form for creating a case
    """

    home_page_url = AMPURLField(label="Organisation URL")
    organisation_name = AMPCharFieldWide(label="Organisation name")
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    app_name = AMPCharFieldWide(label="App name")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=MobileCase.EnforcementBody.choices,
        initial=MobileCase.EnforcementBody.EHRC,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=MobileCase.PsbLocation.choices,
        initial=MobileCase.PsbLocation.ENGLAND,
    )
    previous_case_url = AMPURLField(
        label="URL to previous case · Included in export",
        help_text="If the app has been previously audited, include a link to the case below",
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )

    class Meta:
        model = MobileCase
        fields = [
            "home_page_url",
            "organisation_name",
            "parental_organisation_name",
            "app_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "previous_case_url",
            "is_complaint",
        ]


class MobileCaseMetadataUpdateForm(PreviousCaseURLForm, VersionForm):
    home_page_url = AMPURLField(label="Organisation URL")
    organisation_name = AMPCharFieldWide(label="Organisation name")
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    app_name = AMPCharFieldWide(label="App name")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=MobileCase.EnforcementBody.choices,
        initial=MobileCase.EnforcementBody.EHRC,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=MobileCase.PsbLocation.choices,
        initial=MobileCase.PsbLocation.ENGLAND,
    )
    previous_case_url = AMPURLField(
        label="URL to previous case · Included in export",
        help_text="If the app has been previously audited, include a link to the case below",
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )
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
        model = MobileCase
        fields = [
            "version",
            "home_page_url",
            "organisation_name",
            "parental_organisation_name",
            "app_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "previous_case_url",
            "is_complaint",
            "case_folder_url",
            "is_feedback_requested",
            "case_metadata_complete_date",
        ]


class MobileCaseStatusUpdateForm(VersionForm):
    status = AMPChoiceField(
        label="Status",
        choices=MobileCase.Status.choices,
    )

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "status",
        ]


class MobileCaseHistoryCreateForm(forms.ModelForm):
    value = AMPTextField(label="New note")

    class Meta:
        model = MobileCaseHistory
        fields = [
            "value",
        ]


class MobileCaseHistoryUpdateForm(forms.ModelForm):
    label = AMPCharFieldWide(label="Label")
    value = AMPTextField(label="New note")

    class Meta:
        model = MobileCaseHistory
        fields = [
            "label",
            "value",
        ]


class MobileManageContactsUpdateForm(VersionForm):
    """Form for updating contacts list page"""

    manage_contacts_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "manage_contacts_complete_date",
        ]


class MobileContactCreateForm(forms.ModelForm):
    """Form for creating a contact"""

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    contact_details = AMPCharFieldWide(label="Contact details")
    preferred = AMPChoiceRadioField(
        label="Preferred contact",
        choices=MobileContact.Preferred.choices,
        initial=MobileContact.Preferred.UNKNOWN,
    )
    information = AMPTextField(label="Information about contact")

    class Meta:
        model = MobileContact
        fields = ["name", "job_title", "contact_details", "preferred", "information"]


class MobileContactUpdateForm(VersionForm, MobileContactCreateForm):
    """Form for updating a contact"""

    class Meta:
        model = MobileContact
        fields = [
            "version",
            "name",
            "job_title",
            "contact_details",
            "preferred",
            "information",
        ]


class MobileContactInformationRequestUpdateForm(VersionForm):
    """Form for updating contact information request page"""

    contact_information_request_start_date = AMPDateField(
        label="Information request process started",
        help_text="This is when we first reach out to an organisation via any method regardless of whether we have a contact or not",
    )
    contact_information_request_end_date = AMPDateField(label="Information received")
    contact_information_request_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "contact_information_request_start_date",
            "contact_information_request_end_date",
            "contact_information_request_complete_date",
        ]


class MobileInitialTestAuditorUpdateForm(VersionForm):
    """Form for updating initial test auditor page"""

    auditor = AMPAuditorModelChoiceField(label="Auditor")
    initial_auditor_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "auditor",
            "initial_auditor_complete_date",
        ]


class MobileInitialTestiOSDetailsUpdateForm(VersionForm):
    """Form for updating initial test iOS details page"""

    ios_test_included = AMPChoiceRadioField(
        label="Case includes iOS test?",
        choices=MobileCase.TestIncluded.choices,
    )
    ios_app_url = AMPURLField(label="iOS app URL")
    initial_ios_test_start_date = AMPDateField(label="Test start date")
    initial_ios_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "ios_test_included",
            "ios_app_url",
            "initial_ios_test_start_date",
            "initial_ios_details_complete_date",
        ]


class MobileInitialTestiOSOutcomeUpdateForm(VersionForm):
    """Form for updating initial test iOS outcome page"""

    initial_ios_test_end_date = AMPDateField(label="Test end date")
    initial_ios_total_number_of_screens = AMPIntegerField(
        label="Number of screens tested"
    )
    initial_ios_total_number_of_issues = AMPIntegerField(
        label="Number of issues found · Included in export",
        help_text="This does not include best practice issues",
    )
    initial_ios_app_compliance_state = AMPChoiceRadioField(
        label="Initial app compliance decision",
        choices=MobileCase.AppCompliance.choices,
    )
    initial_ios_statement_compliance_state = AMPChoiceRadioField(
        label="Initial statement compliance decision",
        choices=MobileCase.StatementCompliance.choices,
    )
    initial_ios_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Initial disproportionate burden claim",
        choices=MobileCase.DisproportionateBurden.choices,
    )
    initial_ios_outcome_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "initial_ios_test_end_date",
            "initial_ios_total_number_of_screens",
            "initial_ios_total_number_of_issues",
            "initial_ios_app_compliance_state",
            "initial_ios_statement_compliance_state",
            "initial_ios_disproportionate_burden_claim",
            "initial_ios_outcome_complete_date",
        ]


class MobileInitialTestAndroidDetailsUpdateForm(VersionForm):
    """Form for updating initial test Android details page"""

    android_test_included = AMPChoiceRadioField(
        label="Case includes Android test?",
        choices=MobileCase.TestIncluded.choices,
    )
    android_app_url = AMPURLField(label="Android app URL")
    initial_android_test_start_date = AMPDateField(label="Test start date")
    initial_android_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "android_test_included",
            "android_app_url",
            "initial_android_test_start_date",
            "initial_android_details_complete_date",
        ]


class MobileInitialTestAndroidOutcomeUpdateForm(VersionForm):
    """Form for updating initial test Android outcome page"""

    initial_android_test_end_date = AMPDateField(label="Test end date")
    initial_android_total_number_of_screens = AMPIntegerField(
        label="Number of screens tested"
    )
    initial_android_total_number_of_issues = AMPIntegerField(
        label="Number of issues found · Included in export",
        help_text="This does not include best practice issues",
    )
    initial_android_app_compliance_state = AMPChoiceRadioField(
        label="Initial app compliance decision",
        choices=MobileCase.AppCompliance.choices,
    )
    initial_android_statement_compliance_state = AMPChoiceRadioField(
        label="Initial statement compliance decision",
        choices=MobileCase.StatementCompliance.choices,
    )
    initial_android_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Initial disproportionate burden claim",
        choices=MobileCase.DisproportionateBurden.choices,
    )
    initial_android_outcome_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "initial_android_test_end_date",
            "initial_android_total_number_of_screens",
            "initial_android_total_number_of_issues",
            "initial_android_app_compliance_state",
            "initial_android_statement_compliance_state",
            "initial_android_disproportionate_burden_claim",
            "initial_android_outcome_complete_date",
        ]


class MobileReportReadyForQAUpdateForm(VersionForm):
    """Form for updating report ready for QA page"""

    report_ready_for_qa = AMPChoiceRadioField(
        label="Reports ready for QA process?",
        choices=Boolean.choices,
    )
    report_ready_for_qa_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "report_ready_for_qa",
            "report_ready_for_qa_complete_date",
        ]


class MobileQAAuditorUpdateForm(VersionForm):
    """Form for updating report QA auditor page"""

    reviewer = AMPAuditorModelChoiceField(label="QA auditor")
    qa_auditor_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "reviewer",
            "qa_auditor_complete_date",
        ]


class MobileQACommentsUpdateForm(VersionForm):
    """
    Form for updating QA comments page
    """

    body: AMPTextField = AMPTextField(
        label="Add comment",
        widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "12"}),
    )

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "body",
        ]


class MobileQAApprovalUpdateForm(VersionForm):
    """Form for updating report QA approval page"""

    report_approved_status = AMPChoiceRadioField(
        label="Reports approved?",
        choices=MobileCase.ReportApprovedStatus.choices,
    )
    qa_approval_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "report_approved_status",
            "qa_approval_complete_date",
        ]


class MobileFinalReportUpdateForm(VersionForm):
    """Form for updating publish report page"""

    equality_body_report_url_ios = AMPURLField(
        label="Link to equality body PDF report for iOS · Included in export"
    )
    equality_body_report_url_android = AMPURLField(
        label="Link to equality body PDF report for Android · Included in export"
    )
    final_report_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "equality_body_report_url_ios",
            "equality_body_report_url_android",
            "final_report_complete_date",
        ]


class MobileReportSentUpdateForm(VersionForm):
    """Form for updating correspondence report sent page"""

    report_sent_date = AMPDateField(label="Reports sent on · Included in export")
    report_sent_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "report_sent_date",
            "report_sent_complete_date",
        ]


class MobileReportAcknowledgedUpdateForm(VersionForm):
    """Form for updating correspondence report acknowledged page"""

    report_acknowledged_date = AMPDateField(
        label="Reports acknowledged on · Included in export"
    )
    report_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "report_acknowledged_date",
            "report_acknowledged_complete_date",
        ]


class MobileTwelveWeekDeadlineUpdateForm(VersionForm):
    """Form for updating correspondence 12-week deadline page"""

    twelve_week_deadline_date = AMPDateField(
        label="12-week deadline · Included in export",
        widget=AMPDateWidget(attrs={"populate_with_12_week_only": True}),
    )
    twelve_week_deadline_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "twelve_week_deadline_date",
            "twelve_week_deadline_complete_date",
        ]


class MobileTwelveWeekRequestUpdateForm(VersionForm):
    """Form for updating correspondence 12-week update request page"""

    twelve_week_update_date = AMPDateField(label="12-week update requested")
    twelve_week_update_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "twelve_week_update_date",
            "twelve_week_update_complete_date",
        ]


class MobileTwelveWeekReceivedUpdateForm(VersionForm):
    """Form for updating correspondence 12-week update received page"""

    twelve_week_received_date = AMPDateField(label="12-week update received")
    twelve_week_received_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "twelve_week_received_date",
            "twelve_week_received_complete_date",
        ]


class MobileRetestiOSResultUpdateForm(VersionForm):
    """Form for updating reviewing changes iOS retesting page"""

    retest_ios_start_date = AMPDateField(
        label="Latest retest date · Included in export"
    )
    retest_ios_total_number_of_issues = AMPIntegerField(
        label="Total number of remaining issues · Included in export"
    )
    retest_ios_result_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "retest_ios_start_date",
            "retest_ios_total_number_of_issues",
            "retest_ios_result_complete_date",
        ]


class MobileRetestiOSComplianceDecisionsUpdateForm(VersionForm):
    """Form for updating reviewing changes iOS retest result page"""

    retest_ios_app_compliance_state = AMPChoiceRadioField(
        label="Retest app compliance decision · Included in export",
        choices=MobileCase.AppCompliance.choices,
    )
    retest_ios_app_compliance_information = AMPTextField(
        label="Retest app compliance decision information"
    )
    retest_ios_statement_compliance_state = AMPChoiceRadioField(
        label="Retest statement compliance decision · Included in export",
        choices=MobileCase.StatementCompliance.choices,
    )
    retest_ios_statement_compliance_information = AMPTextField(
        label="Retest statement compliance decision information"
    )
    retest_ios_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Retest disproportionate burden claim · Included in export",
        choices=MobileCase.DisproportionateBurden.choices,
    )
    retest_ios_disproportionate_burden_information = AMPTextField(
        label="Retest disproportionate burden information · Included in export"
    )
    retest_ios_compliance_decisions_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "retest_ios_app_compliance_state",
            "retest_ios_app_compliance_information",
            "retest_ios_statement_compliance_state",
            "retest_ios_statement_compliance_information",
            "retest_ios_disproportionate_burden_claim",
            "retest_ios_disproportionate_burden_information",
            "retest_ios_compliance_decisions_complete_date",
        ]


class MobileRetestAndroidResultUpdateForm(VersionForm):
    """Form for updating reviewing changes Android retesting page"""

    retest_android_start_date = AMPDateField(
        label="Latest retest date · Included in export"
    )
    retest_android_total_number_of_issues = AMPIntegerField(
        label="Total number of remaining issues · Included in export"
    )
    retest_android_result_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "retest_android_start_date",
            "retest_android_total_number_of_issues",
            "retest_android_result_complete_date",
        ]


class MobileRetestAndroidComplianceDecisionsUpdateForm(VersionForm):
    """Form for updating reviewing changes Android retest result page"""

    retest_android_app_compliance_state = AMPChoiceRadioField(
        label="Retest app compliance decision · Included in export",
        choices=MobileCase.AppCompliance.choices,
    )
    retest_android_app_compliance_information = AMPTextField(
        label="Retest app compliance decision information"
    )
    retest_android_statement_compliance_state = AMPChoiceRadioField(
        label="Retest statement compliance decision · Included in export",
        choices=MobileCase.StatementCompliance.choices,
    )
    retest_android_statement_compliance_information = AMPTextField(
        label="Retest statement compliance decision information"
    )
    retest_android_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Retest disproportionate burden claim · Included in export",
        choices=MobileCase.DisproportionateBurden.choices,
    )
    retest_android_disproportionate_burden_information = AMPTextField(
        label="Retest disproportionate burden information · Included in export"
    )
    retest_android_compliance_decisions_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "retest_android_app_compliance_state",
            "retest_android_app_compliance_information",
            "retest_android_statement_compliance_state",
            "retest_android_statement_compliance_information",
            "retest_android_disproportionate_burden_claim",
            "retest_android_disproportionate_burden_information",
            "retest_android_compliance_decisions_complete_date",
        ]


class MobileCaseRecommendationUpdateForm(VersionForm):
    """Form for updating the case recommendation page"""

    psb_progress_info = AMPTextField(
        label="Progress summary and PSB response · Included in export"
    )
    recommendation_for_enforcement = AMPChoiceRadioField(
        label="Enforcement recommendation · Included in export",
        choices=MobileCase.RecommendationForEnforcement.choices,
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
        model = MobileCase
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


class MobileCaseCloseUpdateForm(VersionForm):
    """Form for updating closing the case page"""

    case_close_decision_state = AMPChoiceRadioField(
        label="Case completed",
        choices=MobileCase.CaseCloseDecision,
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "case_close_decision_state",
            "case_close_complete_date",
        ]


class MobileStatementEnforcementUpdateForm(VersionForm):
    """Form for updating the statement enforcement page"""

    psb_statement_appeal_information = AMPTextField(
        label="Public sector body appeal information"
    )
    statement_enforcement_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "psb_statement_appeal_information",
            "statement_enforcement_complete_date",
        ]


class MobileEnforcementBodyMetadataUpdateForm(VersionForm):
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
        choices=MobileCase.EnforcementBodyClosedCase.choices,
    )
    enforcement_body_completed_case_date = AMPDateField(
        label="Date equality body completed the case"
    )
    enforcement_body_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "enforcement_body_sent_date",
            "enforcement_body_started_date",
            "enforcement_body_case_owner",
            "enforcement_body_closed_case_state",
            "enforcement_body_completed_case_date",
            "enforcement_body_metadata_complete_date",
        ]


class MobileZendeskTicketCreateUpdateForm(forms.ModelForm):
    """
    Form for updating a zendesk ticket
    """

    summary = AMPTextField(label="Summary")
    url = AMPURLField(label="Link to Zendesk ticket")

    class Meta:
        model = MobileZendeskTicket
        fields = ["summary", "url"]


class MobileZendeskTicketConfirmDeleteUpdateForm(forms.ModelForm):
    """
    Form for confirming the deletion of a zendesk ticket
    """

    is_deleted = forms.BooleanField(
        label="Confirm you want to remove Zendesk ticket",
        required=False,
        widget=AMPBooleanCheckboxWidget(attrs={"label": "Remove ticket"}),
    )

    class Meta:
        model = MobileZendeskTicket
        fields = ["is_deleted"]


class MobileUnresponsivePSBUpdateForm(VersionForm):
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
        model = MobileCase
        fields = [
            "version",
            "no_psb_contact",
            "no_psb_contact_info",
        ]
