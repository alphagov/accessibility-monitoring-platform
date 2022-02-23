"""
Forms - checks (called tests by users)
"""
from typing import Any, List

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
    AMPModelChoiceField,
    AMPURLField,
)
from ..cases.models import (
    Case,
    BOOLEAN_CHOICES,
    ACCESSIBILITY_STATEMENT_DECISION_CHOICES,
    IS_WEBSITE_COMPLIANT_CHOICES,
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
    REPORT_ACCESSIBILITY_ISSUE_TEXT,
    REPORT_NEXT_ISSUE_TEXT,
    WcagDefinition,
)


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

    url = AMPURLField(label="URL")
    name = AMPCharFieldWide(label="Page name")

    class Meta:
        model = Page
        fields = [
            "url",
            "name",
        ]


AuditExtraPageFormset: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=0
)
AuditExtraPageFormsetOneExtra: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=1
)


class AuditStandardPageUpdateForm(AuditExtraPageUpdateForm):
    """
    Form for updating a standard page (one of the 5 types of page in every audit)
    """

    not_found = AMPChoiceCheckboxField(
        label="Not found?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )

    class Meta:
        model = Page
        fields = [
            "url",
            "name",
            "not_found",
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


class AuditPageModelChoiceField(AMPModelChoiceField):
    """Add completed tick to model choice labels"""

    def label_from_instance(self, obj):
        completed_tick: str = " ✓" if obj.complete_date else ""
        return f"{obj}{completed_tick}"


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

    name = AMPCharFieldWide(label="")
    manual = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Manual tests"})
    )
    axe = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Axe tests"})
    )
    pdf = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "PDF"})
    )
    error_found = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Error found"})
    )
    no_issue = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "No issue"})
    )
    not_tested = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Not tested"})
    )

    class Meta:
        model = Page
        fields: List[str] = [
            "name",
            "manual",
            "axe",
            "pdf",
            "error_found",
            "no_issue",
            "not_tested",
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

    is_website_compliant = AMPChoiceRadioField(
        label="Initial website compliance decision",
        help_text="This field effects the case status",
        choices=IS_WEBSITE_COMPLIANT_CHOICES,
    )
    compliance_decision_notes = AMPTextField(label="Website compliance notes")

    class Meta:
        model = Case
        fields: List[str] = [
            "version",
            "is_website_compliant",
            "compliance_decision_notes",
        ]


class AuditStatement1UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 1 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    scope_state = AMPChoiceRadioField(
        label="Scope",
        choices=SCOPE_STATE_CHOICES,
    )
    scope_notes = AMPTextField(label="Notes")
    feedback_state = AMPChoiceRadioField(
        label="Feedback",
        choices=FEEDBACK_STATE_CHOICES,
    )
    feedback_notes = AMPTextField(label="Notes")
    contact_information_state = AMPChoiceRadioField(
        label="Contact Information",
        choices=CONTACT_INFORMATION_STATE_CHOICES,
    )
    contact_information_notes = AMPTextField(label="Notes")
    enforcement_procedure_state = AMPChoiceRadioField(
        label="Enforcement Procedure",
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
    )
    enforcement_procedure_notes = AMPTextField(label="Notes")
    declaration_state = AMPChoiceRadioField(
        label="Declaration",
        choices=DECLARATION_STATE_CHOICES,
    )
    declaration_notes = AMPTextField(label="Notes")

    compliance_state = AMPChoiceRadioField(
        label="Compliance Status",
        choices=COMPLIANCE_STATE_CHOICES,
    )
    compliance_notes = AMPTextField(label="Notes")
    non_regulation_state = AMPChoiceRadioField(
        label="Non-accessible Content - non compliance with regulations",
        choices=NON_REGULATION_STATE_CHOICES,
    )
    non_regulation_notes = AMPTextField(label="Notes")
    audit_statement_1_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "scope_state",
            "scope_notes",
            "feedback_state",
            "feedback_notes",
            "contact_information_state",
            "contact_information_notes",
            "enforcement_procedure_state",
            "enforcement_procedure_notes",
            "declaration_state",
            "declaration_notes",
            "compliance_state",
            "compliance_notes",
            "non_regulation_state",
            "non_regulation_notes",
            "audit_statement_1_complete_date",
        ]


class AuditStatement2UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 2 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    disproportionate_burden_state = AMPChoiceRadioField(
        label="Non-accessible Content - disproportionate burden",
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
    )
    disproportionate_burden_notes = AMPTextField(label="Notes")
    content_not_in_scope_state = AMPChoiceRadioField(
        label="Non-accessible Content - the content is not within the scope of the applicable legislation",
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
    )
    content_not_in_scope_notes = AMPTextField(label="Notes")
    preparation_date_state = AMPChoiceRadioField(
        label="Preparation Date",
        choices=PREPARATION_DATE_STATE_CHOICES,
    )
    preparation_date_notes = AMPTextField(label="Notes")
    review_state = AMPChoiceRadioField(
        label="Review",
        choices=REVIEW_STATE_CHOICES,
    )
    review_notes = AMPTextField(label="Notes")
    method_state = AMPChoiceRadioField(
        label="Method",
        choices=METHOD_STATE_CHOICES,
    )
    method_notes = AMPTextField(label="Notes")
    access_requirements_state = AMPChoiceRadioField(
        label="Access Requirements",
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
    )
    access_requirements_notes = AMPTextField(label="Notes")
    audit_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "disproportionate_burden_state",
            "disproportionate_burden_notes",
            "content_not_in_scope_state",
            "content_not_in_scope_notes",
            "preparation_date_state",
            "preparation_date_notes",
            "review_state",
            "review_notes",
            "method_state",
            "method_notes",
            "access_requirements_state",
            "access_requirements_notes",
            "audit_statement_2_complete_date",
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


class CaseStatementDecisionUpdateForm(VersionForm):
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


class AuditReportOptionsUpdateForm(VersionForm):
    """
    Form for editing report options
    """

    accessibility_statement_state = AMPChoiceRadioField(
        label="Accessibility statement",
        choices=ACCESSIBILITY_STATEMENT_STATE_CHOICES,
    )
    accessibility_statement_not_correct_format = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_not_correct_format"
                ]
            }
        ),
    )
    accessibility_statement_not_specific_enough = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_not_specific_enough"
                ]
            }
        ),
    )
    accessibility_statement_missing_accessibility_issues = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_missing_accessibility_issues"
                ]
            }
        ),
    )
    accessibility_statement_missing_mandatory_wording = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_missing_mandatory_wording"
                ]
            }
        ),
    )
    accessibility_statement_needs_more_re_disproportionate = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_needs_more_re_disproportionate"
                ]
            }
        ),
    )
    accessibility_statement_needs_more_re_accessibility = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_needs_more_re_accessibility"
                ]
            }
        ),
    )
    accessibility_statement_deadline_not_complete = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_deadline_not_complete"
                ]
            }
        ),
    )
    accessibility_statement_deadline_not_sufficient = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_deadline_not_sufficient"
                ]
            }
        ),
    )
    accessibility_statement_out_of_date = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_out_of_date"
                ]
            }
        ),
    )
    accessibility_statement_template_update = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_template_update"
                ]
            }
        ),
    )
    accessibility_statement_accessible = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_accessible"
                ]
            }
        ),
    )
    accessibility_statement_prominent = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_ACCESSIBILITY_ISSUE_TEXT[
                    "accessibility_statement_prominent"
                ]
            }
        ),
    )
    report_options_next = AMPChoiceRadioField(
        label="What to do next",
        choices=REPORT_OPTIONS_NEXT_CHOICES,
    )
    report_next_change_statement = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": REPORT_NEXT_ISSUE_TEXT["report_next_change_statement"]}
        ),
    )
    report_next_no_statement = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": REPORT_NEXT_ISSUE_TEXT["report_next_no_statement"]}
        ),
    )
    report_next_statement_not_right = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": REPORT_NEXT_ISSUE_TEXT["report_next_statement_not_right"]}
        ),
    )
    report_next_statement_matches = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": REPORT_NEXT_ISSUE_TEXT["report_next_statement_matches"]}
        ),
    )
    report_next_disproportionate_burden = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={
                "label": REPORT_NEXT_ISSUE_TEXT["report_next_disproportionate_burden"]
            }
        ),
    )
    audit_report_options_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_state",
            "accessibility_statement_not_correct_format",
            "accessibility_statement_not_specific_enough",
            "accessibility_statement_missing_accessibility_issues",
            "accessibility_statement_missing_mandatory_wording",
            "accessibility_statement_needs_more_re_disproportionate",
            "accessibility_statement_needs_more_re_accessibility",
            "accessibility_statement_deadline_not_complete",
            "accessibility_statement_deadline_not_sufficient",
            "accessibility_statement_out_of_date",
            "accessibility_statement_template_update",
            "accessibility_statement_accessible",
            "accessibility_statement_prominent",
            "report_options_next",
            "report_next_change_statement",
            "report_next_no_statement",
            "report_next_statement_not_right",
            "report_next_statement_matches",
            "report_next_disproportionate_burden",
            "audit_report_options_complete_date",
        ]


class AuditReportTextUpdateForm(VersionForm):
    """
    Form for editing report text
    """

    audit_report_text_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_report_text_complete_date",
        ]


class AuditRetestMetadataUpdateForm(VersionForm):
    """
    Form for editing audit retest metadata
    """

    retest_date = AMPDateField(label="Date of retest")
    audit_retest_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "retest_date",
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

    name = AMPCharFieldWide(label="")
    fixed = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Fixed"})
    )
    not_fixed = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Not fixed"})
    )
    not_retested = AMPChoiceCheckboxField(
        label="", widget=AMPChoiceCheckboxWidget(attrs={"label": "Not retested"})
    )

    class Meta:
        model = Page
        fields: List[str] = [
            "name",
            "fixed",
            "not_fixed",
            "not_retested",
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
        label="Final website compliance decision",
        choices=WEBSITE_STATE_FINAL_CHOICES,
    )
    website_state_notes_final = AMPTextField(
        label="Final website compliance decision notes",
    )

    class Meta:
        model = Case
        fields = [
            "version",
            "website_state_final",
            "website_state_notes_final",
        ]


class AuditRetestStatementUpdateView(VersionForm):
    """
    Form for retesting statement
    """

    audit_retest_statement_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_complete_date",
        ]


class AuditRetestStatementDecisionUpdateView(VersionForm):
    """
    Form for retesting statement swcision
    """

    audit_retest_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_retest_statement_decision_complete_date",
        ]
