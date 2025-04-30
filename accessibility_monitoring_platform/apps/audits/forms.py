"""
Forms - checks (called tests by users)
"""

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

CHECK_RESULT_TYPE_FILTER_CHOICES: list[tuple[str, str]] = (
    WcagDefinition.Type.choices
    + [
        ("", "All"),
    ]
)
TEST_CHECK_RESULT_STATE_FILTER_CHOICES: list[tuple[str, str]] = (
    CheckResult.Result.choices + [("", "All")]
)
RETEST_CHECK_RESULT_STATE_FILTER_CHOICES: list[tuple[str, str]] = (
    CheckResult.RetestResult.choices + [("", "All")]
)
COPY_TICK_HELP_TEXT: str = """
<span class="amp-control amp-copy-text-to-clipboard" data-text-to-copy="✓" tabindex="0">Copy</span>
    the ✓ and paste next to the fixes the organisation has made"""


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
        fields: list[str] = [
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


AuditExtraPageFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=0
)
AuditExtraPageFormsetOneExtra: forms.formsets.BaseFormSet = forms.modelformset_factory(
    Page, AuditExtraPageUpdateForm, extra=1
)
AuditExtraPageFormsetTwoExtra: forms.formsets.BaseFormSet = forms.modelformset_factory(
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


AuditStandardPageFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
    Page, AuditStandardPageUpdateForm, extra=0
)


class AuditPagesUpdateForm(VersionForm):
    """
    Form for editing pages check page
    """

    audit_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
            "version",
            "audit_pages_complete_date",
        ]


class AuditPageChecksForm(forms.Form):
    """
    Form for editing checks for a page
    """

    complete_date = AMPDatePageCompleteField(
        label="Mark this page as complete",
        widget=AMPDateCheckboxWidget(attrs={"label": "Page complete"}),
    )
    no_errors_date = AMPDatePageCompleteField(
        label="Mark page as having no errors",
        widget=AMPDateCheckboxWidget(attrs={"label": "Web page has no errors"}),
    )

    class Meta:
        model = Audit
        fields: list[str] = [
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
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )
    state_filter = AMPChoiceRadioField(
        label="Test state",
        choices=TEST_CHECK_RESULT_STATE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )

    class Meta:
        model = Page
        fields: list[str] = [
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
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )
    notes = AMPTextField(label="Error details for report")

    class Meta:
        model = CheckResult
        fields = [
            "wcag_definition",
            "check_result_state",
            "notes",
        ]


CheckResultFormset: forms.formsets.BaseFormSet = forms.formset_factory(
    CheckResultForm, extra=0
)


class AuditWebsiteDecisionUpdateForm(VersionForm):
    """
    Form for editing website compliance decision completion
    """

    audit_website_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "website_compliance_state_initial",
            "website_compliance_notes_initial",
        ]


class AuditStatementDecisionUpdateForm(VersionForm):
    """
    Form for editing statement compliance decision completion
    """

    audit_statement_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
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


StatementCheckResultFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "audit_statement_custom_complete_date",
        ]


class InitialCustomIssueCreateUpdateForm(forms.ModelForm):
    """
    Form for creating or updating a custom issue StatementCheckResult
    """

    report_comment = AMPTextField(label="Comments for report")
    auditor_notes = AMPTextField(label="Notes for auditor")

    class Meta:
        model = StatementCheckResult
        fields = ["report_comment", "auditor_notes"]


class AuditRetestNew12WeekCustomIssueCreateForm(forms.ModelForm):
    """
    Form for creating a new 12-week custom issue StatementCheckResult
    """

    retest_comment = AMPTextField(label="Issue description for organisation")
    auditor_notes = AMPTextField(label="12-week internal notes")

    class Meta:
        model = StatementCheckResult
        fields = ["retest_comment", "auditor_notes"]


class New12WeekCustomStatementCheckResultUpdateForm(forms.ModelForm):
    """
    Form for updating a custom statement check result
    """

    retest_comment = AMPTextField(label="Issue description for organisation")
    auditor_notes = AMPTextField(label="12-week internal notes")
    retest_state = AMPChoiceRadioField(
        label="Mark this statement as resolved",
        choices=StatementCheckResult.Result.choices,
        widget=AMPRadioSelectWidget(),
    )

    class Meta:
        model = StatementCheckResult
        fields = ["retest_comment", "auditor_notes", "retest_state"]


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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "audit_statement_summary_complete_date",
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
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "audit_retest_pages_complete_date",
        ]


class AuditRetestPageUpdateForm(forms.ModelForm):
    """Form for updating a page at 12-week retest"""

    updated_url = AMPURLField(label="New URL (if applicable)")
    updated_location = AMPCharFieldWide(label="New page location (if applicable)")

    class Meta:
        model = Page
        fields = [
            "updated_url",
            "updated_location",
        ]


AuditRetestPageFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
    Page, AuditRetestPageUpdateForm, extra=0
)


class AuditRetestPageChecksForm(forms.Form):
    """
    Form for retesting checks for a page
    """

    retest_complete_date = AMPDatePageCompleteField(
        label="Mark this page as complete",
        widget=AMPDateCheckboxWidget(attrs={"label": "Page complete"}),
    )
    retest_page_missing_date = AMPDatePageCompleteField(
        label="Mark page as missing",
        widget=AMPDateCheckboxWidget(attrs={"label": "Page missing"}),
    )
    retest_notes = AMPTextField(label="Error details for correspondence")

    class Meta:
        model = Audit
        fields: list[str] = [
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
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )
    state_filter = AMPChoiceRadioField(
        label="Retest state",
        choices=RETEST_CHECK_RESULT_STATE_FILTER_CHOICES,
        initial="",
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )

    class Meta:
        model = Page
        fields: list[str] = [
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
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )
    retest_notes = AMPTextField(
        label="Error details for correspondence", help_text=COPY_TICK_HELP_TEXT
    )

    class Meta:
        model = CheckResult
        fields = [
            "id",
            "retest_state",
            "retest_notes",
        ]


AuditRetestCheckResultFormset: forms.formsets.BaseFormSet = forms.formset_factory(
    AuditRetestCheckResultForm, extra=0
)


class AuditRetestWebsiteDecisionUpdateForm(VersionForm):
    """
    Form for retest website compliance decision completion
    """

    audit_retest_website_decision_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
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


class AuditRetestWcagSummaryUpdateForm(VersionForm):
    """
    Form for editing 12-week WCAG test audit summary
    """

    audit_retest_wcag_summary_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
            "version",
            "audit_retest_wcag_summary_complete_date",
        ]


class AuditRetestStatementSummaryUpdateForm(VersionForm):
    """
    Form for editing 12-week statement audit summary
    """

    audit_retest_statement_summary_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
            "version",
            "audit_retest_statement_summary_complete_date",
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
    retest_comment = AMPTextField(label="12-week internal notes")

    class Meta:
        model = StatementCheckResult
        fields = [
            "retest_state",
            "retest_comment",
        ]


AuditRetestStatementCheckResultFormset: forms.formsets.BaseFormSet = (
    forms.modelformset_factory(
        StatementCheckResult, AuditRetestStatementCheckResultForm, extra=0
    )
)


class AuditRetestStatementOverviewUpdateForm(VersionForm):
    """
    Form for editing statement overview
    """

    audit_retest_statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "audit_retest_statement_custom_complete_date",
        ]


class AuditRetestStatementInitialCustomIssueUpdateForm(forms.ModelForm):
    """
    Form for updating an initial statement custom issue
    """

    retest_state = AMPChoiceRadioField(
        label="Mark this statement issue as resolved",
        choices=StatementCheckResult.Result.choices,
        widget=AMPRadioSelectWidget(),
    )
    retest_comment = AMPTextField(label="Comments for email")

    class Meta:
        model = StatementCheckResult
        fields = [
            "retest_state",
            "retest_comment",
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
        fields: list[str] = [
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
        model = Audit
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        widget=AMPRadioSelectWidget(
            attrs={
                "horizontal": True,
                "small": True,
            }
        ),
    )
    retest_notes = AMPTextField(label="Notes")

    class Meta:
        model = RetestCheckResult
        fields = [
            "id",
            "retest_state",
            "retest_notes",
        ]


RetestCheckResultFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
    RetestCheckResult, form=RetestCheckResultForm, extra=0
)


class RetestComparisonUpdateForm(forms.ModelForm):
    """
    Form for updating equality body retest comparison complete
    """

    comparison_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: list[str] = [
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
        fields: list[str] = [
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


StatementPageFormset: forms.formsets.BaseFormSet = forms.modelformset_factory(
    StatementPage, StatementPageUpdateForm, extra=0
)
StatementPageFormsetOneExtra: forms.formsets.BaseFormSet = forms.modelformset_factory(
    StatementPage, StatementPageUpdateForm, extra=1
)


class AuditStatementPagesUpdateForm(VersionForm):
    """
    Form for statement pages update at initial test
    """

    audit_statement_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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


RetestStatementCheckResultFormset: forms.formsets.BaseFormSet = (
    forms.modelformset_factory(
        RetestStatementCheckResult, RetestStatementCheckResultForm, extra=0
    )
)


class RetestStatementOverviewUpdateForm(VersionForm):
    """
    Form for editing retest statement overview
    """

    statement_overview_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
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


RetestStatementCustomCheckResultFormset: forms.formsets.BaseFormSet = (
    forms.modelformset_factory(
        RetestStatementCheckResult, RetestStatementCustomCheckResultForm, extra=0
    )
)
RetestStatementCustomCheckResultFormsetOneExtra: forms.formsets.BaseFormSet = (
    forms.modelformset_factory(
        RetestStatementCheckResult, RetestStatementCustomCheckResultForm, extra=1
    )
)


class RetestStatementResultsUpdateForm(VersionForm):
    """
    Form for completion of page showing results of statement content checks
    """

    statement_results_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Retest
        fields: list[str] = [
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
        fields: list[str] = [
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
        fields: list[str] = [
            "version",
            "statement_compliance_state",
            "statement_compliance_notes",
            "statement_decision_complete_date",
        ]
