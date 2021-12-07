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
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPModelChoiceField,
    AMPModelChoiceRadioField,
    AMPURLField,
)
from ..cases.models import BOOLEAN_CHOICES
from .models import (
    Audit,
    Page,
    CheckResult,
    SCREEN_SIZE_CHOICES,
    AUDIT_TYPE_CHOICES,
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
    OVERALL_COMPLIANCE_STATE_CHOICES,
    ACCESSIBILITY_STATEMENT_STATE_CHOICES,
    REPORT_OPTIONS_NEXT_CHOICES,
    REPORT_ACCESSIBILITY_ISSUE_TEXT,
    REPORT_NEXT_ISSUE_TEXT,
)


class AuditCreateForm(forms.ModelForm):
    """
    Form for creating an audit
    """

    name = AMPCharFieldWide(label="Name")
    type = AMPChoiceRadioField(
        label="Initital test or equality body retest?",
        choices=AUDIT_TYPE_CHOICES,
    )
    retest_of_audit = AMPModelChoiceRadioField(
        label="Which test are you retesting?",
        queryset=Audit.objects.none(),
        required=False,
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "name",
            "type",
            "retest_of_audit",
        ]


class AuditMetadataUpdateForm(VersionForm):
    """
    Form for editing check metadata
    """

    name = AMPCharFieldWide(label="Name")
    date_of_test = AMPDateField(label="Date of test")
    screen_size = AMPChoiceField(label="Screen size", choices=SCREEN_SIZE_CHOICES)
    audit_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "date_of_test",
            "name",
            "screen_size",
            "audit_metadata_complete_date",
        ]


class AuditWebsiteUpdateForm(VersionForm):
    """
    Form for editing website check page
    """

    audit_website_check_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_website_check_complete_date",
        ]


class AuditPageChecksUpdateForm(forms.Form):
    """
    Form for editing checks for a page
    """

    next_page = AMPModelChoiceField(
        label="", queryset=Page.objects.none(), empty_label=None
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "next_page",
        ]


class CheckResultUpdateForm(VersionForm):
    """
    Form for updating a single check test
    """

    failed = AMPChoiceCheckboxField(
        label="",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = CheckResult
        fields = [
            "version",
            "failed",
            "notes",
        ]


CheckResultUpdateFormset: Any = forms.modelformset_factory(
    CheckResult, CheckResultUpdateForm, extra=0
)


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
    overall_compliance_state = AMPChoiceRadioField(
        label="Overall Decision on Compliance of Accessibility Statement",
        choices=OVERALL_COMPLIANCE_STATE_CHOICES,
    )
    overall_compliance_notes = AMPTextField(label="Notes")
    audit_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
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
            "overall_compliance_state",
            "overall_compliance_notes",
            "audit_statement_2_complete_date",
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
