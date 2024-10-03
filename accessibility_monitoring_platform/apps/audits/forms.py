"""
Forms - checks (called tests by users)
"""

from typing import Any, List, Tuple

from django import forms

from ..cases.models import Boolean, Case, CaseCompliance
from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPRadioSelectWidget,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from .models import (
    ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT,
    ARCHIVE_REPORT_NEXT_ISSUE_TEXT,
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)

CHECK_RESULT_TYPE_FILTER_CHOICES: List[Tuple[str, str]] = (
    WcagDefinition.Type.choices
    + [
        ("", "All"),
    ]
)
TEST_CHECK_RESULT_STATE_FILTER_CHOICES: List[Tuple[str, str]] = (
    CheckResult.Result.choices + [("", "All")]
)
RETEST_CHECK_RESULT_STATE_FILTER_CHOICES: List[Tuple[str, str]] = (
    CheckResult.RetestResult.choices + [("", "All")]
)


class AuditMetadataUpdateForm(VersionForm):
    """
    Form for editing check metadata
    """

    date_of_test = AMPDateField(label="Date of test")
    screen_size = AMPChoiceField(label="Screen size", choices=Audit.ScreenSize.choices)
    exemptions_state = AMPChoiceRadioField(
        label="Exemptions?",
        choices=Audit.Exemptions.choices,
    )
    exemptions_notes = AMPTextField(label="Notes")
    audit_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "date_of_test",
            "screen_size",
            "exemptions_state",
            "exemptions_notes",
            "audit_metadata_complete_date",
        ]


class AuditExtraPageUpdateForm(forms.ModelForm):
    """
    Form for adding and updating an extra page
    """

    name = AMPCharFieldWide(label="Page name")
    url = AMPURLField(label="URL")
    location = AMPCharFieldWide(label="Page location description if single page app")

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
            "location",
        ]


AuditExtraPageFormset: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=0
)
AuditExtraPageFormsetOneExtra: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=1
)
AuditExtraPageFormsetTwoExtra: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=2
)


class AuditStandardPageUpdateForm(AuditExtraPageUpdateForm):
    """
    Form for updating a standard page (one of the 5 types of page in every audit)
    """

    not_found = AMPChoiceCheckboxField(
        label="Not found?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "Mark page as not found"}),
    )
    is_contact_page = AMPChoiceCheckboxField(
        label="Page is a contact",
        choices=Boolean.choices,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
            "location",
            "not_found",
            "is_contact_page",
        ]


AuditStandardPageFormset: Any = forms.modelformset_factory(
    Page, AuditStandardPageUpdateForm, extra=0
)


class AuditPagesUpdateForm(VersionForm):
    """
    Form for editing pages check page
    """

    audit_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_pages_complete_date",
        ]


class AuditPageChecksForm(forms.Form):
    """
    Form for editing checks for a page
    """

    complete_date = AMPDatePageCompleteField(
        label="", widget=AMPDateCheckboxWidget(attrs={"label": "Mark page as complete"})
    )
    no_errors_date = AMPDatePageCompleteField(
        label="",
        widget=AMPDateCheckboxWidget(attrs={"label": "Web page has no errors"}),
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "complete_date",
            "no_errors_date",
        ]


class CheckResultFilterForm(forms.Form):
    """
    Form for filtering check results
    """

    name = AMPCharFieldWide(label="Filter WCAG tests, category, or grouping")
    type_filter = AMPChoiceRadioField(
        label="Type of WCAG error",
        choices=CHECK_RESULT_TYPE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )
    state_filter = AMPChoiceRadioField(
        label="Test state",
        choices=TEST_CHECK_RESULT_STATE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )

    class Meta:
        model = Page
        fields: List[str] = [
            "name",
            "type_filter",
            "state_filter",
        ]


class CheckResultForm(forms.ModelForm):
    """
    Form for updating a single check test
    """

    wcag_definition = forms.ModelChoiceField(
        queryset=WcagDefinition.objects.all(), widget=forms.HiddenInput()
    )
    check_result_state = AMPChoiceRadioField(
        label="",
        choices=CheckResult.Result.choices,
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )
    notes = AMPTextField(label="Error details")

    class Meta:
        model = CheckResult
        fields = [
            "wcag_definition",
            "check_result_state",
            "notes",
        ]


CheckResultFormset: Any = forms.formset_factory(CheckResultForm, extra=0)


class AuditWebsiteDecisionUpdateForm(VersionForm):
    """
    Form for editing website compliance decision completion
    """

    audit_website_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_website_decision_complete_date",
        ]


class CaseComplianceWebsiteInitialUpdateForm(VersionForm):
    """
    Form for editing website compliance decision
    """

    website_compliance_state_initial = AMPChoiceRadioField(
        label="Initial website compliance decision",
        help_text="This field effects the case status",
        choices=CaseCompliance.WebsiteCompliance.choices,
    )
    website_compliance_notes_initial = AMPTextField(
        label="Initial website compliance notes"
    )

    class Meta:
        model = CaseCompliance
        fields: List[str] = [
            "version",
            "website_compliance_state_initial",
            "website_compliance_notes_initial",
        ]


class ArchiveAuditStatement1UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 1 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    archive_scope_state = AMPChoiceRadioField(
        label="Scope",
        choices=Audit.Scope.choices,
    )
    archive_scope_notes = AMPTextField(label="Notes")
    archive_feedback_state = AMPChoiceRadioField(
        label="Feedback",
        choices=Audit.Feedback.choices,
    )
    archive_feedback_notes = AMPTextField(label="Notes")
    archive_contact_information_state = AMPChoiceRadioField(
        label="Contact Information",
        choices=Audit.ContactInformation.choices,
    )
    archive_contact_information_notes = AMPTextField(label="Notes")
    archive_enforcement_procedure_state = AMPChoiceRadioField(
        label="Enforcement Procedure",
        choices=Audit.EnforcementProcedure.choices,
    )
    archive_enforcement_procedure_notes = AMPTextField(label="Notes")
    archive_declaration_state = AMPChoiceRadioField(
        label="Declaration",
        choices=Audit.Declaration.choices,
    )
    archive_declaration_notes = AMPTextField(label="Notes")
    archive_compliance_state = AMPChoiceRadioField(
        label="Compliance Status",
        choices=Audit.Compliance.choices,
    )
    archive_compliance_notes = AMPTextField(label="Notes")
    archive_non_regulation_state = AMPChoiceRadioField(
        label="Non-accessible Content - non compliance with regulations",
        choices=Audit.NonRegulation.choices,
    )
    archive_non_regulation_notes = AMPTextField(label="Notes")
    archive_audit_statement_1_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["add_contact_email"] = AMPCharFieldWide(label="Email")

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "archive_scope_state",
            "archive_scope_notes",
            "archive_feedback_state",
            "archive_feedback_notes",
            "archive_contact_information_state",
            "archive_contact_information_notes",
            "archive_enforcement_procedure_state",
            "archive_enforcement_procedure_notes",
            "archive_declaration_state",
            "archive_declaration_notes",
            "archive_compliance_state",
            "archive_compliance_notes",
            "archive_non_regulation_state",
            "archive_non_regulation_notes",
            "archive_audit_statement_1_complete_date",
        ]


class ArchiveAuditStatement2UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 2 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    archive_disproportionate_burden_state = AMPChoiceRadioField(
        label="Non-accessible Content - disproportionate burden",
        choices=Audit.DisproportionateBurden.choices,
    )
    archive_disproportionate_burden_notes = AMPTextField(label="Notes")
    archive_content_not_in_scope_state = AMPChoiceRadioField(
        label="Non-accessible Content - the content is not within the scope of the applicable legislation",
        choices=Audit.ContentNotInScope.choices,
    )
    archive_content_not_in_scope_notes = AMPTextField(label="Notes")
    archive_preparation_date_state = AMPChoiceRadioField(
        label="Preparation Date",
        choices=Audit.PreparationDate.choices,
    )
    archive_preparation_date_notes = AMPTextField(label="Notes")
    archive_review_state = AMPChoiceRadioField(
        label="Review",
        choices=Audit.Review.choices,
    )
    archive_review_notes = AMPTextField(label="Notes")
    archive_method_state = AMPChoiceRadioField(
        label="Method",
        choices=Audit.Method.choices,
    )
    archive_method_notes = AMPTextField(label="Notes")
    archive_access_requirements_state = AMPChoiceRadioField(
        label="Access Requirements",
        choices=Audit.AccessRequirements.choices,
    )
    archive_access_requirements_notes = AMPTextField(label="Notes")
    archive_audit_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "archive_disproportionate_burden_state",
            "archive_disproportionate_burden_notes",
            "archive_content_not_in_scope_state",
            "archive_content_not_in_scope_notes",
            "archive_preparation_date_state",
            "archive_preparation_date_notes",
            "archive_review_state",
            "archive_review_notes",
            "archive_method_state",
            "archive_method_notes",
            "archive_access_requirements_state",
            "archive_access_requirements_notes",
            "archive_audit_statement_2_complete_date",
        ]


class AuditStatementDecisionUpdateForm(VersionForm):
    """
    Form for editing statement compliance decision completion
    """

    audit_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_statement_decision_complete_date",
        ]


class StatementCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check
    """

    check_result_state = AMPChoiceRadioField(
        label="",
        choices=StatementCheckResult.Result.choices,
        widget=AMPRadioSelectWidget(),
    )
    report_comment = AMPTextField(label="Comments for report")

    class Meta:
        model = StatementCheckResult
        fields = [
            "check_result_state",
            "report_comment",
        ]


StatementCheckResultFormset: Any = forms.modelformset_factory(
    StatementCheckResult, StatementCheckResultForm, extra=0
)


class AuditStatementOverviewUpdateForm(VersionForm):
    """
    Form for editing statement overview
    """

    statement_extra_report_text = AMPTextField(label="Extra report text")
    audit_statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "statement_extra_report_text",
            "audit_statement_overview_complete_date",
        ]


class AuditStatementWebsiteUpdateForm(VersionForm):
    """
    Form for editing statement information
    """

    audit_statement_website_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_website_complete_date",
        ]


class AuditStatementComplianceUpdateForm(VersionForm):
    """
    Form for editing statement compliance
    """

    audit_statement_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_compliance_complete_date",
        ]


class AuditStatementNonAccessibleUpdateForm(VersionForm):
    """
    Form for editing statement non-accessible
    """

    audit_statement_non_accessible_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_non_accessible_complete_date",
        ]


class AuditStatementPreparationUpdateForm(VersionForm):
    """
    Form for editing statement preparation
    """

    audit_statement_preparation_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_preparation_complete_date",
        ]


class AuditStatementFeedbackUpdateForm(VersionForm):
    """
    Form for editing statement feedback
    """

    audit_statement_feedback_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_feedback_complete_date",
        ]


class AuditStatementCustomUpdateForm(VersionForm):
    """
    Form for editing custom statement issues
    """

    audit_statement_custom_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "audit_statement_custom_complete_date",
        ]


class CustomStatementCheckResultUpdateForm(forms.ModelForm):
    """
    Form for updating a custom statement check result
    """

    report_comment = AMPTextField(label="Comments for report")
    auditor_notes = AMPTextField(label="Notes for auditor")

    class Meta:
        model = StatementCheckResult
        fields = ["report_comment", "auditor_notes"]


CustomStatementCheckResultFormset: Any = forms.modelformset_factory(
    StatementCheckResult, CustomStatementCheckResultUpdateForm, extra=0
)
CustomStatementCheckResultFormsetOneExtra: Any = forms.modelformset_factory(
    StatementCheckResult, CustomStatementCheckResultUpdateForm, extra=1
)


class InitialDisproportionateBurdenUpdateForm(VersionForm):
    """
    Form for editing initial disproportional burden claim
    """

    initial_disproportionate_burden_claim = AMPChoiceRadioField(
        label="Initial disproportionate burden claim (included in equality body export)",
        choices=Audit.DisproportionateBurden.choices,
    )
    initial_disproportionate_burden_notes = AMPTextField(
        label="Initial disproportionate burden claim details (included in equality body export)"
    )
    initial_disproportionate_burden_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "initial_disproportionate_burden_claim",
            "initial_disproportionate_burden_notes",
            "initial_disproportionate_burden_complete_date",
        ]


class CaseComplianceStatementInitialUpdateForm(VersionForm):
    """
    Form for editing statement compliance decision
    """

    statement_compliance_state_initial = AMPChoiceRadioField(
        label="Initial statement compliance decision (included in equality body export)",
        help_text="This field effects the case status",
        choices=CaseCompliance.StatementCompliance.choices,
    )
    statement_compliance_notes_initial = AMPTextField(
        label="Initial statement compliance notes"
    )

    class Meta:
        model = CaseCompliance
        fields: List[str] = [
            "version",
            "statement_compliance_state_initial",
            "statement_compliance_notes_initial",
        ]


class AuditWcagSummaryUpdateForm(VersionForm):
    """
    Form for editing WCAG audit summary
    """

    audit_wcag_summary_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_wcag_summary_complete_date",
        ]


class AuditStatementSummaryUpdateForm(VersionForm):
    """
    Form for editing statement audit summary
    """

    audit_statement_summary_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_statement_summary_complete_date",
        ]


class ArchiveAuditReportOptionsUpdateForm(VersionForm):
    """
    Form for editing report options
    """

    archive_accessibility_statement_state = AMPChoiceRadioField(
        label="Accessibility statement",
        choices=Audit.AccessibilityStatement.choices,
    )
    archive_accessibility_statement_not_correct_format = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_not_correct_format"
                ]
            }
        ),
    )
    archive_accessibility_statement_not_specific_enough = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_not_specific_enough"
                ]
            }
        ),
    )
    archive_accessibility_statement_missing_accessibility_issues = (
        AMPChoiceCheckboxField(
            label="",
            choices=Boolean.choices,
            widget=AMPChoiceCheckboxWidget(
                attrs={
                    "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                        "archive_accessibility_statement_missing_accessibility_issues"
                    ]
                }
            ),
        )
    )
    archive_accessibility_statement_missing_mandatory_wording = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_missing_mandatory_wording"
                ]
            }
        ),
    )
    archive_accessibility_statement_missing_mandatory_wording_notes = AMPTextField(
        label="Additional text for mandatory wording"
    )
    archive_accessibility_statement_needs_more_re_disproportionate = (
        AMPChoiceCheckboxField(
            label="",
            choices=Boolean.choices,
            widget=AMPChoiceCheckboxWidget(
                attrs={
                    "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                        "archive_accessibility_statement_needs_more_re_disproportionate"
                    ]
                }
            ),
        )
    )
    archive_accessibility_statement_needs_more_re_accessibility = (
        AMPChoiceCheckboxField(
            label="",
            choices=Boolean.choices,
            widget=AMPChoiceCheckboxWidget(
                attrs={
                    "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                        "archive_accessibility_statement_needs_more_re_accessibility"
                    ]
                }
            ),
        )
    )
    archive_accessibility_statement_deadline_not_complete = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_deadline_not_complete"
                ]
            }
        ),
    )
    archive_accessibility_statement_deadline_not_complete_wording = AMPTextField(
        label="Wording for missed deadline"
    )
    archive_accessibility_statement_deadline_not_sufficient = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_deadline_not_sufficient"
                ]
            }
        ),
    )
    archive_accessibility_statement_deadline_not_sufficient_wording = AMPTextField(
        label="Wording for insufficient deadline"
    )
    archive_accessibility_statement_out_of_date = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_out_of_date"
                ]
            }
        ),
    )
    archive_accessibility_statement_eass_link = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_eass_link"
                ]
            }
        ),
    )
    archive_accessibility_statement_template_update = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_template_update"
                ]
            }
        ),
    )
    archive_accessibility_statement_accessible = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_accessible"
                ]
            }
        ),
    )
    archive_accessibility_statement_prominent = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "archive_accessibility_statement_prominent"
                ]
            }
        ),
    )
    archive_accessibility_statement_report_text_wording = AMPTextField(
        label="Extra wording for report"
    )
    archive_report_options_next = AMPChoiceRadioField(
        label="What to do next",
        choices=Audit.ReportOptionsNext.choices,
    )
    archive_report_next_change_statement = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_NEXT_ISSUE_TEXT[
                    "archive_report_next_change_statement"
                ]
            }
        ),
    )
    archive_report_next_no_statement = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_NEXT_ISSUE_TEXT[
                    "archive_report_next_no_statement"
                ]
            }
        ),
    )
    archive_report_next_statement_not_right = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_NEXT_ISSUE_TEXT[
                    "archive_report_next_statement_not_right"
                ]
            }
        ),
    )
    archive_report_next_statement_matches = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_NEXT_ISSUE_TEXT[
                    "archive_report_next_statement_matches"
                ]
            }
        ),
    )
    archive_report_next_disproportionate_burden = AMPChoiceCheckboxField(
        label="",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": ARCHIVE_REPORT_NEXT_ISSUE_TEXT[
                    "archive_report_next_disproportionate_burden"
                ]
            }
        ),
    )
    archive_report_options_notes = AMPTextField(label="Notes")
    archive_audit_report_options_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "archive_accessibility_statement_state",
            "archive_accessibility_statement_not_correct_format",
            "archive_accessibility_statement_not_specific_enough",
            "archive_accessibility_statement_missing_accessibility_issues",
            "archive_accessibility_statement_missing_mandatory_wording",
            "archive_accessibility_statement_missing_mandatory_wording_notes",
            "archive_accessibility_statement_needs_more_re_disproportionate",
            "archive_accessibility_statement_needs_more_re_accessibility",
            "archive_accessibility_statement_deadline_not_complete",
            "archive_accessibility_statement_deadline_not_complete_wording",
            "archive_accessibility_statement_deadline_not_sufficient",
            "archive_accessibility_statement_deadline_not_sufficient_wording",
            "archive_accessibility_statement_out_of_date",
            "archive_accessibility_statement_eass_link",
            "archive_accessibility_statement_template_update",
            "archive_accessibility_statement_accessible",
            "archive_accessibility_statement_prominent",
            "archive_accessibility_statement_report_text_wording",
            "archive_report_options_next",
            "archive_report_next_change_statement",
            "archive_report_next_no_statement",
            "archive_report_next_statement_not_right",
            "archive_report_next_statement_matches",
            "archive_report_next_disproportionate_burden",
            "archive_report_options_notes",
            "archive_audit_report_options_complete_date",
        ]


class AuditRetestMetadataUpdateForm(VersionForm):
    """
    Form for editing audit retest metadata
    """

    retest_date = AMPDateField(label="Date of retest")
    audit_retest_metadata_notes = AMPTextField(label="Notes")
    audit_retest_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "retest_date",
            "audit_retest_metadata_notes",
            "audit_retest_metadata_complete_date",
        ]


class AuditRetestPagesUpdateForm(VersionForm):
    """
    Form for editing audit retest pages
    """

    audit_retest_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_pages_complete_date",
        ]


class AuditRetestPageChecksForm(forms.Form):
    """
    Form for retesting checks for a page
    """

    retest_complete_date = AMPDatePageCompleteField(
        label="", widget=AMPDateCheckboxWidget(attrs={"label": "Mark page as complete"})
    )
    retest_page_missing_date = AMPDatePageCompleteField(
        label="",
        widget=AMPDateCheckboxWidget(attrs={"label": "Page missing"}),
    )
    retest_notes = AMPTextField(label="Additional issues found on page")

    class Meta:
        model = Audit
        fields: List[str] = [
            "retest_complete_date",
            "retest_page_missing_date",
            "retest_notes",
        ]


class AuditRetestCheckResultFilterForm(forms.Form):
    """
    Form for filtering check results on retest
    """

    name = AMPCharFieldWide(label="Filter WCAG tests, category, or grouping")
    type_filter = AMPChoiceRadioField(
        label="Type of WCAG error",
        choices=CHECK_RESULT_TYPE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )
    state_filter = AMPChoiceRadioField(
        label="Retest state",
        choices=RETEST_CHECK_RESULT_STATE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )

    class Meta:
        model = Page
        fields: List[str] = [
            "name",
            "type_filter",
            "state_filter",
        ]


class AuditRetestCheckResultForm(forms.ModelForm):
    """
    Form for updating a single check test on retest
    """

    id = forms.IntegerField(widget=forms.HiddenInput())
    retest_state = AMPChoiceRadioField(
        label="Issue fixed?",
        choices=CheckResult.RetestResult.choices,
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )
    retest_notes = AMPTextField(label="Notes")

    class Meta:
        model = CheckResult
        fields = [
            "id",
            "retest_state",
            "retest_notes",
        ]


AuditRetestCheckResultFormset: Any = forms.formset_factory(
    AuditRetestCheckResultForm, extra=0
)


class AuditRetestWebsiteDecisionUpdateForm(VersionForm):
    """
    Form for retest website compliance decision completion
    """

    audit_retest_website_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_website_decision_complete_date",
        ]


class CaseComplianceWebsite12WeekUpdateForm(VersionForm):
    """
    Form to record final website compliance decision
    """

    website_compliance_state_12_week = AMPChoiceRadioField(
        label="12-week website compliance decision",
        choices=CaseCompliance.WebsiteCompliance.choices,
    )
    website_compliance_notes_12_week = AMPTextField(
        label="12-week website compliance decision notes",
    )

    class Meta:
        model = CaseCompliance
        fields = [
            "version",
            "website_compliance_state_12_week",
            "website_compliance_notes_12_week",
        ]


class ArchiveAuditRetestStatement1UpdateForm(VersionForm):
    """
    Form for retesting accessibility statement 1 checks
    """

    archive_audit_retest_scope_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Scope.choices,
    )
    archive_audit_retest_scope_notes = AMPTextField(label="Notes")
    archive_audit_retest_feedback_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Feedback.choices,
    )
    archive_audit_retest_feedback_notes = AMPTextField(label="Notes")
    archive_audit_retest_contact_information_state = AMPChoiceRadioField(
        label="",
        choices=Audit.ContactInformation.choices,
    )
    archive_audit_retest_contact_information_notes = AMPTextField(label="Notes")
    archive_audit_retest_enforcement_procedure_state = AMPChoiceRadioField(
        label="",
        choices=Audit.EnforcementProcedure.choices,
    )
    archive_audit_retest_enforcement_procedure_notes = AMPTextField(label="Notes")
    archive_audit_retest_declaration_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Declaration.choices,
    )
    archive_audit_retest_declaration_notes = AMPTextField(label="Notes")
    archive_audit_retest_compliance_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Compliance.choices,
    )
    archive_audit_retest_compliance_notes = AMPTextField(label="Notes")
    archive_audit_retest_non_regulation_state = AMPChoiceRadioField(
        label="",
        choices=Audit.NonRegulation.choices,
    )
    archive_audit_retest_non_regulation_notes = AMPTextField(label="Notes")
    archive_audit_retest_statement_1_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "archive_audit_retest_scope_state",
            "archive_audit_retest_scope_notes",
            "archive_audit_retest_feedback_state",
            "archive_audit_retest_feedback_notes",
            "archive_audit_retest_contact_information_state",
            "archive_audit_retest_contact_information_notes",
            "archive_audit_retest_enforcement_procedure_state",
            "archive_audit_retest_enforcement_procedure_notes",
            "archive_audit_retest_declaration_state",
            "archive_audit_retest_declaration_notes",
            "archive_audit_retest_compliance_state",
            "archive_audit_retest_compliance_notes",
            "archive_audit_retest_non_regulation_state",
            "archive_audit_retest_non_regulation_notes",
            "archive_audit_retest_statement_1_complete_date",
        ]


class ArchiveAuditRetestStatement2UpdateForm(VersionForm):
    """
    Form for retesting accessibility statement 2 checks
    """

    archive_audit_retest_disproportionate_burden_state = AMPChoiceRadioField(
        label="",
        choices=Audit.DisproportionateBurden.choices,
    )
    archive_audit_retest_disproportionate_burden_notes = AMPTextField(label="Notes")
    archive_audit_retest_content_not_in_scope_state = AMPChoiceRadioField(
        label="",
        choices=Audit.ContentNotInScope.choices,
    )
    archive_audit_retest_content_not_in_scope_notes = AMPTextField(label="Notes")
    archive_audit_retest_preparation_date_state = AMPChoiceRadioField(
        label="",
        choices=Audit.PreparationDate.choices,
    )
    archive_audit_retest_preparation_date_notes = AMPTextField(label="Notes")
    archive_audit_retest_review_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Review.choices,
    )
    archive_audit_retest_review_notes = AMPTextField(label="Notes")
    archive_audit_retest_method_state = AMPChoiceRadioField(
        label="",
        choices=Audit.Method.choices,
    )
    archive_audit_retest_method_notes = AMPTextField(label="Notes")
    archive_audit_retest_access_requirements_state = AMPChoiceRadioField(
        label="",
        choices=Audit.AccessRequirements.choices,
    )
    archive_audit_retest_access_requirements_notes = AMPTextField(label="Notes")
    archive_audit_retest_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "archive_audit_retest_disproportionate_burden_state",
            "archive_audit_retest_disproportionate_burden_notes",
            "archive_audit_retest_content_not_in_scope_state",
            "archive_audit_retest_content_not_in_scope_notes",
            "archive_audit_retest_preparation_date_state",
            "archive_audit_retest_preparation_date_notes",
            "archive_audit_retest_review_state",
            "archive_audit_retest_review_notes",
            "archive_audit_retest_method_state",
            "archive_audit_retest_method_notes",
            "archive_audit_retest_access_requirements_state",
            "archive_audit_retest_access_requirements_notes",
            "archive_audit_retest_statement_2_complete_date",
        ]


class AuditRetestStatementCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check retest
    """

    retest_state = AMPChoiceRadioField(
        label="",
        choices=StatementCheckResult.Result.choices,
        widget=AMPRadioSelectWidget(),
    )
    retest_comment = AMPTextField(label="Retest comments")

    class Meta:
        model = StatementCheckResult
        fields = [
            "retest_state",
            "retest_comment",
        ]


AuditRetestStatementCheckResultFormset: Any = forms.modelformset_factory(
    StatementCheckResult, AuditRetestStatementCheckResultForm, extra=0
)


class AuditRetestStatementOverviewUpdateForm(VersionForm):
    """
    Form for editing statement overview
    """

    audit_retest_statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_overview_complete_date",
        ]


class AuditRetestStatementWebsiteUpdateForm(VersionForm):
    """
    Form for editing statement information
    """

    audit_retest_statement_website_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_website_complete_date",
        ]


class AuditRetestStatementComplianceUpdateForm(VersionForm):
    """
    Form for editing statement compliance
    """

    audit_retest_statement_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_compliance_complete_date",
        ]


class AuditRetestStatementNonAccessibleUpdateForm(VersionForm):
    """
    Form for editing statement non-accessible
    """

    audit_retest_statement_non_accessible_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_non_accessible_complete_date",
        ]


class AuditRetestStatementPreparationUpdateForm(VersionForm):
    """
    Form for editing statement preparation
    """

    audit_retest_statement_preparation_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_preparation_complete_date",
        ]


class AuditRetestStatementFeedbackUpdateForm(VersionForm):
    """
    Form for editing statement feedback
    """

    audit_retest_statement_feedback_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_feedback_complete_date",
        ]


class AuditRetestStatementCustomUpdateForm(VersionForm):
    """
    Form for editing statement custom
    """

    audit_retest_statement_custom_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_custom_complete_date",
        ]


class AuditRetestStatementComparisonUpdateForm(VersionForm):
    """
    Form for retesting statement comparison
    """

    audit_retest_statement_comparison_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_comparison_complete_date",
        ]


class AuditRetestStatementDecisionUpdateForm(VersionForm):
    """
    Form for retesting statement decision
    """

    audit_retest_accessibility_statement_backup_url = AMPURLField(
        label="Link to 12-week saved accessibility statement, only if not compliant",
    )
    audit_retest_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_accessibility_statement_backup_url",
            "audit_retest_statement_decision_complete_date",
        ]


class TwelveWeekDisproportionateBurdenUpdateForm(VersionForm):
    """
    Form for editing twelve_week disproportional burden claim
    """

    twelve_week_disproportionate_burden_claim = AMPChoiceRadioField(
        label="12-week disproportionate burden claim (included in equality body export)",
        choices=Audit.DisproportionateBurden.choices,
    )
    twelve_week_disproportionate_burden_notes = AMPTextField(
        label="12-week disproportionate burden claim details (included in equality body export)"
    )
    twelve_week_disproportionate_burden_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "twelve_week_disproportionate_burden_claim",
            "twelve_week_disproportionate_burden_notes",
            "twelve_week_disproportionate_burden_complete_date",
        ]


class CaseComplianceStatement12WeekUpdateForm(VersionForm):
    """
    Form to record final accessibility statement compliance decision
    """

    statement_compliance_state_12_week = AMPChoiceRadioField(
        label="12-week statement compliance decision (included in equality body export)",
        choices=CaseCompliance.StatementCompliance.choices,
    )
    statement_compliance_notes_12_week = AMPTextField(
        label="12-week statement compliance notes",
    )

    class Meta:
        model = CaseCompliance
        fields = [
            "version",
            "statement_compliance_state_12_week",
            "statement_compliance_notes_12_week",
        ]


class WcagDefinitionSearchForm(forms.Form):
    """
    Form for searching for WCAG definitions
    """

    wcag_definition_search = AMPCharFieldWide(
        widget=forms.TextInput(
            attrs={
                "class": "govuk-input",
                "placeholder": "Search term",
            }
        )
    )


class WcagDefinitionCreateUpdateForm(forms.ModelForm):
    """
    Form for creating WCAG definition
    """

    name = AMPCharFieldWide(label="Name", required=True)
    date_start = AMPDateField(label="Start date")
    date_end = AMPDateField(label="End Date")
    type = AMPChoiceRadioField(label="Type", choices=WcagDefinition.Type.choices)
    url_on_w3 = AMPURLField(label="Link to WCAG", required=True)
    description = AMPCharFieldWide(label="Description")
    hint = AMPCharFieldWide(label="Hint")
    report_boilerplate = AMPTextField(label="Report boilerplate")

    class Meta:
        model = WcagDefinition
        fields: List[str] = [
            "name",
            "date_start",
            "date_end",
            "type",
            "url_on_w3",
            "description",
            "hint",
            "report_boilerplate",
        ]


class StatementCheckSearchForm(forms.Form):
    """
    Form for searching for statement checks
    """

    statement_check_search = AMPCharFieldWide(
        widget=forms.TextInput(
            attrs={
                "class": "govuk-input",
                "placeholder": "Search term",
            }
        )
    )


class StatementCheckCreateUpdateForm(forms.ModelForm):
    """
    Form for creating statement check
    """

    label = AMPCharFieldWide(label="Name", required=True)
    date_start = AMPDateField(label="Start date")
    date_end = AMPDateField(label="End date")
    type = AMPChoiceField(
        label="Statement section", choices=StatementCheck.Type.choices
    )
    success_criteria = AMPCharFieldWide(label="Success criteria")
    report_text = AMPCharFieldWide(label="Report text")

    class Meta:
        model = StatementCheck
        fields: List[str] = [
            "label",
            "date_start",
            "date_end",
            "type",
            "success_criteria",
            "report_text",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = [
            (value, label)
            for value, label in StatementCheck.Type.choices
            if value != StatementCheck.Type.OVERVIEW
        ]


class RetestUpdateForm(forms.ModelForm):
    """
    Form for updating equality body retest
    """

    date_of_retest = AMPDateField(label="Date of retest")
    retest_notes = AMPTextField(label="Retest notes")
    complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "date_of_retest",
            "retest_notes",
            "complete_date",
        ]


class RetestPageChecksForm(forms.ModelForm):
    """
    Form for equality body retesting checks for a page
    """

    complete_date = AMPDatePageCompleteField(
        label="", widget=AMPDateCheckboxWidget(attrs={"label": "Mark page as complete"})
    )
    missing_date = AMPDatePageCompleteField(
        label="",
        widget=AMPDateCheckboxWidget(attrs={"label": "Page missing"}),
    )
    additional_issues_notes = AMPTextField(label="Additional issues found on page")

    class Meta:
        model = RetestPage
        fields: List[str] = [
            "complete_date",
            "missing_date",
            "additional_issues_notes",
        ]


class RetestCheckResultForm(forms.ModelForm):
    """
    Form for updating a single check test on equality body requested retest
    """

    id = forms.IntegerField(widget=forms.HiddenInput())
    retest_state = AMPChoiceRadioField(
        label="Issue fixed?",
        choices=CheckResult.RetestResult.choices,
        widget=AMPRadioSelectWidget(attrs={"horizontal": True}),
    )
    retest_notes = AMPTextField(label="Notes")

    class Meta:
        model = RetestCheckResult
        fields = [
            "id",
            "retest_state",
            "retest_notes",
        ]


RetestCheckResultFormset: Any = forms.modelformset_factory(
    RetestCheckResult, form=RetestCheckResultForm, extra=0
)


class RetestComparisonUpdateForm(forms.ModelForm):
    """
    Form for updating equality body retest comparison complete
    """

    comparison_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "comparison_complete_date",
        ]


class RetestComplianceUpdateForm(forms.ModelForm):
    """
    Form for updating equality body retest compliance
    """

    retest_compliance_state = AMPChoiceRadioField(
        label="Website compliance decision",
        choices=Retest.Compliance.choices,
    )
    compliance_notes = AMPTextField(label="Notes")
    compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "retest_compliance_state",
            "compliance_notes",
            "compliance_complete_date",
        ]


class StatementPageUpdateForm(forms.ModelForm):
    """
    Form for updating a statement page
    """

    url = AMPURLField(label="Link to statement")
    backup_url = AMPURLField(label="Statement backup")
    added_stage = AMPChoiceRadioField(
        label="Statement added", choices=StatementPage.AddedStage.choices
    )

    class Meta:
        model = StatementPage
        fields = ["url", "backup_url", "added_stage"]


StatementPageFormset: Any = forms.modelformset_factory(
    StatementPage, StatementPageUpdateForm, extra=0
)
StatementPageFormsetOneExtra: Any = forms.modelformset_factory(
    StatementPage, StatementPageUpdateForm, extra=1
)


class AuditStatementPagesUpdateForm(VersionForm):
    """
    Form for statement pages update at initial test
    """

    audit_statement_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_statement_pages_complete_date",
        ]


class TwelveWeekStatementPagesUpdateForm(VersionForm):
    """
    Form for statement pages update at 12-week retest
    """

    audit_retest_statement_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_pages_complete_date",
        ]


class RetestStatementPagesUpdateForm(VersionForm):
    """
    Form for statement pages update at equality body-requested retest
    """

    statement_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_pages_complete_date",
        ]


class RetestStatementCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check retest
    """

    check_result_state = AMPChoiceRadioField(
        label="Retest result",
        choices=RetestStatementCheckResult.Result.choices,
        widget=AMPRadioSelectWidget(),
    )
    comment = AMPTextField(label="Comments for equality body email")

    class Meta:
        model = RetestStatementCheckResult
        fields = [
            "check_result_state",
            "comment",
        ]


RetestStatementCheckResultFormset: Any = forms.modelformset_factory(
    RetestStatementCheckResult, RetestStatementCheckResultForm, extra=0
)


class RetestStatementOverviewUpdateForm(VersionForm):
    """
    Form for editing retest statement overview
    """

    statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_overview_complete_date",
        ]


class RetestStatementWebsiteUpdateForm(VersionForm):
    """
    Form for editing retest statement information
    """

    statement_website_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_website_complete_date",
        ]


class RetestStatementComplianceUpdateForm(VersionForm):
    """
    Form for editing retest statement compliance
    """

    statement_compliance_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_compliance_complete_date",
        ]


class RetestStatementNonAccessibleUpdateForm(VersionForm):
    """
    Form for editing retest statement non-accessible
    """

    statement_non_accessible_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_non_accessible_complete_date",
        ]


class RetestStatementPreparationUpdateForm(VersionForm):
    """
    Form for editing retest statement preparation
    """

    statement_preparation_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_preparation_complete_date",
        ]


class RetestStatementFeedbackUpdateForm(VersionForm):
    """
    Form for editing retest statement feedback
    """

    statement_feedback_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_feedback_complete_date",
        ]


class RetestStatementCustomUpdateForm(VersionForm):
    """
    Form for editing retest statement custom
    """

    statement_custom_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_custom_complete_date",
        ]


class RetestStatementCustomCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check retest
    """

    comment = AMPTextField(label="Retest comments")

    class Meta:
        model = RetestStatementCheckResult
        fields = [
            "comment",
        ]


RetestStatementCustomCheckResultFormset: Any = forms.modelformset_factory(
    RetestStatementCheckResult, RetestStatementCustomCheckResultForm, extra=0
)
RetestStatementCustomCheckResultFormsetOneExtra: Any = forms.modelformset_factory(
    RetestStatementCheckResult, RetestStatementCustomCheckResultForm, extra=1
)


class RetestStatementResultsUpdateForm(VersionForm):
    """
    Form for completion of page showing results of statement content checks
    """

    statement_results_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_results_complete_date",
        ]


class RetestDisproportionateBurdenUpdateForm(VersionForm):
    """
    Form for editing equality body retest disproportional burden claim
    """

    disproportionate_burden_claim = AMPChoiceRadioField(
        label="Disproportionate burden claim",
        choices=Audit.DisproportionateBurden.choices,
    )
    disproportionate_burden_notes = AMPTextField(
        label="Disproportionate burden claim details"
    )
    disproportionate_burden_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "disproportionate_burden_claim",
            "disproportionate_burden_notes",
            "disproportionate_burden_complete_date",
        ]


class RetestStatementDecisionUpdateForm(VersionForm):
    """
    Form for editing equality body requested retest statement compliance decision completion
    """

    statement_compliance_state = AMPChoiceRadioField(
        label="Statement compliance decision",
        choices=CaseCompliance.StatementCompliance.choices,
    )
    statement_compliance_notes = AMPTextField(label="Notes")
    statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: List[str] = [
            "version",
            "statement_compliance_state",
            "statement_compliance_notes",
            "statement_decision_complete_date",
        ]
