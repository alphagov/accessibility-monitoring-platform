"""
Forms - checks (called tests by users)
"""
from typing import Any, List

from django import forms
from django.core.exceptions import ValidationError

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPDateCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPModelChoiceField,
    AMPURLField,
)
from ..cases.models import BOOLEAN_CHOICES
from .models import (
    Audit,
    Page,
    CheckResult,
    WcagDefinition,
    SCREEN_SIZE_CHOICES,
    EXEMPTION_CHOICES,
    AUDIT_TYPE_CHOICES,
    TEST_TYPE_AXE,
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
)


class AuditCreateForm(forms.ModelForm):
    """
    Form for creating an audit
    """

    date_of_test = AMPDateField(label="Date of test")
    description = AMPCharFieldWide(label="Test description")
    screen_size = AMPChoiceField(label="Screen size", choices=SCREEN_SIZE_CHOICES)
    is_exemption = AMPChoiceRadioField(label="Exemptions?", choices=EXEMPTION_CHOICES)
    notes = AMPTextField(label="Notes")
    type = AMPChoiceRadioField(
        label="Initital test or equality body retest?", choices=AUDIT_TYPE_CHOICES
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "date_of_test",
            "description",
            "screen_size",
            "is_exemption",
            "notes",
            "type",
        ]


class AuditUpdateMetadataForm(AuditCreateForm, VersionForm):
    """
    Form for editing check metadata
    """

    audit_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "date_of_test",
            "description",
            "screen_size",
            "is_exemption",
            "notes",
            "type",
            "audit_metadata_complete_date",
        ]


class AuditExtraPageUpdateForm(forms.ModelForm):
    """
    Form for updating an extra page
    """

    name = AMPCharFieldWide(label="Page name")
    url = AMPURLField(label="URL")

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
        ]


class AuditStandardPageUpdateForm(AuditExtraPageUpdateForm):
    """
    Form for updating a standard page (one of the 5 types of page in every check)
    """

    not_found = AMPChoiceCheckboxField(
        label="Not found?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
            "not_found",
        ]


AuditStandardPageFormset: Any = forms.modelformset_factory(
    Page, AuditStandardPageUpdateForm, extra=0
)
AuditExtraPageFormset: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=0
)
AuditExtraPageFormsetOneExtra: Any = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=1
)


class AuditUpdatePagesForm(VersionForm):
    """
    Form for editing check pages page
    """

    audit_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_pages_complete_date",
        ]


class AuditUpdateByPageManualForm(forms.Form):
    """
    Form for editing manual checks for a page
    """

    next_page = AMPModelChoiceField(
        label="", queryset=Page.objects.none(), empty_label=None
    )
    page_manual_checks_complete_date = AMPDatePageCompleteField()
    audit_manual_complete_date = AMPDatePageCompleteField(
        widget=AMPDateCheckboxWidget(attrs={"label": "Manual tests completed?"}),
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "next_page",
            "page_manual_checks_complete_date",
            "audit_manual_complete_date",
        ]


class AuditUpdateByPageAxeForm(forms.Form):
    """
    Form for editing axe checks for a page
    """

    next_page = AMPModelChoiceField(
        label="", queryset=Page.objects.none(), empty_label=None
    )
    page_axe_checks_complete_date = AMPDatePageCompleteField()
    audit_axe_complete_date = AMPDatePageCompleteField(
        widget=AMPDateCheckboxWidget(attrs={"label": "Axe tests completed?"}),
    )

    class Meta:
        model = Audit
        fields: List[str] = [
            "next_page",
            "page_axe_checks_complete_date",
            "audit_axe_complete_date",
        ]


class AuditUpdatePdfForm(VersionForm):
    """
    Form for editing pdf checks
    """

    audit_pdf_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_pdf_complete_date",
        ]


class CheckResultUpdateForm(VersionForm):
    """
    Form for updating a single check test
    """

    failed = AMPChoiceCheckboxField(
        label="Failed?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )
    notes = AMPTextField(label="Violation details")

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


class CheckResultForm(forms.ModelForm):
    """
    Form for updating a check result
    """

    failed = AMPChoiceCheckboxField(
        label="Failed?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = CheckResult
        fields: List[str] = [
            "failed",
            "notes",
        ]


class PageWithFailureForm(forms.Form):
    """
    Form recording that a failure is on a specific page
    """

    page = forms.CharField(widget=forms.HiddenInput())
    page_id = forms.CharField(widget=forms.HiddenInput())
    failure_found = AMPChoiceCheckboxField(
        label="Failed?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )

    class Meta:
        fields = [
            "page",
            "failure_found",
        ]


PageWithFailureFormset: Any = forms.formset_factory(PageWithFailureForm, extra=0)


class AxeCheckResultUpdateForm(forms.ModelForm):
    """
    Form for updating a single axe check result
    """

    wcag_definition = AMPModelChoiceField(
        label="Violation", queryset=WcagDefinition.objects.filter(type=TEST_TYPE_AXE)
    )
    notes = AMPTextField(label="Violation notes")

    class Meta:
        model = CheckResult
        fields = [
            "wcag_definition",
            "notes",
        ]

    def clean_wcag_definition(self):
        wcag_definition = self.cleaned_data.get("wcag_definition")
        if not wcag_definition:
            raise ValidationError("Please choose a violation.")
        return wcag_definition


AxeCheckResultUpdateFormset: Any = forms.modelformset_factory(
    CheckResult, AxeCheckResultUpdateForm, extra=1
)


class AuditUpdateStatement1Form(VersionForm):
    """
    Form for editing accessibility statement 1 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement"
    )
    declaration_state = AMPChoiceRadioField(
        label="Declaration", choices=DECLARATION_STATE_CHOICES
    )
    declaration_notes = AMPTextField(label="Notes")
    scope_state = AMPChoiceRadioField(label="Scope", choices=SCOPE_STATE_CHOICES)
    scope_notes = AMPTextField(label="Notes")
    compliance_state = AMPChoiceRadioField(
        label="Compliance Status", choices=COMPLIANCE_STATE_CHOICES
    )
    compliance_notes = AMPTextField(label="Notes")
    non_regulation_state = AMPChoiceRadioField(
        label="Non-accessible Content - non compliance with regulations",
        choices=NON_REGULATION_STATE_CHOICES,
    )
    non_regulation_notes = AMPTextField(label="Notes")
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
    audit_statement_1_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "accessibility_statement_backup_url",
            "declaration_state",
            "declaration_notes",
            "scope_state",
            "scope_notes",
            "compliance_state",
            "compliance_notes",
            "non_regulation_state",
            "non_regulation_notes",
            "disproportionate_burden_state",
            "disproportionate_burden_notes",
            "content_not_in_scope_state",
            "content_not_in_scope_notes",
            "preparation_date_state",
            "preparation_date_notes",
            "audit_statement_1_complete_date",
        ]


class AuditUpdateStatement2Form(VersionForm):
    """
    Form for editing accessibility statement 2 checks
    """

    method_state = AMPChoiceRadioField(
        label="Method",
        choices=METHOD_STATE_CHOICES,
    )
    method_notes = AMPTextField(label="Notes")
    review_state = AMPChoiceRadioField(label="Review", choices=REVIEW_STATE_CHOICES)
    review_notes = AMPTextField(label="Notes")
    feedback_state = AMPChoiceRadioField(
        label="Feedback", choices=FEEDBACK_STATE_CHOICES
    )
    feedback_notes = AMPTextField(label="Notes")
    contact_information_state = AMPChoiceRadioField(
        label="Contact Information", choices=CONTACT_INFORMATION_STATE_CHOICES
    )
    contact_information_notes = AMPTextField(label="Notes")
    enforcement_procedure_state = AMPChoiceRadioField(
        label="Contact Information", choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES
    )
    enforcement_procedure_notes = AMPTextField(label="Notes")
    access_requirements_state = AMPChoiceRadioField(
        label="Access Requirements", choices=ACCESS_REQUIREMENTS_STATE_CHOICES
    )
    access_requirements_notes = AMPTextField(label="Notes")
    overall_compliance_state = AMPChoiceRadioField(
        label="Overall Decision on Compliance", choices=OVERALL_COMPLIANCE_STATE_CHOICES
    )
    overall_compliance_notes = AMPTextField(label="Notes")
    audit_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "method_state",
            "method_notes",
            "review_state",
            "review_notes",
            "feedback_state",
            "feedback_notes",
            "contact_information_state",
            "contact_information_notes",
            "enforcement_procedure_state",
            "enforcement_procedure_notes",
            "access_requirements_state",
            "access_requirements_notes",
            "overall_compliance_state",
            "overall_compliance_notes",
            "audit_statement_2_complete_date",
        ]


class AuditUpdateSummaryForm(VersionForm):
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
