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


AxeCheckResultUpdateFormset: Any = forms.modelformset_factory(
    CheckResult, AxeCheckResultUpdateForm, extra=1
)


class AuditUpdateStatement1Form(VersionForm):
    """
    Form for editing accessibility statement 1 checks
    """

    audit_statement_1_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_statement_1_complete_date",
        ]


class AuditUpdateStatement2Form(VersionForm):
    """
    Form for editing accessibility statement 2 checks
    """

    audit_statement_2_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "version",
            "audit_statement_2_complete_date",
        ]
