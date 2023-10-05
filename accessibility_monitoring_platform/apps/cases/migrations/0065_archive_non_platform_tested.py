"""
    Build object from all the data shown on View case page and store as a JSON string
    in Case.archive.
"""
from datetime import datetime
import json

from django.db import migrations

from ...common.archive_utils import build_field, build_section
from ...common.templatetags.common_tags import amp_datetime


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


def get_comment_subsections(comments, users):
    """Find case comments and return data as subsections"""
    return [
        build_section(
            name=f"Comment by {users.get(comment.user_id, 'None')} on {amp_datetime(comment.created_date)}",
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
    users = {
        user.id: f"{user.first_name} {user.last_name}" for user in User.objects.all()
    }
    Sector = apps.get_model("common", "Sector")
    sectors = {sector.id: sector for sector in Sector.objects.all()}
    Case = apps.get_model("cases", "Case")
    Contact = apps.get_model("cases", "Contact")
    Comment = apps.get_model("comments", "Comment")
    for case in Case.objects.filter(testing_methodology="spreadsheet"):
        comments = Comment.objects.filter(case=case).order_by("-created_date")
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
                        display_value=users.get(case.auditor_id, "None"),
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
                        display_value=sectors.get(case.sector_id).name,
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
                fields=[
                    build_field(
                        case,
                        field_name="test_results_url",
                        label="Link to test results",
                        data_type="link",
                        display_value="Monitor document",
                    ),
                    build_field(case, field_name="test_status", label="Test status"),
                    build_field(
                        case,
                        field_name="accessibility_statement_state",
                        label="Initial accessibility statement decision",
                    ),
                    build_field(
                        case,
                        field_name="accessibility_statement_notes",
                        label="Accessibility statement notes",
                        data_type="markdown",
                    ),
                    build_field(
                        case,
                        field_name="website_compliance_state_initial",
                        label="Initial compliance decision",
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
                        display_value=users.get(case.reviewer_id, "None"),
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
                subsections=get_comment_subsections(comments, users),
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
                        field_name="testing_methodology",
                        label="Testing methodology",
                    ),
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
            {"version": 1, "archived": datetime.now().isoformat(), "sections": sections}
        )
        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.exclude(archive=""):
        archive = json.loads(case.archive)
        case.archive = ""
        case.testing_methodology = "spreadsheet"
        case.test_results_url = archive["sections"][1]["fields"][0]["value"]
        case.test_status = archive["sections"][1]["fields"][1]["value"]
        case.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0064_case_archive"),
    ]

    operations = [
        migrations.RunPython(archive_old_fields, reverse_code=reverse_code),
    ]
