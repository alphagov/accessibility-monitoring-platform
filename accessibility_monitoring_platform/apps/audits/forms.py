"""
Forms - checks (called tests by users)
"""
from typing import Any, List, Tuple

from django import forms

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateCheckboxWidget,
    AMPRadioSelectWidget,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPURLField,
)
from ..cases.models import (
    Case,
    BOOLEAN_CHOICES,
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    WEBSITE_INITIAL_COMPLIANCE_CHOICES,
    WEBSITE_STATE_FINAL_CHOICES,
)
from .models import (
    Audit,
    Page,
    CheckResult,
    SCREEN_SIZE_CHOICES,
    EXEMPTIONS_STATE_CHOICES,
    DECLARATION_STATE_CHOICES,
    SCOPE_STATE_CHOICES,
    COMPLIANCE_STATE_CHOICES,
    NON_REGULATION_STATE_CHOICES,
    DISPROPORTIONATE_BURDEN_STATE_CHOICES,
    CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
    PREPARATION_DATE_STATE_CHOICES,
    METHOD_STATE_CHOICES,
    REVIEW_STATE_CHOICES,
    FEEDBACK_STATE_CHOICES,
    CONTACT_INFORMATION_STATE_CHOICES,
    ENFORCEMENT_PROCEDURE_STATE_CHOICES,
    ACCESS_REQUIREMENTS_STATE_CHOICES,
    ACCESSIBILITY_STATEMENT_STATE_CHOICES,
    REPORT_OPTIONS_NEXT_CHOICES,
    CHECK_RESULT_STATE_CHOICES,
    RETEST_CHECK_RESULT_STATE_CHOICES,
    ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT,
    ARCHIVE_REPORT_NEXT_ISSUE_TEXT,
    WcagDefinition,
    TEST_TYPE_CHOICES,
    StatementCheck,
    StatementCheckResult,
    STATEMENT_CHECK_CHOICES,
    STATEMENT_CHECK_TYPE_CHOICES,
    Retest,
)

CHECK_RESULT_TYPE_FILTER_CHOICES: List[Tuple[str, str]] = TEST_TYPE_CHOICES + [
    ("", "All"),
]
TEST_CHECK_RESULT_STATE_FILTER_CHOICES: List[
    Tuple[str, str]
] = CHECK_RESULT_STATE_CHOICES + [("", "All")]
RETEST_CHECK_RESULT_STATE_FILTER_CHOICES: List[
    Tuple[str, str]
] = RETEST_CHECK_RESULT_STATE_CHOICES + [("", "All")]


class AuditMetadataUpdateForm(VersionForm):
    """
    Form for editing check metadata
    """

    date_of_test = AMPDateField(label="Date of test")
    screen_size = AMPChoiceField(label="Screen size", choices=SCREEN_SIZE_CHOICES)
    exemptions_state = AMPChoiceRadioField(
        label="Exemptions?",
        choices=EXEMPTIONS_STATE_CHOICES,
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

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
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
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "Mark page as not found"}),
    )
    is_contact_page = AMPChoiceCheckboxField(
        label="Page is a contact",
        choices=BOOLEAN_CHOICES,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
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
        choices=CHECK_RESULT_STATE_CHOICES,
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


class CaseWebsiteDecisionUpdateForm(VersionForm):
    """
    Form for editing website compliance decision
    """

    website_compliance_state_initial = AMPChoiceRadioField(
        label="Initial website compliance decision",
        help_text="This field effects the case status",
        choices=WEBSITE_INITIAL_COMPLIANCE_CHOICES,
    )
    compliance_decision_notes = AMPTextField(label="Initial website compliance notes")

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "website_compliance_state_initial",
            "compliance_decision_notes",
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
        choices=SCOPE_STATE_CHOICES,
    )
    archive_scope_notes = AMPTextField(label="Notes")
    archive_feedback_state = AMPChoiceRadioField(
        label="Feedback",
        choices=FEEDBACK_STATE_CHOICES,
    )
    archive_feedback_notes = AMPTextField(label="Notes")
    archive_contact_information_state = AMPChoiceRadioField(
        label="Contact Information",
        choices=CONTACT_INFORMATION_STATE_CHOICES,
    )
    archive_contact_information_notes = AMPTextField(label="Notes")
    archive_enforcement_procedure_state = AMPChoiceRadioField(
        label="Enforcement Procedure",
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
    )
    archive_enforcement_procedure_notes = AMPTextField(label="Notes")
    archive_declaration_state = AMPChoiceRadioField(
        label="Declaration",
        choices=DECLARATION_STATE_CHOICES,
    )
    archive_declaration_notes = AMPTextField(label="Notes")
    archive_compliance_state = AMPChoiceRadioField(
        label="Compliance Status",
        choices=COMPLIANCE_STATE_CHOICES,
    )
    archive_compliance_notes = AMPTextField(label="Notes")
    archive_non_regulation_state = AMPChoiceRadioField(
        label="Non-accessible Content - non compliance with regulations",
        choices=NON_REGULATION_STATE_CHOICES,
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
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
    )
    archive_disproportionate_burden_notes = AMPTextField(label="Notes")
    archive_content_not_in_scope_state = AMPChoiceRadioField(
        label="Non-accessible Content - the content is not within the scope of the applicable legislation",
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
    )
    archive_content_not_in_scope_notes = AMPTextField(label="Notes")
    archive_preparation_date_state = AMPChoiceRadioField(
        label="Preparation Date",
        choices=PREPARATION_DATE_STATE_CHOICES,
    )
    archive_preparation_date_notes = AMPTextField(label="Notes")
    archive_review_state = AMPChoiceRadioField(
        label="Review",
        choices=REVIEW_STATE_CHOICES,
    )
    archive_review_notes = AMPTextField(label="Notes")
    archive_method_state = AMPChoiceRadioField(
        label="Method",
        choices=METHOD_STATE_CHOICES,
    )
    archive_method_notes = AMPTextField(label="Notes")
    archive_access_requirements_state = AMPChoiceRadioField(
        label="Access Requirements",
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
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


class ArchiveAuditStatementDecisionUpdateForm(VersionForm):
    """
    Form for editing statement compliance decision completion
    """

    archive_audit_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "archive_audit_statement_decision_complete_date",
        ]


class StatementCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check
    """

    check_result_state = AMPChoiceRadioField(
        label="",
        choices=STATEMENT_CHECK_CHOICES,
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

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    audit_statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "audit_statement_overview_complete_date",
        ]


class AuditStatementWebsiteUpdateForm(VersionForm):
    """
    Form for editing statement website
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


class ArchiveCaseStatementDecisionUpdateForm(VersionForm):
    """
    Form for editing statement compliance decision
    """

    accessibility_statement_state = AMPChoiceRadioField(
        label="Initial accessibility statement compliance decision",
        help_text="This field effects the case status",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes = AMPTextField(
        label="Initial accessibility statement compliance notes"
    )

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "accessibility_statement_state",
            "accessibility_statement_notes",
        ]


class AuditSummaryUpdateForm(VersionForm):
    """
    Form for editing audit summary
    """

    audit_summary_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_summary_complete_date",
        ]


class ArchiveAuditReportOptionsUpdateForm(VersionForm):
    """
    Form for editing report options
    """

    archive_accessibility_statement_state = AMPChoiceRadioField(
        label="Accessibility statement",
        choices=ACCESSIBILITY_STATEMENT_STATE_CHOICES,
    )
    archive_accessibility_statement_not_correct_format = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
            choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
            choices=BOOLEAN_CHOICES,
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
            choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=REPORT_OPTIONS_NEXT_CHOICES,
    )
    archive_report_next_change_statement = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        choices=BOOLEAN_CHOICES,
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
        ]


class RetestCheckResultFilterForm(forms.Form):
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


class RetestCheckResultForm(forms.ModelForm):
    """
    Form for updating a single check test on retest
    """

    id = forms.IntegerField(widget=forms.HiddenInput())
    retest_state = AMPChoiceRadioField(
        label="Issue fixed?",
        choices=RETEST_CHECK_RESULT_STATE_CHOICES,
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


RetestCheckResultFormset: Any = forms.formset_factory(RetestCheckResultForm, extra=0)


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


class CaseFinalWebsiteDecisionUpdateForm(VersionForm):
    """
    Form to record final website compliance decision
    """

    website_state_final = AMPChoiceRadioField(
        label="12-week website compliance decision",
        choices=WEBSITE_STATE_FINAL_CHOICES,
    )
    website_state_notes_final = AMPTextField(
        label="12-week website compliance decision notes",
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "website_state_final",
            "website_state_notes_final",
        ]


class Audit12WeekStatementUpdateForm(VersionForm):
    """
    Form to add a statement at 12-weeks (no initial statement)
    """

    twelve_week_accessibility_statement_url = AMPURLField(
        label="Link to accessibility statement",
        help_text="Blank out to remove appended statement",
    )
    audit_retest_accessibility_statement_backup_url = AMPURLField(
        label="Link to backup accessibility statement",
        help_text="Blank out to remove appended statement",
    )

    class Meta:
        model = Audit
        fields = [
            "version",
            "twelve_week_accessibility_statement_url",
            "audit_retest_accessibility_statement_backup_url",
        ]


class ArchiveAuditRetestStatement1UpdateForm(VersionForm):
    """
    Form for retesting accessibility statement 1 checks
    """

    archive_audit_retest_scope_state = AMPChoiceRadioField(
        label="",
        choices=SCOPE_STATE_CHOICES,
    )
    archive_audit_retest_scope_notes = AMPTextField(label="Notes")
    archive_audit_retest_feedback_state = AMPChoiceRadioField(
        label="",
        choices=FEEDBACK_STATE_CHOICES,
    )
    archive_audit_retest_feedback_notes = AMPTextField(label="Notes")
    archive_audit_retest_contact_information_state = AMPChoiceRadioField(
        label="",
        choices=CONTACT_INFORMATION_STATE_CHOICES,
    )
    archive_audit_retest_contact_information_notes = AMPTextField(label="Notes")
    archive_audit_retest_enforcement_procedure_state = AMPChoiceRadioField(
        label="",
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
    )
    archive_audit_retest_enforcement_procedure_notes = AMPTextField(label="Notes")
    archive_audit_retest_declaration_state = AMPChoiceRadioField(
        label="",
        choices=DECLARATION_STATE_CHOICES,
    )
    archive_audit_retest_declaration_notes = AMPTextField(label="Notes")
    archive_audit_retest_compliance_state = AMPChoiceRadioField(
        label="",
        choices=COMPLIANCE_STATE_CHOICES,
    )
    archive_audit_retest_compliance_notes = AMPTextField(label="Notes")
    archive_audit_retest_non_regulation_state = AMPChoiceRadioField(
        label="",
        choices=NON_REGULATION_STATE_CHOICES,
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
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
    )
    archive_audit_retest_disproportionate_burden_notes = AMPTextField(label="Notes")
    archive_audit_retest_content_not_in_scope_state = AMPChoiceRadioField(
        label="",
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
    )
    archive_audit_retest_content_not_in_scope_notes = AMPTextField(label="Notes")
    archive_audit_retest_preparation_date_state = AMPChoiceRadioField(
        label="",
        choices=PREPARATION_DATE_STATE_CHOICES,
    )
    archive_audit_retest_preparation_date_notes = AMPTextField(label="Notes")
    archive_audit_retest_review_state = AMPChoiceRadioField(
        label="",
        choices=REVIEW_STATE_CHOICES,
    )
    archive_audit_retest_review_notes = AMPTextField(label="Notes")
    archive_audit_retest_method_state = AMPChoiceRadioField(
        label="",
        choices=METHOD_STATE_CHOICES,
    )
    archive_audit_retest_method_notes = AMPTextField(label="Notes")
    archive_audit_retest_access_requirements_state = AMPChoiceRadioField(
        label="",
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
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


class RetestStatementCheckResultForm(forms.ModelForm):
    """
    Form for updating a single statement check retest
    """

    retest_state = AMPChoiceRadioField(
        label="",
        choices=STATEMENT_CHECK_CHOICES,
        widget=AMPRadioSelectWidget(),
    )
    retest_comment = AMPTextField(label="Retest comments")

    class Meta:
        model = StatementCheckResult
        fields = [
            "retest_state",
            "retest_comment",
        ]


RetestStatementCheckResultFormset: Any = forms.modelformset_factory(
    StatementCheckResult, RetestStatementCheckResultForm, extra=0
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
    Form for editing statement website
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


class AuditRetestStatementOtherUpdateForm(VersionForm):
    """
    Form for editing statement other
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


class ArchiveAuditRetestStatementDecisionUpdateForm(VersionForm):
    """
    Form for retesting statement decision
    """

    audit_retest_accessibility_statement_backup_url = AMPURLField(
        label="Link to 12-week saved accessibility statement, only if not compliant",
    )
    archive_audit_retest_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_accessibility_statement_backup_url",
            "archive_audit_retest_statement_decision_complete_date",
        ]


class ArchiveCaseFinalStatementDecisionUpdateForm(VersionForm):
    """
    Form to record final accessibility statement compliance decision
    """

    accessibility_statement_state_final = AMPChoiceRadioField(
        label="12-week accessibility statement compliance decision",
        choices=ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    )
    accessibility_statement_notes_final = AMPTextField(
        label="12-week accessibility statement compliance notes",
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "accessibility_statement_state_final",
            "accessibility_statement_notes_final",
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
    type = AMPChoiceRadioField(label="Type", choices=TEST_TYPE_CHOICES)
    url_on_w3 = AMPURLField(label="Link to WCAG", required=True)
    description = AMPCharFieldWide(label="Description")
    report_boilerplate = AMPTextField(label="Report boilerplate")

    class Meta:
        model = WcagDefinition
        fields: List[str] = [
            "name",
            "type",
            "url_on_w3",
            "description",
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
    type = AMPChoiceField(
        label="Statement section", choices=STATEMENT_CHECK_TYPE_CHOICES
    )
    success_criteria = AMPCharFieldWide(label="Success criteria")
    report_text = AMPCharFieldWide(label="Report text")

    class Meta:
        model = StatementCheck
        fields: List[str] = [
            "label",
            "type",
            "success_criteria",
            "report_text",
        ]


class RetestUpdateForm(forms.ModelForm):
    """
    Form for updating equality body retest metadata
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
