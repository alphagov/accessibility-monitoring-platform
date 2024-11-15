"""
Archive Cases by recreating the structure of the UI as JSON.

The unarchived Cases with ids lower than #1170 are those without statement
content check (yes/no) results. Case #1168 is the canonical example.
"""

import json
from datetime import datetime

from django.conf import settings
from django.db import migrations

from ...common.archive_utils import build_field, build_section
from ...common.templatetags.common_tags import amp_datetime

ARCHIVE_VERSION: int = 3
FIRST_STATEMENT_CONTENT_CASE_ID: int = 1170


def get_initial_wcag_test_subsections(
    case, case_compliance, audit, pages, error_check_results, wcag_definitions
):
    page_fields = [
        build_field(
            page,
            field_name="url",
            label=page.name if page.name else page.get_page_type_display(),
            data_type="link",
        )
        for page in pages
    ]
    page_subsections = [
        build_section(
            name=page.name if page.name else page.get_page_type_display(),
            complete_date=page.complete_date,
            fields=[
                {
                    "name": "CheckResult",
                    "data_type": "markdown",
                    "label": f"{wcag_definitions[check_result.wcag_definition_id].name}: {wcag_definitions[check_result.wcag_definition_id].description} ({wcag_definitions[check_result.wcag_definition_id].get_type_display()})",
                    "value": check_result.notes,
                    "display_value": None,
                }
                for check_result in error_check_results[page.id]
            ],
        )
        for page in pages
    ]
    audit_subsections = [
        build_section(
            name="Initial test metadata",
            complete_date=audit.audit_metadata_complete_date,
            fields=[
                build_field(audit, field_name="date_of_test", label="Date of test"),
                build_field(audit, field_name="screen_size", label="Screen size"),
                build_field(audit, field_name="exemptions_state", label="Exemptions?"),
                build_field(
                    audit,
                    field_name="exemptions_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="Pages",
            complete_date=audit.audit_pages_complete_date,
            fields=page_fields,
            subsections=page_subsections,
        ),
        build_section(
            name="Initial website compliance decision",
            complete_date=audit.audit_website_decision_complete_date,
            fields=[
                build_field(
                    case_compliance,
                    field_name="website_compliance_state_initial",
                    label="Initial website compliance decision",
                ),
                build_field(
                    case_compliance,
                    field_name="website_compliance_notes_initial",
                    label="Initial website compliance notes",
                    data_type="markdown",
                ),
            ],
        ),
    ]
    return audit_subsections


def get_initial_statement_test_subsections(
    case, case_compliance, audit, pages, error_check_results, wcag_definitions
):
    statement_links_subsections = []
    for count, statement_page in enumerate(audit.statementpage_set.all(), start=1):
        statement_links_subsections.append(
            build_section(
                name=f"Statement {count}",
                complete_date=None,
                fields=[
                    build_field(
                        statement_page,
                        field_name="url",
                        label="Link to statement",
                        data_type="link",
                    ),
                    build_field(
                        statement_page,
                        field_name="backup_url",
                        label="Statement backup",
                        data_type="link",
                    ),
                    build_field(
                        statement_page,
                        field_name="added_stage",
                        label="Statement added",
                    ),
                    build_field(statement_page, field_name="created", label="Created"),
                ],
            )
        )
    audit_subsections = [
        build_section(
            name="Statement links",
            complete_date=audit.audit_statement_pages_complete_date,
            fields=[],
            subsections=statement_links_subsections,
        ),
        build_section(
            name="Accessibility statement Pt. 1",
            complete_date=audit.archive_audit_statement_1_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="accessibility_statement_backup_url",
                    label="Link to saved accessibility statement",
                    data_type="link",
                ),
                build_field(audit, field_name="archive_scope_state", label="Scope"),
                build_field(
                    audit,
                    field_name="archive_scope_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit, field_name="archive_feedback_state", label="Feedback"
                ),
                build_field(
                    audit,
                    field_name="archive_feedback_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_contact_information_state",
                    label="Contact Information",
                ),
                build_field(
                    audit,
                    field_name="archive_contact_information_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_enforcement_procedure_state",
                    label="Enforcement Procedure",
                ),
                build_field(
                    audit,
                    field_name="archive_enforcement_procedure_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit, field_name="archive_declaration_state", label="Declaration"
                ),
                build_field(
                    audit,
                    field_name="archive_declaration_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_compliance_state",
                    label="Compliance Status",
                ),
                build_field(
                    audit,
                    field_name="archive_compliance_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_non_regulation_state",
                    label="Non-accessible Content - non compliance with regulations",
                ),
                build_field(
                    audit,
                    field_name="archive_non_regulation_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="Accessibility statement Pt. 2",
            complete_date=audit.archive_audit_statement_2_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="accessibility_statement_backup_url",
                    label="Link to saved accessibility statement",
                    data_type="link",
                ),
                build_field(
                    audit,
                    field_name="archive_disproportionate_burden_state",
                    label="Non-accessible Content - disproportionate burden",
                ),
                build_field(
                    audit,
                    field_name="archive_disproportionate_burden_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_content_not_in_scope_state",
                    label="Non-accessible Content - the content is not within the scope of the applicable legislation",
                ),
                build_field(
                    audit,
                    field_name="archive_content_not_in_scope_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_preparation_date_state",
                    label="Preparation Date",
                ),
                build_field(
                    audit,
                    field_name="archive_preparation_date_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(audit, field_name="archive_review_state", label="Review"),
                build_field(
                    audit,
                    field_name="archive_review_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(audit, field_name="archive_method_state", label="Method"),
                build_field(
                    audit,
                    field_name="archive_method_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_access_requirements_state",
                    label="Access Requirements",
                ),
                build_field(
                    audit,
                    field_name="archive_access_requirements_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="Initial disproportionate burden claim",
            complete_date=audit.initial_disproportionate_burden_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="initial_disproportionate_burden_claim",
                    label="Initial disproportionate burden claim (included in equality body export)",
                ),
                build_field(
                    audit,
                    field_name="initial_disproportionate_burden_notes",
                    label="Initial disproportionate burden claim details (included in equality body export)",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="Initial statement compliance decision",
            complete_date=audit.audit_website_decision_complete_date,
            fields=[
                build_field(
                    case_compliance,
                    field_name="statement_compliance_state_initial",
                    label="Initial accessibility statement compliance decision",
                ),
                build_field(
                    case_compliance,
                    field_name="statement_compliance_notes_initial",
                    label="Initial accessibility statement compliance notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="Report options",
            complete_date=audit.archive_audit_report_options_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_state",
                    label="Accessibility statement",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_not_correct_format",
                    label="it was not in the correct format",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_not_specific_enough",
                    label="it was not specific enough",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_missing_accessibility_issues",
                    label="accessibility issues were found during the test that were not included in the statement",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_missing_mandatory_wording",
                    label="mandatory wording is missing",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_missing_mandatory_wording_notes",
                    label="Additional text for mandatory wording",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_needs_more_re_disproportionate",
                    label="we require more information covering the disproportionate burden claim",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_needs_more_re_accessibility",
                    label="it required more information detailing the accessibility issues",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_deadline_not_complete",
                    label="it includes a deadline of XXX for fixing XXX issues and this has not been completed",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_deadline_not_complete_wording",
                    label="Wording for missed deadline",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_deadline_not_sufficient",
                    label="it includes a deadline of XXX for fixing XXX issues and this is not sufficient",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_deadline_not_sufficient_wording",
                    label="Wording for insufficient deadline",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_out_of_date",
                    label="it is out of date and needs to be reviewed",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_eass_link",
                    label="it must link directly to the Equality Advisory and Support Service (EASS) website",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_template_update",
                    label="it is a requirement that accessibility statements are accessible. Some users may experience difficulties using PDF documents. It may be beneficial for users if there was a HTML version of your full accessibility statement.",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_accessible",
                    label="in 2020 the GOV.UK sample template was updated to include an extra  mandatory piece of information to outline the scope of your accessibility statement. This needs to be added to your statement.",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_prominent",
                    label="your statement should be prominently placed on the homepage of the website  or made available on every web page, for example in a static header or footer, as per the legislative requirement.",
                ),
                build_field(
                    audit,
                    field_name="archive_accessibility_statement_report_text_wording",
                    label="Extra wording for report",
                ),
                build_field(
                    audit,
                    field_name="archive_report_options_next",
                    label="What to do next",
                ),
                build_field(
                    audit,
                    field_name="archive_report_next_change_statement",
                    label="They have an acceptable statement but need to change it because of the errors we found",
                ),
                build_field(
                    audit,
                    field_name="archive_report_next_no_statement",
                    label="They don’t have a statement, or it is in the wrong format",
                ),
                build_field(
                    audit,
                    field_name="archive_report_next_statement_not_right",
                    label="They have a statement but it is not quite right",
                ),
                build_field(
                    audit,
                    field_name="archive_report_next_statement_matches",
                    label="Their statement matches",
                ),
                build_field(
                    audit,
                    field_name="archive_report_next_disproportionate_burden",
                    label="Disproportionate burden",
                ),
                build_field(
                    audit,
                    field_name="archive_report_options_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
    ]
    return audit_subsections


def get_contact_subsections(contacts):
    """Find case contacts and return data as subsections"""
    contact_subsections = []
    for count, contact in enumerate(contacts, start=1):
        fields = [
            build_field(contact, field_name="name", label="Name"),
            build_field(contact, field_name="job_title", label="Job title"),
            build_field(contact, field_name="email", label="Email"),
        ]
        if len(contacts) > 1:
            fields.append(
                build_field(contact, field_name="preferred", label="Preferred contact")
            )
            contact_subsections.append(
                build_section(f"Contact {count}", complete_date=None, fields=fields)
            )
        else:
            contact_subsections.append(
                build_section(name="Contact", complete_date=None, fields=fields)
            )
    return contact_subsections


def get_comment_subsections(comments, user_names):
    """Find case comments and return data as subsections"""
    return [
        build_section(
            name=f"Comment by {user_names.get(comment.user_id, 'None')} on {amp_datetime(comment.created_date)}",
            complete_date=None,
            fields=[
                build_field(
                    comment,
                    field_name="body",
                    label="Comment",
                    data_type="markdown",
                ),
            ],
        )
        for count, comment in enumerate(comments, start=1)
    ]


def get_12_week_wcag_test_subsections(
    case, case_compliance, audit, pages, error_check_results, wcag_definitions
):
    page_fields = [
        build_field(
            page,
            field_name="url",
            label=page.name if page.name else page.get_page_type_display(),
            data_type="link",
        )
        for page in pages
    ]
    page_subsections = [
        build_section(
            name=f"12-week retest {page.name if page.name else page.get_page_type_display()}",
            complete_date=page.complete_date,
            fields=[
                {
                    "name": "CheckResult",
                    "data_type": "markdown",
                    "label": f"{wcag_definitions[check_result.wcag_definition_id].name}: {wcag_definitions[check_result.wcag_definition_id].description} ({wcag_definitions[check_result.wcag_definition_id].get_type_display()})",
                    "display_value": None,
                }
                for check_result in error_check_results[page.id]
            ],
        )
        for page in pages
    ]
    audit_subsections = [
        build_section(
            name="12-week retest metadata",
            complete_date=audit.audit_retest_metadata_complete_date,
            fields=[
                build_field(audit, field_name="retest_date", label="Date of retest"),
                build_field(
                    audit,
                    field_name="audit_retest_metadata_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="12-week retest pages",
            complete_date=audit.audit_pages_complete_date,
            fields=page_fields,
            subsections=page_subsections,
        ),
        build_section(
            name="12-week retest website compliance decision",
            complete_date=audit.audit_retest_website_decision_complete_date,
            fields=[
                build_field(
                    case_compliance,
                    field_name="website_compliance_state_12_week",
                    label="12-week website compliance decision",
                ),
                build_field(
                    case_compliance,
                    field_name="website_compliance_notes_12_week",
                    label="12-week website compliance decision notes",
                    data_type="markdown",
                ),
            ],
        ),
    ]
    return audit_subsections


def get_12_week_statement_test_subsections(
    case, case_compliance, audit, pages, error_check_results, wcag_definitions
):
    audit_subsections = [
        build_section(
            name="12-week retest accessibility statement Pt. 1",
            complete_date=audit.archive_audit_retest_statement_1_complete_date,
            fields=[
                build_field(
                    audit, field_name="archive_audit_retest_scope_state", label="Scope"
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_scope_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_feedback_state",
                    label="Feedback",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_feedback_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_contact_information_state",
                    label="Contact Information",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_contact_information_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_enforcement_procedure_state",
                    label="Enforcement Procedure",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_enforcement_procedure_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_declaration_state",
                    label="Declaration",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_declaration_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_compliance_state",
                    label="Compliance Status",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_compliance_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_non_regulation_state",
                    label="Non-accessible Content - non compliance with regulations",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_non_regulation_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="12-week retest accessibility statement Pt. 2",
            complete_date=audit.archive_audit_retest_statement_2_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="archive_audit_retest_disproportionate_burden_state",
                    label="Non-accessible Content - disproportionate burden",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_disproportionate_burden_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_content_not_in_scope_state",
                    label="Non-accessible Content - the content is not within the scope of the applicable legislation",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_content_not_in_scope_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_preparation_date_state",
                    label="Preparation Date",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_preparation_date_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_review_state",
                    label="Review",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_review_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_method_state",
                    label="Method",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_method_notes",
                    label="Notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_access_requirements_state",
                    label="Access Requirements",
                ),
                build_field(
                    audit,
                    field_name="archive_audit_retest_access_requirements_notes",
                    label="Notes",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="12-week retest disproportionate burden claim",
            complete_date=audit.twelve_week_disproportionate_burden_complete_date,
            fields=[
                build_field(
                    audit,
                    field_name="twelve_week_disproportionate_burden_claim",
                    label="12-week disproportionate burden claim (included in equality body export)",
                ),
                build_field(
                    audit,
                    field_name="twelve_week_disproportionate_burden_notes",
                    label="12-week disproportionate burden claim details (included in equality body export)",
                    data_type="markdown",
                ),
            ],
        ),
        build_section(
            name="12-week retest statement compliance decision",
            complete_date=audit.audit_retest_statement_decision_complete_date,
            fields=[
                build_field(
                    case_compliance,
                    field_name="statement_compliance_state_12_week",
                    label="12-week accessibility statement compliance decision",
                ),
                build_field(
                    case_compliance,
                    field_name="statement_compliance_notes_12_week",
                    label="12-week accessibility statement compliance notes",
                    data_type="markdown",
                ),
                build_field(
                    audit,
                    field_name="audit_retest_accessibility_statement_backup_url",
                    label="Link to 12-week saved accessibility statement, only if not compliant",
                    data_type="link",
                ),
            ],
        ),
    ]
    return audit_subsections


def archive_old_fields(apps, schema_editor):  # pylint: disable=unused-argument
    return  # No longer run this archive. It fails in prototypes with empty databases.
    if settings.UNDER_TEST or settings.INTEGRATION_TEST:
        # Migration is incompatible with unit test environment
        return
    User = apps.get_model("auth", "User")
    user_names = {
        user.id: f"{user.first_name} {user.last_name}" for user in User.objects.all()
    }
    Sector = apps.get_model("common", "Sector")
    sector_names = {sector.id: sector.name for sector in Sector.objects.all()}
    Case = apps.get_model("cases", "Case")
    CaseStatus = apps.get_model("cases", "CaseStatus")
    CaseCompliance = apps.get_model("cases", "CaseCompliance")
    Contact = apps.get_model("cases", "Contact")
    Comment = apps.get_model("comments", "Comment")
    Audit = apps.get_model("audits", "Audit")
    Page = apps.get_model("audits", "Page")
    WcagDefinition = apps.get_model("audits", "WcagDefinition")
    wcag_definitions = {
        wcag_definition.id: wcag_definition
        for wcag_definition in WcagDefinition.objects.all()
    }
    CheckResult = apps.get_model("audits", "CheckResult")
    for case in (
        Case.objects.filter(archive="")
        .filter(id__lt=FIRST_STATEMENT_CONTENT_CASE_ID)
        .filter(archive="")
    ):
        case_status = CaseStatus.objects.get(case=case)
        case_compliance = CaseCompliance.objects.get(case=case)
        comments = Comment.objects.filter(case=case).order_by("-created_date")
        audit = Audit.objects.filter(case=case).first()
        pages = Page.objects.filter(audit=audit).exclude(url="")
        error_check_results = {
            page.id: CheckResult.objects.filter(page=page).filter(
                check_result_state="error"
            )
            for page in pages
        }
        case_details_section = build_section(
            name="Case details",
            complete_date=None,
            fields=[],
            subsections=[
                build_section(
                    name="Case metadata",
                    complete_date=case.case_details_complete_date,
                    fields=[
                        build_field(
                            case,
                            field_name="created",
                            label="Date created",
                            data_type="date",
                        ),
                        build_field(case_status, field_name="status", label="Status"),
                        build_field(
                            case,
                            field_name="auditor_id",
                            label="Auditor",
                            display_value=user_names.get(case.auditor_id, "None"),
                        ),
                        build_field(
                            case,
                            field_name="home_page_url",
                            label="Full URL (included in equality body export)",
                            data_type="link",
                        ),
                        build_field(
                            case,
                            field_name="organisation_name",
                            label="Organisation name (included in equality body export)",
                        ),
                        build_field(
                            case,
                            field_name="parental_organisation_name",
                            label="Parent organisation name (included in equality body export)",
                        ),
                        build_field(
                            case,
                            field_name="website_name",
                            label="Website name (included in equality body export)",
                        ),
                        build_field(
                            case,
                            field_name="subcategory",
                            label="Subcategory",
                            data_type="str",
                        ),
                        build_field(
                            case,
                            field_name="enforcement_body",
                            label="Which equalities body will check the case?",
                        ),
                        build_field(
                            case,
                            field_name="psb_location",
                            label="Public sector body location",
                        ),
                        build_field(
                            case,
                            field_name="sector_id",
                            label="Sector",
                            data_type="str",
                            display_value=sector_names.get(case.sector_id, "None"),
                        ),
                        build_field(
                            case, field_name="is_complaint", label="Complaint?"
                        ),
                        build_field(
                            case,
                            field_name="previous_case_url",
                            label="URL to previous case",
                            data_type="link",
                            display_value=case.previous_case_url,
                        ),
                        build_field(
                            case,
                            field_name="notes",
                            label="Notes",
                            data_type="markdown",
                        ),
                        build_field(
                            case,
                            field_name="trello_url",
                            label="Trello ticket URL",
                            data_type="link",
                            display_value=case.trello_url,
                        ),
                        build_field(
                            case,
                            field_name="is_feedback_requested",
                            label="Feedback survey sent?",
                        ),
                    ],
                ),
            ],
        )
        if audit is None:
            print(f"{case} has no audit")
            sections = [case_details_section]
        else:
            sections = [
                case_details_section,
                build_section(
                    name="Initial WCAG test",
                    complete_date=None,
                    fields=[],
                    subsections=(
                        get_initial_wcag_test_subsections(
                            case,
                            case_compliance,
                            audit,
                            pages,
                            error_check_results,
                            wcag_definitions,
                        )
                    ),
                ),
                build_section(
                    name="Initial statement",
                    complete_date=None,
                    fields=[],
                    subsections=(
                        get_initial_statement_test_subsections(
                            case,
                            case_compliance,
                            audit,
                            pages,
                            error_check_results,
                            wcag_definitions,
                        )
                    ),
                ),
                build_section(
                    name="Report QA",
                    complete_date=None,
                    fields=[
                        build_field(
                            case,
                            field_name="report_notes",
                            label="Report notes",
                            data_type="markdown",
                        ),
                    ],
                    subsections=[
                        build_section(
                            name="Report ready for QA",
                            complete_date=case.reporting_details_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="report_review_status",
                                    label="Report ready for QA process?",
                                ),
                            ],
                        ),
                        build_section(
                            name="QA auditor",
                            complete_date=case.qa_auditor_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="reviewer_id",
                                    label="QA Auditor",
                                    display_value=user_names.get(
                                        case.auditor_id, "None"
                                    ),
                                ),
                            ],
                        ),
                        build_section(
                            name="Comments",
                            complete_date=None,
                            fields=[],
                            subsections=get_comment_subsections(comments, user_names),
                        ),
                        build_section(
                            name="QA approval",
                            complete_date=case.qa_approval_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="report_approved_status",
                                    label="Report approved?",
                                ),
                            ],
                        ),
                    ],
                ),
                build_section(
                    name="Contact details",
                    complete_date=None,
                    fields=[],
                    subsections=[
                        build_section(
                            name="Manage contact details",
                            complete_date=case.manage_contact_details_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="contact_notes",
                                    label="Contact detail notes",
                                    data_type="markdown",
                                ),
                            ],
                            subsections=get_contact_subsections(
                                Contact.objects.filter(case=case)
                            ),
                        ),
                    ],
                ),
                build_section(
                    name="Report correspondence",
                    complete_date=None,
                    fields=[
                        build_field(
                            case,
                            field_name="no_psb_contact",
                            label="Public sector body is unresponsive",
                        ),
                        build_field(
                            case,
                            field_name="seven_day_no_contact_email_sent_date",
                            label="Seven day 'no contact details' email sent",
                        ),
                        build_field(
                            case, field_name="report_sent_date", label="Report sent on"
                        ),
                        build_field(
                            case,
                            field_name="report_followup_week_1_due_date",
                            label="1-week followup to report due",
                        ),
                        build_field(
                            case,
                            field_name="report_followup_week_1_sent_date",
                            label="1-week followup to report sent",
                        ),
                        build_field(
                            case,
                            field_name="report_followup_week_4_due_date",
                            label="4-week followup to report due",
                        ),
                        build_field(
                            case,
                            field_name="report_followup_week_4_sent_date",
                            label="4-week followup to report sent",
                        ),
                        build_field(
                            case,
                            field_name="report_acknowledged_date",
                            label="Report acknowledged",
                        ),
                        build_field(
                            case,
                            field_name="correspondence_notes",
                            label="Correspondence notes",
                            data_type="markdown",
                        ),
                    ],
                ),
                build_section(
                    name="12-week correspondence",
                    complete_date=None,
                    fields=[
                        build_field(
                            case,
                            field_name="report_followup_week_12_due_date",
                            label="12-week deadline due",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_update_requested_date",
                            label="12-week update requested",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_1_week_chaser_due_date",
                            label="1-week followup due",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_1_week_chaser_sent_date",
                            label="1-week followup sent",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_correspondence_acknowledged_date",
                            label="12-week update received",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_response_state",
                            label="No response to 12-week deadline",
                        ),
                        build_field(
                            case,
                            field_name="twelve_week_correspondence_notes",
                            label="12-week Correspondence notes",
                        ),
                    ],
                ),
                build_section(
                    name="12-week WCAG test",
                    complete_date=None,
                    fields=[],
                    subsections=(
                        get_12_week_wcag_test_subsections(
                            case,
                            case_compliance,
                            audit,
                            pages,
                            error_check_results,
                            wcag_definitions,
                        )
                    ),
                ),
                build_section(
                    name="12-week statement",
                    complete_date=None,
                    fields=[],
                    subsections=(
                        get_12_week_statement_test_subsections(
                            case,
                            case_compliance,
                            audit,
                            pages,
                            error_check_results,
                            wcag_definitions,
                        )
                    ),
                ),
                build_section(
                    name="Closing the case",
                    complete_date=None,
                    fields=[],
                    subsections=[
                        build_section(
                            name="Reviewing changes",
                            complete_date=case.review_changes_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="retested_website_date",
                                    label="Retested website? (included in equality body export)",
                                ),
                                build_field(
                                    case,
                                    field_name="psb_progress_notes",
                                    label="Summary of progress made from public sector body (included in equality body export)",
                                    data_type="markdown",
                                ),
                                build_field(
                                    case,
                                    field_name="is_ready_for_final_decision",
                                    label="Is this case ready for final decision?",
                                ),
                            ],
                        ),
                        build_section(
                            name="Recommendation",
                            complete_date=case.enforcement_recommendation_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="compliance_email_sent_date",
                                    label="Date when compliance decision email sent to public sector body (included in equality body export)",
                                ),
                                build_field(
                                    case,
                                    field_name="recommendation_for_enforcement",
                                    label="Recommendation for equality body (included in equality body export)",
                                ),
                                build_field(
                                    case,
                                    field_name="recommendation_notes",
                                    label="Enforcement recommendation notes including exemptions (included in equality body export)",
                                    data_type="markdown",
                                ),
                            ],
                        ),
                        build_section(
                            name="Closing the case page",
                            complete_date=case.case_close_complete_date,
                            fields=[
                                build_field(
                                    case,
                                    field_name="case_completed",
                                    label="Case completed",
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        case.archive = json.dumps(
            {
                "version": ARCHIVE_VERSION,
                "archived": datetime.now().isoformat(),
                "sections": sections,
            }
        )
        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.exclude(archive=""):
        archive = json.loads(case.archive)
        if archive["version"] == ARCHIVE_VERSION:
            case.archive = ""
            case.save()


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0007_case_qa_approval_complete_date"),
    ]

    operations = [
        migrations.RunPython(archive_old_fields, reverse_code=reverse_code),
    ]
