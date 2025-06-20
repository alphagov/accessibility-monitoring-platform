"""
Forms - detailed
"""

import re

import requests
from django import forms
from django.core.exceptions import ValidationError

from ..common.forms import (
    AMPAuditorModelChoiceField,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPIntegerField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from ..common.models import Boolean, Sector, SubCategory
from .models import Contact, DetailedCase, DetailedCaseHistory


class DetailedCaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name",
    )
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    home_page_url = AMPURLField(label="Full URL")
    website_name = AMPCharFieldWide(label="Website name")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=DetailedCase.EnforcementBody.choices,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=DetailedCase.PsbLocation.choices,
    )
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

    class Meta:
        model = DetailedCase
        fields = [
            "organisation_name",
            "parental_organisation_name",
            "home_page_url",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
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
        if case_id.isdigit() and DetailedCase.objects.filter(id=case_id).exists():
            return previous_case_url
        else:
            raise ValidationError("Previous case not found in platform")


class DetailedCaseMetadataUpdateForm(DetailedCaseCreateForm, VersionForm):
    case_metadata_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "organisation_name",
            "parental_organisation_name",
            "home_page_url",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "previous_case_url",
            "is_complaint",
            "case_metadata_complete_date",
        ]


class DetailedCaseStatusUpdateForm(VersionForm):
    status = AMPChoiceField(label="Status", choices=DetailedCase.Status)

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


class ManageContactsUpdateForm(VersionForm):
    """Form for updating contacts list page"""

    manage_contacts_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "manage_contacts_complete_date",
        ]


class ContactCreateForm(forms.ModelForm):
    """Form for creating a contact"""

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    contact_point = AMPCharFieldWide(label="Contact point")
    preferred = AMPChoiceRadioField(
        label="Preferred contact", choices=Contact.Preferred.choices
    )
    type = AMPChoiceRadioField(label="Type of contact", choices=Contact.Type.choices)

    class Meta:
        model = Contact
        fields = ["name", "job_title", "contact_point", "preferred", "type"]


class ContactUpdateForm(VersionForm):
    """Form for updating a contact"""

    name = AMPCharFieldWide(label="Name")
    job_title = AMPCharFieldWide(label="Job title")
    contact_point = AMPCharFieldWide(label="Email")
    preferred = AMPChoiceRadioField(
        label="Preferred contact?", choices=Contact.Preferred.choices
    )
    type = AMPChoiceRadioField(label="Type of contact", choices=Contact.Type.choices)

    class Meta:
        model = Contact
        fields = ["version", "name", "job_title", "contact_point", "preferred", "type"]


class ContactInformationRequestUpdateForm(VersionForm):
    """Form for updating contact information request page"""

    first_contact_date = AMPDateField(label="First contact sent date")
    first_contact_sent_to = AMPCharFieldWide(label="First contact sent to")
    request_contact_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "first_contact_date",
            "first_contact_sent_to",
            "request_contact_details_complete_date",
        ]


class ContactChasingRecordUpdateForm(VersionForm):
    """Form for updating chasing record for contact page"""

    notes = AMPTextField(label="Chasing record")
    chasing_record_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "notes",
            "chasing_record_complete_date",
        ]


class ContactInformationDeliveredUpdateForm(VersionForm):
    """Form for updating contact information delivered page"""

    contact_acknowledged_date = AMPDateField(label="Request acknowledged")
    contact_acknowledged_by = AMPCharFieldWide(label="Acknowledged by")
    saved_to_google_drive = AMPChoiceCheckboxField(
        label="Information saved to Google drive?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Information saved to Google drive"}
        ),
    )
    information_delivered_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "contact_acknowledged_date",
            "contact_acknowledged_by",
            "saved_to_google_drive",
            "information_delivered_complete_date",
        ]


class InitialTestingDetailsUpdateForm(VersionForm):
    """Form for updating initial testing details page"""

    auditor = AMPAuditorModelChoiceField(label="Auditor")
    monitor_folder_url = AMPURLField(label="Link to monitor folder")
    initial_testing_details_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "auditor",
            "monitor_folder_url",
            "initial_testing_details_complete_date",
        ]


class InitialTestingOutcomeUpdateForm(VersionForm):
    """Form for updating initial testing outcome page"""

    initial_test_date = AMPDateField(label="Test date")
    initial_total_number_of_issues = AMPIntegerField(label="Total number of issues")
    initial_testing_outcome_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "initial_test_date",
            "initial_total_number_of_issues",
            "initial_testing_outcome_complete_date",
        ]


class InitialWebsiteComplianceUpdateForm(VersionForm):
    """Form for updating initial website compliance page"""

    initial_website_compliance_state = AMPChoiceRadioField(
        label="Initial compliance decision",
        choices=DetailedCase.WebsiteCompliance.choices,
    )
    initial_website_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "initial_website_compliance_state",
            "initial_website_compliance_complete_date",
        ]


class InitialDisproportionateBurdenUpdateForm(VersionForm):
    """Form for updating initial disproportionate burden page"""

    initial_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Initial disproportionate burden claim",
        choices=DetailedCase.DisproportionateBurden.choices,
    )
    initial_disproportionate_burden_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "initial_disproportionate_burden_claim",
            "initial_disproportionate_burden_complete_date",
        ]


class InitialStatementComplianceUpdateForm(VersionForm):
    """Form for updating initial statement compliance page"""

    initial_statement_compliance_state = AMPChoiceRadioField(
        label="Initial compliance decision",
        choices=DetailedCase.StatementCompliance.choices,
    )
    initial_statement_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "initial_statement_compliance_state",
            "initial_statement_compliance_complete_date",
        ]


class ReportDraftUpdateForm(VersionForm):
    """Form for updating report draft page"""

    report_draft_url = AMPURLField(label="Link to report draft")
    report_ready_for_qa = AMPChoiceRadioField(
        label="Report ready for QA process?",
        choices=Boolean.choices,
    )
    report_draft_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_draft_url",
            "report_ready_for_qa",
            "report_draft_complete_date",
        ]


class QAApprovalUpdateForm(VersionForm):
    """Form for updating report QA approval page"""

    reviewer = AMPAuditorModelChoiceField(label="QA auditor")
    report_approved_status = AMPChoiceRadioField(
        label="Report approved?",
        choices=DetailedCase.ReportApprovedStatus.choices,
    )
    qa_approval_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "reviewer",
            "report_approved_status",
            "qa_approval_complete_date",
        ]


class PublishReportUpdateForm(VersionForm):
    """Form for updating publish report page"""

    equality_body_report_url = AMPURLField(label="Link to equality body PDF report")
    public_report_url = AMPURLField(label="Link to public report")
    publish_report_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "equality_body_report_url",
            "public_report_url",
            "publish_report_complete_date",
        ]


class ReportSentUpdateForm(VersionForm):
    """Form for updating correspondence report sent page"""

    report_sent_date = AMPDateField(label="Report sent on")
    report_sent_to = AMPCharFieldWide(label="Report sent to")
    report_sent_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_sent_date",
            "report_sent_to",
            "report_sent_complete_date",
        ]


class ReportAcknowledgedUpdateForm(VersionForm):
    """Form for updating correspondence report acknowledged page"""

    report_acknowledged_date = AMPDateField(label="Report acknowledged on")
    report_acknowledged_by = AMPCharFieldWide(label="Report acknowledged by")
    report_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "report_acknowledged_date",
            "report_acknowledged_by",
            "report_acknowledged_complete_date",
        ]


class TwelveWeekDeadlineUpdateForm(VersionForm):
    """Form for updating correspondence 12-week deadline page"""

    twelve_week_deadline_date = AMPDateField(label="12-week deadline")
    twelve_week_deadline_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_deadline_date",
            "twelve_week_deadline_complete_date",
        ]


class TwelveWeekRequestUpdateForm(VersionForm):
    """Form for updating correspondence 12-week update request page"""

    twelve_week_update_date = AMPDateField(label="12-week update requested")
    twelve_week_update_to = AMPCharFieldWide(label="Request sent to")
    twelve_week_update_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_update_date",
            "twelve_week_update_to",
            "twelve_week_update_complete_date",
        ]


class TwelveWeekAcknowledgedUpdateForm(VersionForm):
    """Form for updating correspondence 12-week acknowledged page"""

    twelve_week_acknowledged_date = AMPDateField(label="12-week update acknowledged")
    twelve_week_acknowledged_by = AMPCharFieldWide(label="Acknowledged by")
    twelve_week_acknowledged_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "twelve_week_acknowledged_date",
            "twelve_week_acknowledged_by",
            "twelve_week_acknowledged_complete_date",
        ]


class RetestResultUpdateForm(VersionForm):
    """Form for updating reviewing changes retest result page"""

    retest_date = AMPDateField(label="Retest date")
    retest_total_number_of_issues = AMPIntegerField(
        label="Total number of remaining issues"
    )
    retest_result_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_date",
            "retest_total_number_of_issues",
            "retest_result_complete_date",
        ]


class RetestSummaryUpdateForm(VersionForm):
    """Form for updating reviewing changes summary of changes page"""

    summary_of_changes_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "summary_of_changes_complete_date",
        ]


class RetestWebsiteComplianceUpdateForm(VersionForm):
    """Form for updating reviewing changes website compliance page"""

    retest_website_compliance_state = AMPChoiceRadioField(
        label="Retest compliance decision",
        choices=DetailedCase.WebsiteCompliance.choices,
    )
    retest_website_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_website_compliance_state",
            "retest_website_compliance_complete_date",
        ]


class RetestDisproportionateBurdenUpdateForm(VersionForm):
    """Form for updating reviewing changes disproportionate burden page"""

    retest_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Retest disproportionate burden claim",
        choices=DetailedCase.DisproportionateBurden.choices,
    )
    retest_disproportionate_burden_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_disproportionate_burden_claim",
            "retest_disproportionate_burden_complete_date",
        ]


class RetestStatementComplianceUpdateForm(VersionForm):
    """Form for updating reviewing changes statement compliance page"""

    retest_statement_backup_url = AMPURLField(label="Link to backup of statement")
    retest_statement_compliance_state = AMPChoiceRadioField(
        label="Retest compliance decision",
        choices=DetailedCase.StatementCompliance.choices,
    )
    retest_statement_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "retest_statement_backup_url",
            "retest_statement_compliance_state",
            "retest_statement_compliance_complete_date",
        ]


class RetestMetricsUpdateForm(VersionForm):
    """Form for updating reviewing changes final metrics page"""

    number_of_days_to_retest = AMPIntegerField(label="Days taken to retest")
    retest_metrics_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "number_of_days_to_retest",
            "retest_metrics_complete_date",
        ]


class CaseCloseUpdateForm(VersionForm):
    """Form for updating closing the case page"""

    case_close_decision_state = AMPChoiceRadioField(
        label="Enforcement recommendation",
        choices=DetailedCase.CaseCloseDecision.choices,
    )
    case_close_decision_notes = AMPTextField(label="Enforcement recommendation details")
    case_close_decision_sent_date = AMPDateField(label="Date decision email sent")
    case_close_decision_sent_to = AMPCharFieldWide(label="Decision sent to")
    is_feedback_survey_sent = AMPChoiceCheckboxField(
        label="Feedback survey sent",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Feedback survey sent to this organisation?"}
        ),
    )
    case_close_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "case_close_decision_state",
            "case_close_decision_notes",
            "case_close_decision_sent_date",
            "case_close_decision_sent_to",
            "is_feedback_survey_sent",
            "case_close_complete_date",
        ]


class EnforcementBodyMetadataUpdateForm(VersionForm):
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
    is_case_added_to_stats = AMPChoiceCheckboxField(
        label="Case stats",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "Case added to stats tab?"}),
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
            "is_case_added_to_stats",
            "enforcement_body_metadata_complete_date",
        ]
