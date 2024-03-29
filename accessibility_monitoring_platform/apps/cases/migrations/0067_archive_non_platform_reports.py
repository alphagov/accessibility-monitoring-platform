# Generated by Django 4.2.4 on 2023-10-11 13:20
"""
    Build object from all the data shown on View case page and store as a JSON string
    in Case.archive for Cases with non-platform reports.
"""
import json
from datetime import datetime

from django.db import migrations

from ...common.archive_utils import build_field, build_section
from ...common.templatetags.common_tags import amp_datetime


def get_audit_subsections(case, audit, pages, error_check_results, wcag_definitions):
    """Find audit and return data as subsections"""
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
            name="Test metadata",
            complete_date=audit.audit_metadata_complete_date,
            fields=[
                build_field(audit, field_name="date_of_test", label="Date of test"),
                build_field(audit, field_name="screen_size", label="Screen size"),
                build_field(audit, field_name="exemptions_state", label="Exemptions?"),
                build_field(audit, field_name="exemptions_notes", label="Notes"),
            ],
        ),
        build_section(
            name="Pages",
            complete_date=audit.audit_pages_complete_date,
            fields=page_fields,
            subsections=page_subsections,
        ),
        build_section(
            name="Website compliance decision",
            complete_date=audit.audit_website_decision_complete_date,
            fields=[
                build_field(
                    case,
                    field_name="website_compliance_state_initial",
                    label="Initial website compliance decision",
                ),
                build_field(
                    case,
                    field_name="compliance_decision_notes",
                    label="Initial website compliance notes",
                    data_type="markdown",
                ),
            ],
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
                build_field(audit, field_name="archive_feedback_notes", label="Notes"),
                build_field(
                    audit,
                    field_name="archive_contact_information_state",
                    label="Contact Information",
                ),
                build_field(
                    audit, field_name="archive_contact_information_notes", label="Notes"
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
                ),
                build_field(
                    audit, field_name="archive_declaration_state", label="Declaration"
                ),
                build_field(
                    audit, field_name="archive_declaration_notes", label="Notes"
                ),
                build_field(
                    audit,
                    field_name="archive_compliance_state",
                    label="Compliance Status",
                ),
                build_field(
                    audit, field_name="archive_compliance_notes", label="Notes"
                ),
                build_field(
                    audit,
                    field_name="archive_non_regulation_state",
                    label="Non-accessible Content - non compliance with regulations",
                ),
                build_field(
                    audit, field_name="archive_non_regulation_notes", label="Notes"
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
                ),
                build_field(
                    audit,
                    field_name="archive_preparation_date_state",
                    label="Preparation Date",
                ),
                build_field(
                    audit, field_name="archive_preparation_date_notes", label="Notes"
                ),
                build_field(audit, field_name="archive_review_state", label="Review"),
                build_field(audit, field_name="archive_review_notes", label="Notes"),
                build_field(audit, field_name="archive_method_state", label="Method"),
                build_field(audit, field_name="archive_method_notes", label="Notes"),
                build_field(
                    audit,
                    field_name="archive_access_requirements_state",
                    label="Access Requirements",
                ),
                build_field(
                    audit, field_name="archive_access_requirements_notes", label="Notes"
                ),
            ],
        ),
        build_section(
            name="Accessibility statement compliance decision",
            complete_date=audit.archive_audit_statement_decision_complete_date,
            fields=[
                build_field(
                    case,
                    field_name="accessibility_statement_state",
                    label="Initial accessibility statement compliance decision",
                ),
                build_field(
                    case,
                    field_name="accessibility_statement_notes",
                    label="Initial accessibility statement compliance notes",
                    data_type="markdown",
                ),
            ],
        ),
        # build_section(
        #     name="Report options",
        #     complete_date=audit.archive_audit_report_options_complete_date,
        #     fields=[
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_state",
        #             label="Accessibility statement",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_not_correct_format",
        #             label="it was not in the correct format",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_not_specific_enough",
        #             label="it was not specific enough",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_missing_accessibility_issues",
        #             label="accessibility issues were found during the test that were not included in the statement",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_missing_mandatory_wording",
        #             label="mandatory wording is missing",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_missing_mandatory_wording_notes",
        #             label="Additional text for mandatory wording",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_needs_more_re_disproportionate",
        #             label="we require more information covering the disproportionate burden claim",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_needs_more_re_accessibility",
        #             label="it required more information detailing the accessibility issues",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_deadline_not_complete",
        #             label="it includes a deadline of XXX for fixing XXX issues and this has not been completed",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_deadline_not_complete_wording",
        #             label="Wording for missed deadline",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_deadline_not_sufficient",
        #             label="it includes a deadline of XXX for fixing XXX issues and this is not sufficient",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_deadline_not_sufficient_wording",
        #             label="Wording for insufficient deadline",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_out_of_date",
        #             label="it is out of date and needs to be reviewed",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_eass_link",
        #             label="it must link directly to the Equality Advisory and Support Service (EASS) website",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_template_update",
        #             label="it is a requirement that accessibility statements are accessible. Some users may experience difficulties using PDF documents. It may be beneficial for users if there was a HTML version of your full accessibility statement.",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_accessible",
        #             label="in 2020 the GOV.UK sample template was updated to include an extra  mandatory piece of information to outline the scope of your accessibility statement. This needs to be added to your statement.",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_prominent",
        #             label="your statement should be prominently placed on the homepage of the website  or made available on every web page, for example in a static header or footer, as per the legislative requirement.",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_accessibility_statement_report_text_wording",
        #             label="Extra wording for report",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_options_next",
        #             label="What to do next",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_next_change_statement",
        #             label="They have an acceptable statement but need to change it because of the errors we found",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_next_no_statement",
        #             label="They don’t have a statement, or it is in the wrong format",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_next_statement_not_right",
        #             label="They have a statement but it is not quite right",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_next_statement_matches",
        #             label="Their statement matches",
        #         ),
        #         build_field(
        #             audit,
        #             field_name="archive_report_next_disproportionate_burden",
        #             label="Disproportionate burden",
        #         ),
        #         build_field(
        #             audit, field_name="archive_report_options_notes", label="Notes"
        #         ),
        #     ],
        # ),
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


def archive_old_fields(apps, schema_editor):  # pylint: disable=unused-argument
    User = apps.get_model("auth", "User")
    user_names = {
        user.id: f"{user.first_name} {user.last_name}" for user in User.objects.all()
    }
    Sector = apps.get_model("common", "Sector")
    sector_names = {sector.id: sector.name for sector in Sector.objects.all()}
    Case = apps.get_model("cases", "Case")
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
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    for case in Case.objects.filter(archive="").filter(report_methodology="odt"):
        comments = Comment.objects.filter(case=case).order_by("-created_date")
        audit = Audit.objects.filter(case=case).first()
        pages = Page.objects.filter(audit=audit).exclude(url="")
        error_check_results = {
            page.id: CheckResult.objects.filter(page=page).filter(
                check_result_state="error"
            )
            for page in pages
        }
        if audit is None:
            print(f"{case} has no audit")
        sections = [
            build_section(
                name="Case details",
                complete_date=case.case_details_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="created",
                        label="Date created",
                        data_type="date",
                    ),
                    build_field(case, field_name="status", label="Status"),
                    build_field(
                        case,
                        field_name="auditor_id",
                        label="Auditor",
                        display_value=user_names.get(case.auditor_id, "None"),
                    ),
                    build_field(
                        case,
                        field_name="home_page_url",
                        label="Full URL",
                        data_type="link",
                    ),
                    build_field(
                        case, field_name="organisation_name", label="Organisation name"
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
                    build_field(case, field_name="is_complaint", label="Complaint?"),
                    build_field(
                        case,
                        field_name="previous_case_url",
                        label="URL to previous case",
                        data_type="link",
                        display_value=case.previous_case_url,
                    ),
                    build_field(
                        case,
                        field_name="trello_url",
                        label="Trello ticket URL",
                        data_type="link",
                        display_value=case.trello_url,
                    ),
                ],
            ),
            build_section(
                name="Testing details",
                complete_date=case.testing_details_complete_date,
                fields=[],
                subsections=get_audit_subsections(
                    case, audit, pages, error_check_results, wcag_definitions
                )
                if audit is not None
                else [],
            ),
            build_section(
                name="Report details",
                complete_date=case.reporting_details_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="report_draft_url",
                        label="Link to report draft",
                        data_type="link",
                        display_value="Report draft",
                    ),
                    build_field(
                        case,
                        field_name="report_notes",
                        label="Report details notes",
                        data_type="markdown",
                    ),
                ],
            ),
            build_section(
                name="QA process",
                complete_date=case.qa_process_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="report_review_status",
                        label="Report ready to be reviewed",
                    ),
                    build_field(
                        case,
                        field_name="reviewer_id",
                        label="QA auditor",
                        display_value=user_names.get(case.reviewer_id, "None"),
                    ),
                    {
                        "name": "qa_comments",
                        "data_type": "str",
                        "label": "Comments",
                        "value": comments.count(),
                        "display_value": comments.count(),
                    },
                    build_field(
                        case,
                        field_name="report_approved_status",
                        label="Report approved?",
                    ),
                    build_field(
                        case,
                        field_name="report_final_odt_url",
                        label="Link to final ODT report",
                        data_type="link",
                        display_value="Final draft (ODT)",
                    ),
                    build_field(
                        case,
                        field_name="report_final_pdf_url",
                        label="Link to final PDF report",
                        data_type="link",
                        display_value="Final draft (PDF)",
                    ),
                ],
                subsections=get_comment_subsections(comments, user_names),
            ),
            build_section(
                name="Contact details",
                complete_date=case.contact_details_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="contact_notes",
                        label="Contact details notes",
                        data_type="markdown",
                    )
                ],
                subsections=get_contact_subsections(Contact.objects.filter(case=case)),
            ),
            build_section(
                name="Report correspondence",
                complete_date=case.reporting_details_complete_date,
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
                        field_name="zendesk_url",
                        label="Zendesk ticket URL",
                        data_type="link",
                        display_value=case.zendesk_url,
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
                complete_date=case.twelve_week_correspondence_complete_date,
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
                name="Reviewing changes",
                complete_date=case.review_changes_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="retested_website_date",
                        label="Retested website?",
                    ),
                    build_field(
                        case,
                        field_name="psb_progress_notes",
                        label="Summary of progress made from public sector body",
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
                name="Final website compliance decision",
                complete_date=case.final_website_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="website_state_final",
                        label="Final website compliance decision",
                    ),
                    build_field(
                        case,
                        field_name="website_state_notes_final",
                        label="Final website compliance decision notes",
                        data_type="markdown",
                    ),
                ],
            ),
            build_section(
                name="Final accessibility statement compliance decision",
                complete_date=case.final_statement_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="is_disproportionate_claimed",
                        label="Disproportionate burden claimed?",
                    ),
                    build_field(
                        case,
                        field_name="disproportionate_notes",
                        label="Disproportionate burden notes",
                        data_type="markdown",
                    ),
                    build_field(
                        case,
                        field_name="accessibility_statement_screenshot_url",
                        label="Link to accessibility statement screenshot",
                        data_type="link",
                    ),
                    build_field(
                        case,
                        field_name="accessibility_statement_state_final",
                        label="Final accessibility statement decision",
                    ),
                    build_field(
                        case,
                        field_name="accessibility_statement_notes_final",
                        label="Final accessibility statement notes",
                        data_type="markdown",
                    ),
                ],
            ),
            build_section(
                name="Closing the case",
                complete_date=case.case_close_complete_date,
                fields=[
                    build_field(
                        case,
                        field_name="compliance_email_sent_date",
                        label="Date when compliance decision email sent to public sector body",
                    ),
                    build_field(
                        case,
                        field_name="recommendation_for_enforcement",
                        label="Recommendation for equality body",
                    ),
                    build_field(
                        case,
                        field_name="recommendation_notes",
                        label="Enforcement recommendation notes including exemptions",
                        data_type="markdown",
                    ),
                    build_field(
                        case, field_name="case_completed", label="Case completed"
                    ),
                ],
            ),
            build_section(
                name="Archived",
                complete_date=None,
                fields=[
                    build_field(
                        case,
                        field_name="report_methodology",
                        label="Report methodology",
                    ),
                    build_field(
                        case, field_name="notes", label="Notes", data_type="markdown"
                    ),
                ],
            ),
        ]
        case.archive = json.dumps(
            {"version": 2, "archived": datetime.now().isoformat(), "sections": sections}
        )
        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.exclude(archive=""):
        archive = json.loads(case.archive)
        if archive["version"] == 2:
            case.archive = ""
            case.report_methodology = "odt"
            case.save()


class Migration(migrations.Migration):
    dependencies = [
        (
            "audits",
            "0032_rename_access_requirements_notes_audit_archive_access_requirements_notes_and_more",
        ),
        ("cases", "0066_remove_case_test_status_and_more"),
    ]

    operations = [
        migrations.RunPython(archive_old_fields, reverse_code=reverse_code),
    ]
