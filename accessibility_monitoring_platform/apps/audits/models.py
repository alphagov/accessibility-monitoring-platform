"""
Models - audits (called tests by the users)
"""
from datetime import date
from typing import Dict, List, Tuple

from django.db import models
from django.db.models import Case as DjangoCase
from django.db.models import Q, When
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.models import Boolean, StartEndDateManager, VersionModel
from ..common.utils import amp_format_date

PAGE_TYPE_EXTRA: str = "extra"
PAGE_TYPE_HOME: str = "home"
PAGE_TYPE_CONTACT: str = "contact"
PAGE_TYPE_STATEMENT: str = "statement"
PAGE_TYPE_PDF: str = "pdf"
PAGE_TYPE_FORM: str = "form"
PAGE_TYPE_CORONAVIRUS: str = "coronavirus"
PAGE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (PAGE_TYPE_EXTRA, "Additional"),
    (PAGE_TYPE_HOME, "Home"),
    (PAGE_TYPE_CONTACT, "Contact"),
    (PAGE_TYPE_STATEMENT, "Accessibility statement"),
    (PAGE_TYPE_CORONAVIRUS, "Coronavirus"),
    (PAGE_TYPE_PDF, "PDF"),
    (PAGE_TYPE_FORM, "Form"),
]
MANDATORY_PAGE_TYPES: List[str] = [
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
]
TEST_TYPE_MANUAL: str = "manual"
TEST_TYPE_AXE: str = "axe"
TEST_TYPE_PDF: str = "pdf"
TEST_TYPE_CHOICES: List[Tuple[str, str]] = [
    (TEST_TYPE_MANUAL, "Manual"),
    (TEST_TYPE_AXE, "Axe"),
    (TEST_TYPE_PDF, "PDF"),
]
FEEDBACK_STATE_DEFAULT: str = "not-present"
FEEDBACK_STATE_VALID: str = "present"
FEEDBACK_STATE_CHOICES: List[Tuple[str, str]] = [
    (FEEDBACK_STATE_VALID, "Present"),
    ("incomplete", "Present but missing detail"),
    (FEEDBACK_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
CONTACT_INFORMATION_STATE_DEFAULT: str = "not-present"
CONTACT_INFORMATION_VALID: str = "present"
CONTACT_INFORMATION_STATE_CHOICES: List[Tuple[str, str]] = [
    (CONTACT_INFORMATION_VALID, "Present"),
    ("incomplete", "Present but missing detail"),
    (CONTACT_INFORMATION_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
ENFORCEMENT_PROCEDURE_STATE_DEFAULT: str = "not-present"
ENFORCEMENT_PROCEDURE_VALID: str = "present"
ENFORCEMENT_PROCEDURE_STATE_CHOICES: List[Tuple[str, str]] = [
    (ENFORCEMENT_PROCEDURE_VALID, "Present"),
    (ENFORCEMENT_PROCEDURE_STATE_DEFAULT, "Not included"),
    ("other", "Other (Please specify)"),
]
COMPLIANCE_STATE_DEFAULT: str = "not-present"
COMPLIANCE_STATE_VALID: str = "present"
COMPLIANCE_STATE_CHOICES: List[Tuple[str, str]] = [
    (COMPLIANCE_STATE_VALID, "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (COMPLIANCE_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
NON_REGULATION_STATE_DEFAULT: str = "not-present"
NON_REGULATION_VALID: str = "present"
NON_REGULATION_STATE_CHOICES: List[Tuple[str, str]] = [
    (NON_REGULATION_VALID, "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (NON_REGULATION_STATE_DEFAULT, "Not present"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
DISPROPORTIONATE_BURDEN_STATE_NO_CLAIM: str = "no-claim"
DISPROPORTIONATE_BURDEN_STATE_ASSESSMENT: str = "assessment"
DISPROPORTIONATE_BURDEN_STATE_CHOICES: List[Tuple[str, str]] = [
    (DISPROPORTIONATE_BURDEN_STATE_NO_CLAIM, "No claim"),
    (DISPROPORTIONATE_BURDEN_STATE_ASSESSMENT, "Claim with assessment"),
    ("no-assessment", "Claim with no assessment"),
]
CONTENT_NOT_IN_SCOPE_STATE_DEFAULT: str = "not-present"
CONTENT_NOT_IN_SCOPE_VALID: str = "present"
CONTENT_NOT_IN_SCOPE_STATE_CHOICES: List[Tuple[str, str]] = [
    (CONTENT_NOT_IN_SCOPE_VALID, "Present and correct"),
    ("incorrect", "Present but incorrect"),
    (CONTENT_NOT_IN_SCOPE_STATE_DEFAULT, "Not present"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
PREPARATION_DATE_STATE_DEFAULT: str = "not-present"
PREPARATION_DATE_VALID: str = "present"
PREPARATION_DATE_STATE_CHOICES: List[Tuple[str, str]] = [
    (PREPARATION_DATE_VALID, "Present"),
    (PREPARATION_DATE_STATE_DEFAULT, "Not included"),
    ("other", "Other (Please specify)"),
]
REVIEW_STATE_DEFAULT: str = "not-present"
REVIEW_STATE_VALID: str = "present"
REVIEW_STATE_CHOICES: List[Tuple[str, str]] = [
    (REVIEW_STATE_VALID, "Present and correct"),
    ("out-of-date", "Present but out of date"),
    (REVIEW_STATE_DEFAULT, "Not included"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
METHOD_STATE_DEFAULT: str = "not-present"
METHOD_STATE_VALID: str = "present"
METHOD_STATE_CHOICES: List[Tuple[str, str]] = [
    (METHOD_STATE_VALID, "Present"),
    ("incomplete", "Present but missing detail"),
    (METHOD_STATE_DEFAULT, "Not present"),
    ("other", "Other (Please specify)"),
]
ACCESS_REQUIREMENTS_STATE_DEFAULT: str = "req-not-met"
ACCESS_REQUIREMENTS_VALID: str = "req-met"
ACCESS_REQUIREMENTS_STATE_CHOICES: List[Tuple[str, str]] = [
    (ACCESS_REQUIREMENTS_VALID, "Meets requirements"),
    (ACCESS_REQUIREMENTS_STATE_DEFAULT, "Does not meet requirements"),
    ("n/a", "N/A"),
    ("other", "Other (Please specify)"),
]
ARCHIVE_ACCESSIBILITY_STATEMENT_STATE_DEFAULT: str = "not-found"
ARCHIVE_ACCESSIBILITY_STATEMENT_STATE_CHOICES: List[Tuple[str, str]] = [
    (
        ARCHIVE_ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
        "An accessibility statement for the website was not found.",
    ),
    (
        "found",
        "An accessibility statement for the website was found in the correct format.",
    ),
    ("found-but", "An accessibility statement for the website was found but:"),
]
REPORT_OPTIONS_NEXT_DEFAULT: str = "errors"
REPORT_OPTIONS_NEXT_CHOICES: List[Tuple[str, str]] = [
    (REPORT_OPTIONS_NEXT_DEFAULT, "Errors were found"),
    ("no-errors", "No serious errors were found"),
]

CHECK_RESULT_NOT_TESTED: str = "not-tested"
CHECK_RESULT_ERROR: str = "error"
CHECK_RESULT_NO_ERROR: str = "no-error"
CHECK_RESULT_STATE_CHOICES: List[Tuple[str, str]] = [
    (CHECK_RESULT_ERROR, "Error found"),
    (CHECK_RESULT_NO_ERROR, "No issue"),
    (CHECK_RESULT_NOT_TESTED, "Not tested"),
]
RETEST_CHECK_RESULT_DEFAULT: str = "not-retested"
RETEST_CHECK_RESULT_FIXED: str = "fixed"
RETEST_CHECK_RESULT_NOT_FIXED: str = "not-fixed"
RETEST_CHECK_RESULT_STATE_CHOICES: List[Tuple[str, str]] = [
    (RETEST_CHECK_RESULT_FIXED, "Fixed"),
    (RETEST_CHECK_RESULT_NOT_FIXED, "Not fixed"),
    (RETEST_CHECK_RESULT_DEFAULT, "Not retested"),
]

ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT: Dict[str, str] = {
    "archive_accessibility_statement_not_correct_format": "it was not in the correct format",
    "archive_accessibility_statement_not_specific_enough": "it was not specific enough",
    "archive_accessibility_statement_missing_accessibility_issues": "accessibility issues were found during the test that"
    " were not included in the statement",
    "archive_accessibility_statement_missing_mandatory_wording": "mandatory wording is missing",
    "archive_accessibility_statement_needs_more_re_disproportionate": "we require more information covering the"
    " disproportionate burden claim",
    "archive_accessibility_statement_needs_more_re_accessibility": "it required more information detailing the accessibility"
    " issues",
    "archive_accessibility_statement_deadline_not_complete": "it includes a deadline of XXX for fixing XXX issues and this"
    " has not been completed",
    "archive_accessibility_statement_deadline_not_sufficient": "it includes a deadline of XXX for fixing XXX issues and"
    " this is not sufficient",
    "archive_accessibility_statement_out_of_date": "it is out of date and needs to be reviewed",
    "archive_accessibility_statement_eass_link": "it must link directly to the Equality Advisory and"
    " Support Service (EASS) website",
    "archive_accessibility_statement_template_update": "it is a requirement that accessibility statements are accessible."
    " Some users may experience difficulties using PDF documents. It may be beneficial for users if there was a HTML"
    " version of your full accessibility statement.",
    "archive_accessibility_statement_accessible": "in 2020 the GOV.UK sample template was updated to include an extra"
    " mandatory piece of information to outline the scope of your accessibility statement. This needs to be added to"
    " your statement.",
    "archive_accessibility_statement_prominent": "your statement should be prominently placed on the homepage of the website"
    " or made available on every web page, for example in a static header or footer, as per the legislative"
    " requirement.",
}
ARCHIVE_REPORT_NEXT_ISSUE_TEXT: Dict[str, str] = {
    "archive_report_next_change_statement": "They have an acceptable statement but need to change it because of the"
    " errors we found",
    "archive_report_next_no_statement": "They don’t have a statement, or it is in the wrong format",
    "archive_report_next_statement_not_right": "They have a statement but it is not quite right",
    "archive_report_next_statement_matches": "Their statement matches",
    "archive_report_next_disproportionate_burden": "Disproportionate burden",
}
ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_PREFIXES: List[str] = [
    "scope",
    "feedback",
    "contact_information",
    "enforcement_procedure",
    "declaration",
    "compliance",
    "non_regulation",
    "disproportionate_burden",
    "content_not_in_scope",
    "preparation_date",
    "review",
    "method",
    "access_requirements",
]
ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_VALID_VALUES: Dict[str, str] = {
    "scope": ["present"],
    "feedback": [FEEDBACK_STATE_VALID],
    "contact_information": [CONTACT_INFORMATION_VALID],
    "enforcement_procedure": [ENFORCEMENT_PROCEDURE_VALID],
    "declaration": ["present"],
    "compliance": [COMPLIANCE_STATE_VALID],
    "non_regulation": [NON_REGULATION_VALID],
    "disproportionate_burden": [
        DISPROPORTIONATE_BURDEN_STATE_NO_CLAIM,
        DISPROPORTIONATE_BURDEN_STATE_ASSESSMENT,
    ],
    "content_not_in_scope": [CONTENT_NOT_IN_SCOPE_VALID],
    "preparation_date": [PREPARATION_DATE_VALID],
    "review": [REVIEW_STATE_VALID],
    "method": [METHOD_STATE_VALID],
    "access_requirements": [ACCESS_REQUIREMENTS_VALID],
}

STATEMENT_CHECK_TYPE_OVERVIEW: str = "overview"
STATEMENT_CHECK_TYPE_WEBSITE: str = "website"
STATEMENT_CHECK_TYPE_COMPLIANCE: str = "compliance"
STATEMENT_CHECK_TYPE_NON_ACCESSIBLE: str = "non-accessible"
STATEMENT_CHECK_TYPE_PREPARATION: str = "preparation"
STATEMENT_CHECK_TYPE_FEEDBACK: str = "feedback"
STATEMENT_CHECK_TYPE_CUSTOM: str = "custom"
STATEMENT_CHECK_TYPE_CHOICES: List[Tuple[str, str]] = [
    (STATEMENT_CHECK_TYPE_OVERVIEW, "Statement overview"),
    (STATEMENT_CHECK_TYPE_WEBSITE, "Statement information"),
    (STATEMENT_CHECK_TYPE_COMPLIANCE, "Compliance status"),
    (STATEMENT_CHECK_TYPE_NON_ACCESSIBLE, "Non-accessible content"),
    (STATEMENT_CHECK_TYPE_PREPARATION, "Statement preparation"),
    (STATEMENT_CHECK_TYPE_FEEDBACK, "Feedback and enforcement procedure"),
    (STATEMENT_CHECK_TYPE_CUSTOM, "Custom statement issues"),
]
STATEMENT_CHECK_YES: str = "yes"
STATEMENT_CHECK_NO: str = "no"
STATEMENT_CHECK_NOT_TESTED: str = "not-tested"
STATEMENT_CHECK_CHOICES: List[Tuple[str, str]] = [
    (STATEMENT_CHECK_YES, "Yes"),
    (STATEMENT_CHECK_NO, "No"),
    (STATEMENT_CHECK_NOT_TESTED, "Not tested"),
]
RETEST_INITIAL_COMPLIANCE_DEFAULT: str = "not-known"
RETEST_INITIAL_COMPLIANCE_COMPLIANT: str = "compliant"
RETEST_INITIAL_COMPLIANCE_CHOICES: List[Tuple[str, str]] = [
    (RETEST_INITIAL_COMPLIANCE_COMPLIANT, "Compliant"),
    ("partially-compliant", "Partially compliant"),
    (RETEST_INITIAL_COMPLIANCE_DEFAULT, "Not known"),
]
ADDED_STAGE_INITIAL: str = "initial"
ADDED_STAGE_TWELVE_WEEK: str = "12-week-retest"
ADDED_STAGE_RETEST: str = "retest"
ADDED_STAGE_CHOICES: List[Tuple[str, str]] = [
    (ADDED_STAGE_INITIAL, "Initial"),
    (ADDED_STAGE_TWELVE_WEEK, "12-week retest"),
    (ADDED_STAGE_RETEST, "Equality body retest"),
]


class ArchiveAccessibilityStatementCheck:
    """Accessibility statement check"""

    field_name_prefix: str
    valid_value: str
    label: str
    initial_state: str
    initial_state_display: str
    initial_notes: str
    final_state: str
    final_state_display: str
    final_notes: str

    def __init__(self, field_name_prefix: str, audit: "Audit"):
        self.field_name_prefix = field_name_prefix
        self.valid_values = ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_VALID_VALUES.get(
            field_name_prefix, []
        )
        self.label = Audit._meta.get_field(
            f"archive_{field_name_prefix}_state"
        ).verbose_name
        self.initial_state = getattr(audit, f"archive_{field_name_prefix}_state")
        self.initial_state_display = getattr(
            audit, f"get_archive_{field_name_prefix}_state_display"
        )()
        self.initial_notes = getattr(audit, f"archive_{field_name_prefix}_notes")
        self.final_state = getattr(
            audit, f"archive_audit_retest_{field_name_prefix}_state"
        )
        self.final_state_display = getattr(
            audit, f"get_archive_audit_retest_{field_name_prefix}_state_display"
        )()
        self.final_notes = getattr(
            audit, f"archive_audit_retest_{field_name_prefix}_notes"
        )

    @property
    def initially_invalid(self):
        return self.valid_values and self.initial_state not in self.valid_values

    @property
    def finally_fixed(self):
        return self.initially_invalid and self.final_state in self.valid_values

    @property
    def finally_invalid(self):
        return self.valid_values and self.final_state not in self.valid_values


class Audit(VersionModel):
    """
    Model for test
    """

    class ScreenSize(models.TextChoices):
        SIZE_15 = "15in", "15 inch"
        SIZE_14 = "14in", "14 inch"
        SIZE_13 = "13in", "13 inch"

    class Exemptions(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Unknown"

    class Declaration(models.TextChoices):
        PRESENT = "present", "Present and correct"
        NOT_PRESENT = "not-present", "Not included"
        OTHER = "other", "Other"

    class Scope(models.TextChoices):
        PRESENT = "present", "Present and correct"
        NOT_PRESENT = "not-present", "Not included"
        INCOMPLETE = "incomplete", "Does not cover entire website"
        OTHER = "other", "Other"

    case = models.OneToOneField(
        Case, on_delete=models.PROTECT, related_name="audit_case"
    )
    published_report_data_updated_time = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    # metadata page
    date_of_test = models.DateField(default=date.today)
    screen_size = models.CharField(
        max_length=20,
        choices=ScreenSize.choices,
        default=ScreenSize.SIZE_15,
    )
    exemptions_state = models.CharField(
        max_length=20,
        choices=Exemptions.choices,
        default=Exemptions.UNKNOWN,
    )
    exemptions_notes = models.TextField(default="", blank=True)
    audit_metadata_complete_date = models.DateField(null=True, blank=True)

    # Pages page
    audit_pages_complete_date = models.DateField(null=True, blank=True)

    # Website decision
    audit_website_decision_complete_date = models.DateField(null=True, blank=True)

    # Accessibility statement 1
    accessibility_statement_backup_url = models.TextField(default="", blank=True)
    accessibility_statement_backup_url_date = models.DateField(null=True, blank=True)
    archive_declaration_state = models.CharField(
        "Declaration",
        max_length=20,
        choices=Declaration.choices,
        default=Declaration.NOT_PRESENT,
    )
    archive_declaration_notes = models.TextField(default="", blank=True)
    archive_scope_state = models.CharField(
        verbose_name="Scope",
        max_length=20,
        choices=Scope.choices,
        default=Scope.NOT_PRESENT,
    )
    archive_scope_notes = models.TextField(default="", blank=True)
    archive_compliance_state = models.CharField(
        "Compliance Status",
        max_length=20,
        choices=COMPLIANCE_STATE_CHOICES,
        default=COMPLIANCE_STATE_DEFAULT,
    )
    archive_compliance_notes = models.TextField(default="", blank=True)
    archive_non_regulation_state = models.CharField(
        "Non-accessible Content - non compliance with regulations",
        max_length=20,
        choices=NON_REGULATION_STATE_CHOICES,
        default=NON_REGULATION_STATE_DEFAULT,
    )
    archive_non_regulation_notes = models.TextField(default="", blank=True)
    archive_disproportionate_burden_state = models.CharField(
        "Non-accessible Content - disproportionate burden",
        max_length=20,
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
        default=DISPROPORTIONATE_BURDEN_STATE_NO_CLAIM,
    )
    archive_disproportionate_burden_notes = models.TextField(default="", blank=True)
    archive_content_not_in_scope_state = models.CharField(
        "Non-accessible Content - the content is not within the scope of the applicable legislation",
        max_length=20,
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
        default=CONTENT_NOT_IN_SCOPE_STATE_DEFAULT,
    )
    archive_content_not_in_scope_notes = models.TextField(default="", blank=True)
    archive_preparation_date_state = models.CharField(
        "Preparation Date",
        max_length=20,
        choices=PREPARATION_DATE_STATE_CHOICES,
        default=PREPARATION_DATE_STATE_DEFAULT,
    )
    archive_preparation_date_notes = models.TextField(default="", blank=True)
    archive_audit_statement_1_complete_date = models.DateField(null=True, blank=True)

    # Accessibility statement 2
    archive_method_state = models.CharField(
        "Method",
        max_length=20,
        choices=METHOD_STATE_CHOICES,
        default=METHOD_STATE_DEFAULT,
    )
    archive_method_notes = models.TextField(default="", blank=True)
    archive_review_state = models.CharField(
        "Review",
        max_length=20,
        choices=REVIEW_STATE_CHOICES,
        default=REVIEW_STATE_DEFAULT,
    )
    archive_review_notes = models.TextField(default="", blank=True)
    archive_feedback_state = models.CharField(
        "Feedback",
        max_length=20,
        choices=FEEDBACK_STATE_CHOICES,
        default=FEEDBACK_STATE_DEFAULT,
    )
    archive_feedback_notes = models.TextField(default="", blank=True)
    archive_contact_information_state = models.CharField(
        "Contact Information",
        max_length=20,
        choices=CONTACT_INFORMATION_STATE_CHOICES,
        default=CONTACT_INFORMATION_STATE_DEFAULT,
    )
    archive_contact_information_notes = models.TextField(default="", blank=True)
    archive_enforcement_procedure_state = models.CharField(
        "Enforcement Procedure",
        max_length=20,
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
        default=ENFORCEMENT_PROCEDURE_STATE_DEFAULT,
    )
    archive_enforcement_procedure_notes = models.TextField(default="", blank=True)
    archive_access_requirements_state = models.CharField(
        "Access Requirements",
        max_length=20,
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
        default=ACCESS_REQUIREMENTS_STATE_DEFAULT,
    )
    archive_access_requirements_notes = models.TextField(default="", blank=True)
    archive_audit_statement_2_complete_date = models.DateField(null=True, blank=True)

    # Statement decision
    archive_audit_statement_decision_complete_date = models.DateField(
        null=True, blank=True
    )

    # Summary
    audit_summary_complete_date = models.DateField(null=True, blank=True)

    # Report options
    archive_accessibility_statement_state = models.CharField(
        max_length=20,
        choices=ARCHIVE_ACCESSIBILITY_STATEMENT_STATE_CHOICES,
        default=ARCHIVE_ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
    )
    archive_accessibility_statement_not_correct_format = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_not_specific_enough = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_missing_accessibility_issues = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_missing_mandatory_wording = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_missing_mandatory_wording_notes = models.TextField(
        default="", blank=True
    )
    archive_accessibility_statement_needs_more_re_disproportionate = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_needs_more_re_accessibility = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_deadline_not_complete = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_deadline_not_complete_wording = models.TextField(
        default="it includes a deadline of XXX for fixing XXX issues and this has not been completed",
        blank=True,
    )
    archive_accessibility_statement_deadline_not_sufficient = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_deadline_not_sufficient_wording = models.TextField(
        default="it includes a deadline of XXX for fixing XXX issues and this is not sufficient",
        blank=True,
    )
    archive_accessibility_statement_out_of_date = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_eass_link = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_template_update = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_accessible = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_prominent = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_report_options_next = models.CharField(
        max_length=20,
        choices=REPORT_OPTIONS_NEXT_CHOICES,
        default=REPORT_OPTIONS_NEXT_DEFAULT,
    )
    archive_report_next_change_statement = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_report_next_no_statement = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_report_next_statement_not_right = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_report_next_statement_matches = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_report_next_disproportionate_burden = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    archive_accessibility_statement_report_text_wording = models.TextField(
        default="",
        blank=True,
    )
    archive_report_options_notes = models.TextField(default="", blank=True)
    archive_audit_report_options_complete_date = models.DateField(null=True, blank=True)

    # Statement pages
    audit_statement_pages_complete_date = models.DateField(null=True, blank=True)

    # Statement checking overview
    statement_extra_report_text = models.TextField(default="", blank=True)
    audit_statement_overview_complete_date = models.DateField(null=True, blank=True)

    # Statement checking website
    audit_statement_website_complete_date = models.DateField(null=True, blank=True)

    # Statement checking compliance
    audit_statement_compliance_complete_date = models.DateField(null=True, blank=True)

    # Statement checking non-accessible content
    audit_statement_non_accessible_complete_date = models.DateField(
        null=True, blank=True
    )

    # Statement checking preparation
    audit_statement_preparation_complete_date = models.DateField(null=True, blank=True)

    # Statement checking feedback
    audit_statement_feedback_complete_date = models.DateField(null=True, blank=True)

    # Statement checking other
    audit_statement_custom_complete_date = models.DateField(null=True, blank=True)

    # Report text
    archive_audit_report_text_complete_date = models.DateField(null=True, blank=True)

    # retest metadata page
    retest_date = models.DateField(null=True, blank=True)
    audit_retest_metadata_notes = models.TextField(default="", blank=True)
    audit_retest_metadata_complete_date = models.DateField(null=True, blank=True)

    # Retest pages
    audit_retest_pages_complete_date = models.DateField(null=True, blank=True)

    # Retest website compliance
    audit_retest_website_decision_complete_date = models.DateField(
        null=True, blank=True
    )

    # 12-week accessibility statement (no initial statement)
    twelve_week_accessibility_statement_url = models.TextField(default="", blank=True)

    # Retest accessibility statement 1
    audit_retest_accessibility_statement_backup_url = models.TextField(
        default="", blank=True
    )
    audit_retest_accessibility_statement_backup_url_date = models.DateField(
        null=True, blank=True
    )
    archive_audit_retest_declaration_state = models.CharField(
        max_length=20,
        choices=Declaration.choices,
        default=Declaration.NOT_PRESENT,
    )
    archive_audit_retest_declaration_notes = models.TextField(default="", blank=True)
    archive_audit_retest_scope_state = models.CharField(
        max_length=20, choices=Scope.choices, default=Scope.NOT_PRESENT
    )
    archive_audit_retest_scope_notes = models.TextField(default="", blank=True)
    archive_audit_retest_compliance_state = models.CharField(
        max_length=20,
        choices=COMPLIANCE_STATE_CHOICES,
        default=COMPLIANCE_STATE_DEFAULT,
    )
    archive_audit_retest_compliance_notes = models.TextField(default="", blank=True)
    archive_audit_retest_non_regulation_state = models.CharField(
        max_length=20,
        choices=NON_REGULATION_STATE_CHOICES,
        default=NON_REGULATION_STATE_DEFAULT,
    )
    archive_audit_retest_non_regulation_notes = models.TextField(default="", blank=True)
    archive_audit_retest_disproportionate_burden_state = models.CharField(
        max_length=20,
        choices=DISPROPORTIONATE_BURDEN_STATE_CHOICES,
        default=DISPROPORTIONATE_BURDEN_STATE_NO_CLAIM,
    )
    archive_audit_retest_disproportionate_burden_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_content_not_in_scope_state = models.CharField(
        max_length=20,
        choices=CONTENT_NOT_IN_SCOPE_STATE_CHOICES,
        default=CONTENT_NOT_IN_SCOPE_STATE_DEFAULT,
    )
    archive_audit_retest_content_not_in_scope_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_preparation_date_state = models.CharField(
        max_length=20,
        choices=PREPARATION_DATE_STATE_CHOICES,
        default=PREPARATION_DATE_STATE_DEFAULT,
    )
    archive_audit_retest_preparation_date_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_statement_1_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest accessibility statement 2
    archive_audit_retest_method_state = models.CharField(
        max_length=20, choices=METHOD_STATE_CHOICES, default=METHOD_STATE_DEFAULT
    )
    archive_audit_retest_method_notes = models.TextField(default="", blank=True)
    archive_audit_retest_review_state = models.CharField(
        max_length=20, choices=REVIEW_STATE_CHOICES, default=REVIEW_STATE_DEFAULT
    )
    archive_audit_retest_review_notes = models.TextField(default="", blank=True)
    archive_audit_retest_feedback_state = models.CharField(
        max_length=20, choices=FEEDBACK_STATE_CHOICES, default=FEEDBACK_STATE_DEFAULT
    )
    archive_audit_retest_feedback_notes = models.TextField(default="", blank=True)
    archive_audit_retest_contact_information_state = models.CharField(
        max_length=20,
        choices=CONTACT_INFORMATION_STATE_CHOICES,
        default=CONTACT_INFORMATION_STATE_DEFAULT,
    )
    archive_audit_retest_contact_information_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_enforcement_procedure_state = models.CharField(
        max_length=20,
        choices=ENFORCEMENT_PROCEDURE_STATE_CHOICES,
        default=ENFORCEMENT_PROCEDURE_STATE_DEFAULT,
    )
    archive_audit_retest_enforcement_procedure_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_access_requirements_state = models.CharField(
        max_length=20,
        choices=ACCESS_REQUIREMENTS_STATE_CHOICES,
        default=ACCESS_REQUIREMENTS_STATE_DEFAULT,
    )
    archive_audit_retest_access_requirements_notes = models.TextField(
        default="", blank=True
    )
    archive_audit_retest_statement_2_complete_date = models.DateField(
        null=True, blank=True
    )

    # Statement pages
    audit_retest_statement_pages_complete_date = models.DateField(null=True, blank=True)

    # Retest statement checking overview
    audit_retest_statement_overview_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking website
    audit_retest_statement_website_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking compliance
    audit_retest_statement_compliance_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking non-accessible content
    audit_retest_statement_non_accessible_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking preparation
    audit_retest_statement_preparation_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking feedback
    audit_retest_statement_feedback_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking other
    audit_retest_statement_custom_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement comparison
    audit_retest_statement_comparison_complete_date = models.DateField(
        null=True, blank=True
    )
    # Retest statement decision
    archive_audit_retest_statement_decision_complete_date = models.DateField(
        null=True, blank=True
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.case}" f" (Test {amp_format_date(self.date_of_test)})")

    def get_absolute_url(self) -> str:
        return reverse("audits:audit-detail", kwargs={"pk": self.pk})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_accessibility_statement_backup_url = (
            self.accessibility_statement_backup_url
        )
        self.__original_audit_retest_accessibility_statement_backup_url = (
            self.audit_retest_accessibility_statement_backup_url
        )

    def save(self, *args, **kwargs) -> None:
        if (
            self.accessibility_statement_backup_url
            != self.__original_accessibility_statement_backup_url
        ):
            self.accessibility_statement_backup_url_date = timezone.now()
        if (
            self.audit_retest_accessibility_statement_backup_url
            != self.__original_audit_retest_accessibility_statement_backup_url
        ):
            self.audit_retest_accessibility_statement_backup_url_date = timezone.now()
        self.__original_accessibility_statement_backup_url = (
            self.accessibility_statement_backup_url
        )
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    @property
    def report_accessibility_issues(self) -> List[str]:
        issues: List[str] = []
        for key, value in ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT.items():
            if getattr(self, key) == Boolean.YES:
                if key == "archive_accessibility_statement_deadline_not_complete":
                    issues.append(
                        self.archive_accessibility_statement_deadline_not_complete_wording
                    )
                elif key == "archive_accessibility_statement_deadline_not_sufficient":
                    issues.append(
                        self.archive_accessibility_statement_deadline_not_sufficient_wording
                    )
                else:
                    issues.append(value)
        return issues

    @property
    def deleted_pages(self):
        return self.page_audit.filter(is_deleted=True)

    @property
    def every_page(self):
        """Sort page of type PDF to be last"""
        return (
            self.page_audit.filter(is_deleted=False)
            .annotate(
                position_pdfs_statements_last=DjangoCase(
                    When(page_type=PAGE_TYPE_PDF, then=1),
                    When(page_type=PAGE_TYPE_STATEMENT, then=2),
                    default=0,
                )
            )
            .order_by("position_pdfs_statements_last", "id")
        )

    @property
    def testable_pages(self):
        return self.every_page.exclude(not_found=Boolean.YES).exclude(url="")

    @property
    def html_pages(self):
        return self.every_page.exclude(page_type=PAGE_TYPE_PDF)

    @property
    def accessibility_statement_page(self):
        return self.every_page.filter(page_type=PAGE_TYPE_STATEMENT).first()

    @property
    def contact_page(self):
        return self.every_page.filter(page_type=PAGE_TYPE_CONTACT).first()

    @property
    def standard_pages(self):
        return self.every_page.exclude(page_type=PAGE_TYPE_EXTRA)

    @property
    def extra_pages(self):
        return self.html_pages.filter(page_type=PAGE_TYPE_EXTRA)

    @property
    def failed_check_results(self):
        return (
            self.checkresult_audit.filter(
                is_deleted=False,
                check_result_state=CHECK_RESULT_ERROR,
                page__is_deleted=False,
                page__not_found=Boolean.NO,
                page__retest_page_missing_date=None,
            )
            .annotate(
                position_pdf_page_last=DjangoCase(
                    When(page__page_type=PAGE_TYPE_PDF, then=1), default=0
                )
            )
            .order_by("position_pdf_page_last", "page__id", "wcag_definition__id")
            .select_related("page", "wcag_definition")
            .all()
        )

    @property
    def fixed_check_results(self):
        return self.failed_check_results.filter(retest_state=RETEST_CHECK_RESULT_FIXED)

    @property
    def unfixed_check_results(self):
        return self.failed_check_results.exclude(retest_state=RETEST_CHECK_RESULT_FIXED)

    @property
    def accessibility_statement_checks(
        self,
    ) -> List[ArchiveAccessibilityStatementCheck]:
        return [
            ArchiveAccessibilityStatementCheck(
                field_name_prefix=field_name_prefix, audit=self
            )
            for field_name_prefix in ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_PREFIXES
        ]

    @property
    def accessibility_statement_initially_invalid_checks_count(self):
        return len(
            [
                statement_check
                for statement_check in self.accessibility_statement_checks
                if statement_check.initially_invalid
            ]
        )

    @property
    def fixed_accessibility_statement_checks_count(self):
        return len(
            [
                statement_check
                for statement_check in self.accessibility_statement_checks
                if statement_check.finally_fixed
            ]
        )

    @property
    def finally_invalid_accessibility_statement_checks(self):
        return [
            statement_check
            for statement_check in self.accessibility_statement_checks
            if statement_check.finally_invalid
        ]

    @property
    def statement_check_results(self) -> bool:
        return self.statementcheckresult_set.filter(is_deleted=False)

    @property
    def uses_statement_checks(self) -> bool:
        return self.statement_check_results.count() > 0

    @property
    def overview_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(type=STATEMENT_CHECK_TYPE_OVERVIEW)

    @property
    def overview_statement_checks_complete(self) -> bool:
        return (
            self.overview_statement_check_results.filter(
                check_result_state=STATEMENT_CHECK_NOT_TESTED
            ).count()
            == 0
        )

    @property
    def statement_check_result_statement_found(self) -> bool:
        overview_statement_yes_count: CheckResult = (
            self.overview_statement_check_results.filter(
                check_result_state=STATEMENT_CHECK_YES
            ).count()
        )
        return (
            overview_statement_yes_count
            == self.overview_statement_check_results.count()
        )

    @property
    def website_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(type=STATEMENT_CHECK_TYPE_WEBSITE)

    @property
    def compliance_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(type=STATEMENT_CHECK_TYPE_COMPLIANCE)

    @property
    def non_accessible_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_NON_ACCESSIBLE
        )

    @property
    def preparation_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_PREPARATION
        )

    @property
    def feedback_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(type=STATEMENT_CHECK_TYPE_FEEDBACK)

    @property
    def custom_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(type=STATEMENT_CHECK_TYPE_CUSTOM)

    @property
    def failed_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(
            check_result_state=STATEMENT_CHECK_NO
        )

    @property
    def passed_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(
            check_result_state=STATEMENT_CHECK_YES
        )

    @property
    def outstanding_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(
            Q(check_result_state=STATEMENT_CHECK_NO)
            | Q(retest_state=STATEMENT_CHECK_NO)
        ).exclude(retest_state=STATEMENT_CHECK_YES)

    @property
    def overview_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_OVERVIEW
        )

    @property
    def website_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_WEBSITE
        )

    @property
    def compliance_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_COMPLIANCE
        )

    @property
    def non_accessible_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_NON_ACCESSIBLE
        )

    @property
    def preparation_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_PREPARATION
        )

    @property
    def feedback_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_FEEDBACK
        )

    @property
    def custom_outstanding_statement_check_results(self) -> bool:
        return self.outstanding_statement_check_results.filter(
            type=STATEMENT_CHECK_TYPE_CUSTOM
        )

    @property
    def all_overview_statement_checks_have_passed(self) -> bool:
        """Check all overview statement checks have passed test or retest"""
        return (
            self.overview_statement_check_results.exclude(
                check_result_state=STATEMENT_CHECK_YES
            ).count()
            == 0
            or self.overview_statement_check_results.exclude(
                retest_state=STATEMENT_CHECK_YES
            ).count()
            == 0
        )

    @property
    def failed_retest_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(retest_state=STATEMENT_CHECK_NO)

    @property
    def passed_retest_statement_check_results(self) -> bool:
        return self.statement_check_results.filter(retest_state=STATEMENT_CHECK_YES)

    @property
    def fixed_statement_check_results(self) -> bool:
        return self.failed_statement_check_results.filter(
            retest_state=STATEMENT_CHECK_YES
        )

    @property
    def statement_pages(self) -> bool:
        return self.statementpage_set.filter(is_deleted=False)

    @property
    def accessibility_statement_initially_found(self):
        return self.statement_pages.filter(added_stage=ADDED_STAGE_INITIAL).count() > 0

    @property
    def twelve_week_accessibility_statement_found(self):
        return (
            self.statement_pages.filter(added_stage=ADDED_STAGE_TWELVE_WEEK).count() > 0
        )

    @property
    def accessibility_statement_found(self):
        return self.statement_pages.count() > 0


class Page(models.Model):
    """
    Model for test/audit page
    """

    audit = models.ForeignKey(
        Audit, on_delete=models.PROTECT, related_name="page_audit"
    )
    is_deleted = models.BooleanField(default=False)

    page_type = models.CharField(
        max_length=20, choices=PAGE_TYPE_CHOICES, default=PAGE_TYPE_EXTRA
    )
    name = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    complete_date = models.DateField(null=True, blank=True)
    no_errors_date = models.DateField(null=True, blank=True)
    not_found = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    is_contact_page = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    retest_complete_date = models.DateField(null=True, blank=True)
    retest_page_missing_date = models.DateField(null=True, blank=True)
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return self.name if self.name else self.get_page_type_display()

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)
        if self.page_type == PAGE_TYPE_STATEMENT:
            self.audit.case.set_statement_compliance_states()

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-audit-page-checks", kwargs={"pk": self.pk})

    @property
    def all_check_results(self):
        return (
            self.checkresult_page.filter(is_deleted=False)
            .order_by("wcag_definition__id")
            .select_related("wcag_definition")
            .all()
        )

    @property
    def failed_check_results(self):
        return self.all_check_results.filter(check_result_state=CHECK_RESULT_ERROR)

    @property
    def unfixed_check_results(self):
        return self.failed_check_results.exclude(retest_state=RETEST_CHECK_RESULT_FIXED)

    @property
    def check_results_by_wcag_definition(self):
        check_results: QuerySet[CheckResult] = self.all_check_results
        return {
            check_result.wcag_definition: check_result for check_result in check_results
        }

    @property
    def anchor(self):
        return f"test-page-{self.id}"


class WcagDefinition(models.Model):
    """
    Model for WCAG tests captured by the platform
    """

    type = models.CharField(
        max_length=20, choices=TEST_TYPE_CHOICES, default=TEST_TYPE_MANUAL
    )
    name = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)
    url_on_w3 = models.TextField(default="", blank=True)
    report_boilerplate = models.TextField(default="", blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    objects = StartEndDateManager()

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        if self.description:
            return str(f"{self.name}: {self.description} ({self.get_type_display()})")
        return f"{self.name} ({self.get_type_display()})"

    def get_absolute_url(self) -> str:
        return reverse("audits:wcag-definition-update", kwargs={"pk": self.pk})


class CheckResult(models.Model):
    """
    Model for test result
    """

    audit = models.ForeignKey(
        Audit, on_delete=models.PROTECT, related_name="checkresult_audit"
    )
    page = models.ForeignKey(
        Page, on_delete=models.PROTECT, related_name="checkresult_page"
    )
    is_deleted = models.BooleanField(default=False)
    type = models.CharField(
        max_length=20, choices=TEST_TYPE_CHOICES, default=TEST_TYPE_PDF
    )
    wcag_definition = models.ForeignKey(
        WcagDefinition,
        on_delete=models.PROTECT,
        related_name="checkresult_wcagdefinition",
    )

    check_result_state = models.CharField(
        max_length=20,
        choices=CHECK_RESULT_STATE_CHOICES,
        default=CHECK_RESULT_NOT_TESTED,
    )
    notes = models.TextField(default="", blank=True)
    retest_state = models.CharField(
        max_length=20,
        choices=RETEST_CHECK_RESULT_STATE_CHOICES,
        default=RETEST_CHECK_RESULT_DEFAULT,
    )
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    @property
    def dict_for_retest(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "retest_state": self.retest_state,
            "retest_notes": self.retest_notes,
        }

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return str(f"{self.page} | {self.wcag_definition}")

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)


class StatementCheck(models.Model):
    """
    Model for accessibilty statement-specific checks
    """

    type = models.CharField(
        max_length=20,
        choices=STATEMENT_CHECK_TYPE_CHOICES,
        default=STATEMENT_CHECK_TYPE_CUSTOM,
    )
    label = models.TextField(default="", blank=True)
    success_criteria = models.TextField(default="", blank=True)
    report_text = models.TextField(default="", blank=True)
    position = models.IntegerField(default=0)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    objects = StartEndDateManager()

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        if self.success_criteria:
            return str(
                f"{self.label}: {self.success_criteria} ({self.get_type_display()})"
            )
        return f"{self.label} ({self.get_type_display()})"

    def get_absolute_url(self) -> str:
        return reverse("audits:statement-check-update", kwargs={"pk": self.pk})


class StatementCheckResult(models.Model):
    """
    Model for accessibility statement-specific check result
    """

    audit = models.ForeignKey(Audit, on_delete=models.PROTECT)
    statement_check = models.ForeignKey(
        StatementCheck, on_delete=models.PROTECT, null=True, blank=True
    )
    type = models.CharField(
        max_length=20,
        choices=STATEMENT_CHECK_TYPE_CHOICES,
        default=STATEMENT_CHECK_TYPE_CUSTOM,
    )
    check_result_state = models.CharField(
        max_length=10,
        choices=STATEMENT_CHECK_CHOICES,
        default=STATEMENT_CHECK_NOT_TESTED,
    )
    report_comment = models.TextField(default="", blank=True)
    auditor_notes = models.TextField(default="", blank=True)
    retest_state = models.CharField(
        max_length=10,
        choices=STATEMENT_CHECK_CHOICES,
        default=STATEMENT_CHECK_NOT_TESTED,
    )
    retest_comment = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["statement_check__position", "id"]

    def __str__(self) -> str:
        if self.statement_check is None:
            return str(f"{self.audit} | Custom")
        return str(f"{self.audit} | {self.statement_check}")

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.audit.case.set_statement_compliance_states()

    @property
    def label(self):
        return self.statement_check.label if self.statement_check else "Custom"


class Retest(VersionModel):
    """
    Model for retest of outstanding issues requested by an equality body
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=1, blank=True)
    date_of_retest = models.DateField(default=date.today)
    retest_notes = models.TextField(default="", blank=True)
    retest_compliance_state = models.CharField(
        max_length=20,
        choices=RETEST_INITIAL_COMPLIANCE_CHOICES,
        default=RETEST_INITIAL_COMPLIANCE_DEFAULT,
    )
    compliance_notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)
    complete_date = models.DateField(null=True, blank=True)
    comparison_complete_date = models.DateField(null=True, blank=True)
    compliance_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["case_id", "-id_within_case"]

    def get_absolute_url(self) -> str:
        return reverse("audits:retest-compliance-update", kwargs={"pk": self.id})

    def __str__(self) -> str:
        if self.id_within_case == 0:
            return "12-week retest"
        return str(f"Retest #{self.id_within_case}")

    @property
    def is_incomplete(self) -> bool:
        return self.retest_compliance_state == RETEST_INITIAL_COMPLIANCE_DEFAULT

    @property
    def fixed_checks_count(self):
        """
        Add the numbers of checks fixed in the 12-week retest and all equality
        body requested retests up to this one.
        """
        fixed_checks_count: int = (
            CheckResult.objects.filter(audit=self.case.audit)
            .filter(retest_state=RETEST_CHECK_RESULT_FIXED)
            .exclude(page__not_found="yes")
            .count()
        )
        for retest in self.case.retests.exclude(
            id_within_case__gt=self.id_within_case
        ).exclude(id_within_case=0):
            fixed_checks_count += (
                RetestCheckResult.objects.filter(retest=retest)
                .filter(retest_state=RETEST_CHECK_RESULT_FIXED)
                .exclude(retest_page__page__not_found="yes")
                .count()
            )
        return fixed_checks_count

    @property
    def original_retest(self):
        """Copy of 12-week retest results"""
        return self.case.retests.filter(id_within_case=0).first()

    @property
    def previous_retest(self):
        """Return previous retest"""
        if self.id_within_case > 0:
            return self.case.retests.filter(
                id_within_case=self.id_within_case - 1
            ).first()
        return None

    @property
    def latest_retest(self):
        """Return latest retest"""
        return self.case.retests.first()


class RetestPage(models.Model):
    """
    Model for equality body requested retest page
    """

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    page = models.ForeignKey(Page, on_delete=models.PROTECT)
    missing_date = models.DateField(null=True, blank=True)
    complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return f"{self.page}"

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-retest-page-checks", kwargs={"pk": self.pk})

    @property
    def heading(self):
        return f"{self.retest} | {self.page}"

    @property
    def all_check_results(self):
        return self.retestcheckresult_set.all()

    @property
    def unfixed_check_results(self):
        return self.all_check_results.exclude(retest_state=RETEST_CHECK_RESULT_FIXED)

    @property
    def original_check_results(self):
        return self.retest.original_retest.retestpage_set.get(
            page=self.page
        ).all_check_results


class RetestCheckResult(models.Model):
    """
    Model for equality body requested retest result
    """

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    retest_page = models.ForeignKey(RetestPage, on_delete=models.PROTECT)
    check_result = models.ForeignKey(CheckResult, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    retest_state = models.CharField(
        max_length=20,
        choices=RETEST_CHECK_RESULT_STATE_CHOICES,
        default=RETEST_CHECK_RESULT_DEFAULT,
    )
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return str(f"{self.retest_page} | {self.check_result}")

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    @property
    def original_retest_check_result(self):
        """Return original copy of 12-week retest result for this check"""
        return self.retest.original_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def latest_retest_check_result(self):
        """Return latest retest result for this check"""
        return self.retest.latest_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def previous_retest_check_result(self):
        """Return previous retest result for this check"""
        return self.retest.previous_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def all_retest_check_results(self):
        """Return all retest results for this check"""
        return RetestCheckResult.objects.filter(check_result=self.check_result)


class StatementPage(models.Model):
    """
    Model to store links to statement pages found at various stages in the life
    of a case.
    """

    audit = models.ForeignKey(Audit, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)

    url = models.TextField(default="", blank=True)
    backup_url = models.TextField(default="", blank=True)
    added_stage = models.CharField(
        max_length=20, choices=ADDED_STAGE_CHOICES, default=ADDED_STAGE_INITIAL
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return self.url or self.backup_url
