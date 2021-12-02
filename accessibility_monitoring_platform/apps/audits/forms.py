"""
Forms - checks (called tests by users)
"""
from typing import Any, Dict, List

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
    ACCESSIBILITY_STATEMENT_STATE_CHOICES,
    REPORT_OPTIONS_NEXT_CHOICES,
    REPORT_ACCESSIBILITY_ISSUE_TEXT,
    REPORT_NEXT_ISSUE_TEXT,
)

ACCESSIBILITY_STATEMENT_EXAMPLES: Dict[str, str] = {
    "declaration_state": "[Name of organisation] is committed to making its website accessible,"
    " in accordance with the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations"
    " 2018.",
    "scope_state": """This accessibility statement applies to [insert scope of statement,"""
    """ e.g. website(s)/mobile application(s) to which the statement applies, as appropriate].

NOTE: For mobile applications, please include version information and date.""",
    "compliance_state": """One of the following

• This website is fully compliant with the Web Content Accessibility Guidelines version 2.1 AA standard.

• This website is partially compliant with the Web Content Accessibility Guidelines version 2.1 AA standard,"""
    """ due to the non-compliances listed below.

• This website is not compliant with the Web Content Accessibility Guidelines version 2.1 AA standard."""
    """ The non-accessible sections are listed below.""",
    "non_regulation_state": """[List the non-compliance(s) of the website(s)/mobile application(s), and/or,"""
    """ describe which section(s)/content/function(s) are not yet compliant].

NOTE: Describe in non-technical terms, as far as possible, how the content is not accessible, including reference(s)"""
    """ to the applicable requirements in the relevant standards and/or technical specifications that are not met;"""
    """ e.g.: ‘The login form of the document sharing application is not fully usable by keyboard (requirement number"""
    """ XXX (if applicable))’""",
    "disproportionate_burden_state": "[List non-accessible section(s)/content/function(s) for which the"
    " disproportionate burden exemption, is being temporarily invoked] and which WCAG success criteria the problem"
    " fails on",
    "content_not_in_scope_state": "List non-accessible section(s)/content/function(s) which is/are out of scope"
    " of the applicable legislation]. Which WCAG success criteria the problem falls on."
    "[Indicate accessible alternatives, where appropriate].",
    "preparation_date_state": """This statement was prepared on [date].""",
    "method_state": """[Indicate the method used to prepare the statement]
You should link to a full explanation of what you tested and how you chose it. If you get a third party auditor"""
    """ to test your website for you, they should include sampling details in the test report - so you can just link"""
    """ to that.""",
    "review_state": """[The statement was last reviewed on [insert date of latest review]. At least once per year.""",
    "feedback_state": "[Provide a description of, and a link to, the feedback mechanism to be used to notify the public"
    " sector body of any compliance failures and to request information and content excluded from the scope of the"
    " Directive].",
    "contact_information_state": "[Provide the contact information of the relevant entity(ies)/unit(s)/person(s)"
    " (as appropriate) responsible for accessibility and for processing requests sent through the feedback mechanism].",
    "enforcement_procedure_state": """The Equality and Human Rights Commission (EHRC) is responsible for enforcing"""
    """ the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018 (the"""
    """ ‘accessibility regulations’). If you’re not happy with how we respond to your complaint, contact the Equality"""
    """ Advisory and Support Service (EASS).

[Note: if your organisation is based in Northern Ireland, refer users who want to complain to the Equalities"""
    """ Commission for Northern Ireland (ECNI) instead of the EASS and EHRC.]""",
    "access_requirements_state": """The accessibility statement should be easy to find for the user.

A link to the accessibility statement should be prominently placed on the homepage of the website or made available"""
    """ on every web page, for example in a static header or footer.

A standardised URL may be used for the accessibility statement.""",
}


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


class AuditMetadataUpdateForm(AuditCreateForm, VersionForm):
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


class AuditStandardPageUpdateForm(forms.ModelForm):
    """
    Form for updating a standard page (one of the 5 types of page in every audit)
    """

    url = AMPURLField(label="URL")
    not_found = AMPChoiceCheckboxField(
        label="Not found?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )

    class Meta:
        model = Page
        fields = [
            "url",
            "not_found",
        ]


AuditStandardPageFormset: Any = forms.modelformset_factory(
    Page, AuditStandardPageUpdateForm, extra=0
)


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


class AuditPagesUpdateForm(VersionForm):
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


class AuditManualUpdateForm(forms.Form):
    """
    Form for editing manual checks for a page
    """

    next_page = AMPModelChoiceField(
        label="", queryset=Page.objects.none(), empty_label=None
    )
    page_manual_checks_complete_date = AMPDatePageCompleteField()
    audit_manual_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "next_page",
            "page_manual_checks_complete_date",
            "audit_manual_complete_date",
        ]


class AuditAxeUpdateForm(forms.Form):
    """
    Form for editing axe checks for a page
    """

    next_page = AMPModelChoiceField(
        label="", queryset=Page.objects.none(), empty_label=None
    )
    page_axe_checks_complete_date = AMPDatePageCompleteField()
    audit_axe_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Audit
        fields: List[str] = [
            "next_page",
            "page_axe_checks_complete_date",
            "audit_axe_complete_date",
        ]


class AuditPdfUpdateForm(VersionForm):
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
        label="",
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


class AuditStatement1UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 1 checks
    """

    accessibility_statement_backup_url = AMPURLField(
        label="Link to saved accessibility statement",
    )
    declaration_state = AMPChoiceRadioField(
        label="Declaration",
        choices=DECLARATION_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["declaration_state"],
    )
    declaration_notes = AMPTextField(label="Notes")
    scope_state = AMPChoiceRadioField(
        label="Scope",
        choices=SCOPE_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["scope_state"],
    )
    scope_notes = AMPTextField(label="Notes")
    compliance_state = AMPChoiceRadioField(
        label="Compliance Status",
        choices=COMPLIANCE_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["compliance_state"],
    )
    compliance_notes = AMPTextField(label="Notes")
    non_regulation_state = AMPChoiceRadioField(
        label="Non-accessible Content - non compliance with regulations",
        choices=NON_REGULATION_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["non_regulation_state"],
    )
    non_regulation_notes = AMPTextField(label="Notes")
    disproportionate_burden_state = AMPChoiceRadioField(
        label="Non-accessible Content - disproportionate burden",
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["disproportionate_burden_state"],
    )
    disproportionate_burden_notes = AMPTextField(label="Notes")
    content_not_in_scope_state = AMPChoiceRadioField(
        label="Non-accessible Content - the content is not within the scope of the applicable legislation",
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["content_not_in_scope_state"],
    )
    content_not_in_scope_notes = AMPTextField(label="Notes")
    preparation_date_state = AMPChoiceRadioField(
        label="Preparation Date",
        choices=PREPARATION_DATE_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["preparation_date_state"],
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


class AuditStatement2UpdateForm(VersionForm):
    """
    Form for editing accessibility statement 2 checks
    """

    method_state = AMPChoiceRadioField(
        label="Method",
        choices=METHOD_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["method_state"],
    )
    method_notes = AMPTextField(label="Notes")
    review_state = AMPChoiceRadioField(
        label="Review",
        choices=REVIEW_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["review_state"],
    )
    review_notes = AMPTextField(label="Notes")
    feedback_state = AMPChoiceRadioField(
        label="Feedback",
        choices=FEEDBACK_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["feedback_state"],
    )
    feedback_notes = AMPTextField(label="Notes")
    contact_information_state = AMPChoiceRadioField(
        label="Contact Information",
        choices=CONTACT_INFORMATION_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["contact_information_state"],
    )
    contact_information_notes = AMPTextField(label="Notes")
    enforcement_procedure_state = AMPChoiceRadioField(
        label="Enforcement Procedure",
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["enforcement_procedure_state"],
    )
    enforcement_procedure_notes = AMPTextField(label="Notes")
    access_requirements_state = AMPChoiceRadioField(
        label="Access Requirements",
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
        help_text=ACCESSIBILITY_STATEMENT_EXAMPLES["access_requirements_state"],
    )
    access_requirements_notes = AMPTextField(label="Notes")
    overall_compliance_state = AMPChoiceRadioField(
        label="Overall Decision on Compliance",
        choices=OVERALL_COMPLIANCE_STATE_CHOICES,
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
