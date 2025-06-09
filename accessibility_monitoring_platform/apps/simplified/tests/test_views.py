"""
Tests for cases views
"""

import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from moto import mock_aws
from pytest_django.asserts import assertContains, assertNotContains

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)
from ...audits.tests.test_models import ERROR_NOTES, create_audit_and_check_results
from ...cases.models import EventHistory
from ...comments.models import Comment
from ...common.models import Boolean, EmailTemplate, Sector
from ...common.utils import amp_format_date
from ...exports.csv_export_utils import (
    CASE_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ...notifications.models import Task
from ...reports.models import Report
from ...s3_read_write.models import S3Report
from ..models import (
    CaseCompliance,
    CaseEvent,
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    ZendeskTicket,
)
from ..utils import create_case_and_compliance
from ..views import (
    FOUR_WEEKS_IN_DAYS,
    ONE_WEEK_IN_DAYS,
    TWELVE_WEEKS_IN_DAYS,
    CaseQAApprovalUpdateView,
    calculate_no_contact_chaser_dates,
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
    find_duplicate_cases,
    format_due_date_help_text,
    mark_qa_comments_as_read,
)

CONTACT_NAME: str = "Contact Name"
CONTACT_EMAIL: str = "test@email.com"
DOMAIN: str = "domain.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}"
ORGANISATION_NAME: str = "Organisation name"
REPORT_SENT_DATE: date = date(2021, 2, 28)
UPDATE_REQUESTED_DATE: date = date(2021, 5, 10)
OTHER_DATE: date = date(2020, 12, 31)
ONE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
FOUR_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=FOUR_WEEKS_IN_DAYS
)
TWELVE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=TWELVE_WEEKS_IN_DAYS
)
ONE_WEEK_CHASER_DUE_DATE: date = TWELVE_WEEK_FOLLOWUP_DUE_DATE + timedelta(
    days=ONE_WEEK_IN_DAYS
)
DEACTIVATE_NOTES: str = """I am
a deactivate note,
I am"""
STATEMENT_COMPLIANCE_NOTES: str = "Accessibility Statement note"
TODAY: date = date.today()
DRAFT_REPORT_URL: str = "https://draft-report-url.com"
TRELLO_URL: str = "https://trello.com/board12"
case_feedback_survey_columns_to_export_str: str = ",".join(
    column.column_header for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
)
case_equality_body_columns_to_export_str: str = ",".join(
    column.column_header for column in EQUALITY_BODY_COLUMNS_FOR_EXPORT
)
case_columns_to_export_str: str = ",".join(
    column.column_header for column in CASE_COLUMNS_FOR_EXPORT
)
ACCESSIBILITY_STATEMENT_URL: str = "https://example.com/accessibility-statement"
CONTACT_STATEMENT_URL: str = "https://example.com/contact"
TODAY: date = date.today()
QA_COMMENT_BODY: str = "QA comment body"
CASE_ARCHIVE: list[dict] = {
    "sections": [
        {
            "name": "Archived section one",
            "complete": "2021-10-21",
            "fields": [
                {
                    "name": "archived_date_field_one",
                    "data_type": "date",
                    "label": "Date field",
                    "value": "2021-04-19",
                    "display_value": "19 April 2021",
                },
                {
                    "name": "archived_choice_field",
                    "data_type": "str",
                    "label": "Status field",
                    "value": "case-closed-sent-to-equalities-body",
                    "display_value": "Case closed and sent to equalities body",
                },
            ],
            "subsections": [
                {
                    "name": "Archived subsection a",
                    "complete": None,
                    "fields": [
                        {
                            "name": "archived_datetime_field_one",
                            "data_type": "datetime",
                            "label": "Datetime field",
                            "value": "2023-03-01T13:01:17+00:00",
                            "display_value": "1 March 2023 1:17pm",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Archived section two",
            "complete": None,
            "fields": [
                {
                    "name": "archived_url",
                    "data_type": "link",
                    "label": "Archived URL",
                    "value": "https://www.example.com",
                    "display_value": "www.example.com",
                },
                {
                    "name": "archived_notes",
                    "data_type": "markdown",
                    "label": "Archived notes",
                    "value": "Monitoring suspended - private practice",
                    "display_value": None,
                },
            ],
            "subsections": None,
        },
    ]
}
RESOLVED_EQUALITY_BODY_MESSAGE: str = "Resolved equality body correspondence message"
RESOLVED_EQUALITY_BODY_NOTES: str = "Resolved equality body correspondence notes"
UNRESOLVED_EQUALITY_BODY_MESSAGE: str = (
    "Unresolved equality body correspondence message"
)
UNRESOLVED_EQUALITY_BODY_NOTES: str = "Unresolved equality body correspondence notes"
STATEMENT_CHECK_RESULT_REPORT_COMMENT: str = "Statement check result report comment"
STATEMENT_CHECK_RESULT_RETEST_COMMENT: str = "Statement check result retest comment"
REPORT_ACKNOWLEDGED_WARNING: str = (
    "The report has been acknowledged by the organisation, and no further follow-up is needed."
)
TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING: str = (
    "The request for a final update has been acknowledged by the organisation"
)
RECOMMENDATION_NOTE: str = "Recommendation note"
ZENDESK_URL: str = "https://zendesk.com/ticket"
ZENDESK_SUMMARY: str = "Zendesk ticket summary"
PAGE_LOCATION: str = "Press A and then B"
EXAMPLE_EMAIL_TEMPLATE_ID: int = 4
RETEST_NOTES: str = "Retest notes"
HOME_PAGE_ERROR_NOTES: str = "Home page error note"
STATEMENT_PAGE_ERROR_NOTES: str = "Statement page error note"
OUTSTANDING_ISSUE_NOTES: str = "Outstanding error found."
CORRESPONDENCE_PROCESS_PAGES: list[tuple[str, str]] = [
    ("edit-request-contact-details", "Request contact details"),
    ("edit-one-week-contact-details", "One-week follow-up"),
    ("edit-four-week-contact-details", "Four-week follow-up"),
]


class MockMessages:
    def __init__(self):
        self.messages = []

    def add(self, level: str, message: str, extra_tags: str) -> None:
        self.messages.append((level, message, extra_tags))


def add_user_to_auditor_groups(user: User) -> None:
    auditor_group: Group = Group.objects.create(name="Auditor")
    historic_auditor_group: Group = Group.objects.create(name="Historic auditor")
    qa_auditor_group: Group = Group.objects.create(name="QA auditor")
    auditor_group.user_set.add(user)
    historic_auditor_group.user_set.add(user)
    qa_auditor_group.user_set.add(user)


def test_archived_case_view_case_includes_contents(admin_client):
    """
    Test that the Case overview page for an archived case shows links to sections
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        archive=json.dumps(CASE_ARCHIVE)
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-view-and-search", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<a href="#archived-section-one" class="govuk-link govuk-link--no-visited-state">
        Archived section one <span class="govuk-visually-hidden">complete</span></a>""",
        html=True,
    )
    assertContains(
        response,
        """<a href="#archived-section-two" class="govuk-link govuk-link--no-visited-state">
        Archived section two</a>""",
        html=True,
    )


def test_archived_case_view_case_includes_sections(admin_client):
    """
    Test that the Case overview page for an archived case shows sections and
    subsections.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        archive=json.dumps(CASE_ARCHIVE)
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<h2 id="archived-section-one" class="govuk-heading-m">
            Archived section one
            <span class="govuk-visually-hidden">complete</span>
            ✓
        </h2>""",
        html=True,
    )
    assertContains(
        response,
        """<p id="archived-subsection-a" class="govuk-body-m"><b>Archived subsection a</b></p>""",
        html=True,
    )
    assertContains(
        response,
        """<h2 id="archived-section-two" class="govuk-heading-m">
            Archived section two
        </h2>""",
        html=True,
    )


def test_archived_case_view_case_includes_fields(admin_client):
    """
    Test that the Case overview page for an archived case shows fields
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        archive=json.dumps(CASE_ARCHIVE)
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Date field</th>
            <td class="govuk-table__cell amp-width-one-half">19 April 2021</td>
        </tr>
        """,
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Status field</th>
            <td class="govuk-table__cell amp-width-one-half">Case closed and sent to equalities body</td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Datetime field</th>
            <td class="govuk-table__cell amp-width-one-half">1 March 2023 1:17pm</td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Archived URL</th>
            <td class="govuk-table__cell amp-width-one-half">
                <a href="https://www.example.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    www.example.com
                </a>
            </td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Archived notes</th>
            <td class="govuk-table__cell amp-width-one-half amp-notes">
                 <p>Monitoring suspended - private practice</p>
            </td>
        </tr>""",
        html=True,
    )


def test_archived_case_view_case_includes_post_case_sections(admin_client):
    """
    Test that the Case overview page for an archived case shows expected post case.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        archive=json.dumps(CASE_ARCHIVE), variant=SimplifiedCase.Variant.ARCHIVED
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(response, "Statement enforcement")
    assertContains(response, "Equality body metadata")
    assertContains(response, "Equality body correspondence")
    assertContains(response, "Retest overview")


def test_view_case_includes_tests(admin_client):
    """
    Test that the Case overview displays test and 12-week retest.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(case=case, retest_date=TODAY)

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, "Initial test metadata")
    assertContains(response, "Date of test")
    assertContains(response, "Initial statement compliance decision")

    assertContains(response, "12-week retest metadata")
    assertContains(response, "Date of retest")


def test_view_case_includes_zendesk_tickets(admin_client):
    """
    Test that the Case overview displays Zendesk tickets.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    ZendeskTicket.objects.create(
        simplified_case=case,
        url=ZENDESK_URL,
        summary=ZENDESK_SUMMARY,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, "PSB Zendesk tickets")
    assertContains(response, ZENDESK_URL)
    assertContains(response, ZENDESK_SUMMARY)


def test_case_detail_view_leaves_out_deleted_contact(admin_client):
    """Test that deleted Contacts are not included in context"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Contact.objects.create(
        simplified_case=case,
        name="Undeleted Contact",
    )
    Contact.objects.create(
        simplified_case=case,
        name="Deleted Contact",
        is_deleted=True,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, "Undeleted Contact")
    assertNotContains(response, "Deleted Contact")


def test_case_feedback_survey_export_list_view(admin_client):
    """Test that the case feedback survey export list view returns csv data"""
    response: HttpResponse = admin_client.get(
        reverse("simplified:export-feedback-survey-cases")
    )

    assert response.status_code == 200
    assertContains(response, case_feedback_survey_columns_to_export_str)


def test_case_export_list_view(admin_client):
    """Test that the case export list view returns csv data"""
    response: HttpResponse = admin_client.get(reverse("simplified:case-export-list"))

    assert response.status_code == 200
    assertContains(response, case_columns_to_export_str)


@pytest.mark.parametrize(
    "export_view_name",
    [
        "simplified:case-export-list",
        "simplified:export-feedback-survey-cases",
    ],
)
def test_case_export_view_filters_by_search(export_view_name, admin_client):
    """
    Test that the case exports can be filtered by search from top menu
    """
    included_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name="Included",
        enforcement_body=SimplifiedCase.EnforcementBody.ECNI,
    )
    SimplifiedCase.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse(export_view_name)}?search={included_case.case_number}"
    )

    assert response.status_code == 200
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_export_list_view_respects_filters(admin_client):
    """Test that the case export list view includes only filtered data"""
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)
    SimplifiedCase.objects.create(organisation_name="Included", auditor=user)
    SimplifiedCase.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('simplified:case-export-list')}?auditor={user.id}"
    )

    assert response.status_code == 200
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_deactivate_case_view(admin_client):
    """Test that deactivate case view deactivates the case"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk: dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.post(
        reverse("simplified:deactivate-case", kwargs=case_pk),
        {
            "version": case.version,
            "deactivate_notes": DEACTIVATE_NOTES,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("simplified:case-detail", kwargs=case_pk)

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert case_from_db.is_deactivated
    assert case_from_db.deactivate_date == TODAY
    assert case_from_db.deactivate_notes == DEACTIVATE_NOTES


def test_reactivate_case_view(admin_client):
    """Test that reactivate case view reactivates the case"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk: dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.post(
        reverse("simplified:reactivate-case", kwargs=case_pk),
        {
            "version": case.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("simplified:case-detail", kwargs=case_pk)

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert not case_from_db.is_deactivated


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "simplified:case-create",
            '<h1 class="govuk-heading-xl">Create simplified case</h1>',
        ),
    ],
)
def test_non_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the non-case-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content)


def test_case_page_with_case_nav_and_form_without_go_back(admin_client):
    """
    Test that a case-specific page loads with case-navigation and form
    and without the go back to previous page in browser history widget.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse("simplified:edit-case-metadata", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(
        response,
        f"""<form method="post" action="{url}">""",
    )
    assertContains(response, '<select name="auditor"')
    assertNotContains(response, "Return to previous page")


def test_case_page_with_form_and_go_back_without_case_nav(admin_client):
    """
    Test that a case-specific page loads with a form and without case-navigation or
    the go back to previous page in browser history widget.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse("simplified:edit-no-psb-response", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertNotContains(response, "Case details (0/1)", html=True)
    assertContains(
        response,
        f"""<form method="post" action="{url}">""",
    )
    assertContains(response, "Return to previous page")


def test_case_page_with_go_back_without_form_or_case_nav(admin_client):
    """
    Test that a case-specific page loads without a form or case-navigation but with
    the go back to previous page in browser history widget.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse("simplified:email-template-list", kwargs={"case_id": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertNotContains(response, "Case details (0/1)", html=True)
    assertNotContains(
        response,
        f"""<form method="post" action="{url}">""",
    )
    assertContains(response, "Return to previous page")


def test_case_page_with_case_nav_no_form_and_no_go_back(admin_client):
    """
    Test that a case-specific page loads with case-navigation but no form and no
    go back to previous page in browser history widget.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse("simplified:edit-retest-overview", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertNotContains(
        response,
        f"""<form method="post" action="{url}">""",
    )
    assertNotContains(response, "Return to previous page")


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "simplified:edit-report-ready-for-qa",
            "<b>Report ready for QA</b>",
        ),
        (
            "simplified:edit-qa-auditor",
            "<b>QA auditor</b>",
        ),
        (
            "simplified:edit-qa-comments",
            "<b>Comments (0)</b>",
        ),
        (
            "simplified:edit-qa-approval",
            "<b>QA approval</b>",
        ),
        (
            "simplified:edit-publish-report",
            "<b>Publish report</b>",
        ),
    ],
)
def test_report_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the report-specific view page loads"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, expected_content, html=True)


def test_create_contact_page_loads(admin_client):
    """Test that the create Contact page loads"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-contact-create", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        "<b>Add contact</b>",
        html=True,
    )


def test_update_contact_page_loads(admin_client):
    """Test that the update Contact page loads"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(
        simplified_case=case, name=CONTACT_NAME, email=CONTACT_EMAIL
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-contact-update", kwargs={"pk": contact.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<h1 class="govuk-heading-xl amp-margin-bottom-30">Edit contact {contact}</h1>""",
        html=True,
    )


def test_create_zendesk_ticket_page_loads(admin_client):
    """Test that the create Zendesk ticket page loads"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:create-zendesk-ticket", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h1 class="govuk-heading-xl amp-margin-bottom-30">Add PSB Zendesk ticket</h1>',
        html=True,
    )


def test_update_zendesk_ticket_page_loads(admin_client):
    """Test that the update Zendesk ticket page loads"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(simplified_case=case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h1 class="govuk-heading-xl amp-margin-bottom-30">Edit PSB Zendesk ticket #1</h1>',
        html=True,
    )


def test_create_zendesk_ticket_view(admin_client):
    """Test that the create Zendesk ticket view works"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:create-zendesk-ticket", kwargs={"case_id": case.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(
        simplified_case=case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.CREATE


def test_update_zendesk_ticket_view(admin_client):
    """Test that the update Zendesk ticket view works"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(simplified_case=case)

    response: HttpResponse = admin_client.post(
        reverse("simplified:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(
        simplified_case=case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.UPDATE


def test_confirm_delete_zendesk_ticket_view(admin_client):
    """Test that the confirm delete Zendesk ticket view works"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(simplified_case=case)

    assert zendesk_ticket.is_deleted is False

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:confirm-delete-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}
        ),
        {"is_deleted": True, "delete": "Remove ticket"},
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket_from_db: ZendeskTicket = ZendeskTicket.objects.get(
        id=zendesk_ticket.id
    )

    assert zendesk_ticket_from_db.is_deleted is True

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.UPDATE


def test_create_case_shows_error_messages(admin_client):
    """
    Test that the create case page shows the expected error messages
    """
    response: HttpResponse = admin_client.post(
        reverse("simplified:case-create"),
        {
            "home_page_url": "gov.uk",
            "save_exit": "Save and exit",
        },
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<p class="govuk-error-message">
            <span class="govuk-visually-hidden">Error:</span>
            URL must start with http:// or https://
        </p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-error-message">
            <span class="govuk-visually-hidden">Error:</span>
            Choose which equalities body will check the case
        </p>""",
        html=True,
    )


@pytest.mark.parametrize(
    "button_name, expected_redirect_url",
    [
        (
            "save_continue_case",
            reverse("simplified:edit-case-metadata", kwargs={"pk": 1}),
        ),
        ("save_new_case", reverse("simplified:case-create")),
        ("save_exit", reverse("cases:case-list")),
    ],
)
def test_create_case_redirects_based_on_button_pressed(
    button_name, expected_redirect_url, admin_client
):
    """Test that a successful case create redirects based on the button pressed"""
    response: HttpResponse = admin_client.post(
        reverse("simplified:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


@pytest.mark.django_db
def test_create_case_shows_duplicate_cases(admin_client):
    """Test that create case shows duplicates found"""
    other_url: str = "other_url"
    other_organisation_name: str = "other organisation name"
    SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL,
        organisation_name=other_organisation_name,
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=other_url,
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
        },
    )

    assert response.status_code == 200
    assertContains(response, other_url)
    assertContains(response, other_organisation_name)


@pytest.mark.parametrize(
    "button_name, expected_redirect_url",
    [
        (
            "save_continue_case",
            reverse("simplified:edit-case-metadata", kwargs={"pk": 3}),
        ),
        ("save_new_case", reverse("simplified:case-create")),
        ("save_exit", reverse("cases:case-list")),
    ],
)
@pytest.mark.django_db
def test_create_case_can_create_duplicate_cases(
    button_name, expected_redirect_url, admin_client
):
    """Test that create case can create duplicate cases"""
    SimplifiedCase.objects.create(home_page_url=HOME_PAGE_URL)
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)

    response: HttpResponse = admin_client.post(
        f"{reverse('simplified:case-create')}?allow_duplicate_cases=True",
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


def test_create_case_creates_case_event(admin_client):
    """Test that a successful case create also creates a case event"""
    response: HttpResponse = admin_client.post(
        reverse("simplified:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "save_exit": "Button value",
        },
    )

    assert response.status_code == 302

    case: SimplifiedCase = SimplifiedCase.objects.get(home_page_url=HOME_PAGE_URL)
    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(simplified_case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.CREATE
    assert case_event.message == "Created case"


def test_updating_case_creates_case_event(admin_client):
    """
    Test that updating a case creates a case event
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-review-changes", kwargs={"pk": case.id}),
        {
            "is_ready_for_final_decision": "yes",
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(simplified_case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.READY_FOR_FINAL_DECISION
    assert (
        case_event.message == "Case ready for final decision changed from 'No' to 'Yes'"
    )


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        ("simplified:edit-case-metadata", "save", "simplified:edit-case-metadata"),
        (
            "simplified:edit-case-metadata",
            "save_continue",
            "simplified:edit-test-results",
        ),
        ("simplified:edit-test-results", "save", "simplified:edit-test-results"),
        (
            "simplified:edit-report-ready-for-qa",
            "save",
            "simplified:edit-report-ready-for-qa",
        ),
        (
            "simplified:edit-report-ready-for-qa",
            "save_continue",
            "simplified:edit-qa-auditor",
        ),
        ("simplified:edit-qa-auditor", "save", "simplified:edit-qa-auditor"),
        ("simplified:edit-qa-auditor", "save_continue", "simplified:edit-qa-comments"),
        ("simplified:edit-qa-comments", "save", "simplified:edit-qa-comments"),
        ("simplified:edit-qa-comments", "save_continue", "simplified:edit-qa-approval"),
        ("simplified:edit-qa-approval", "save", "simplified:edit-qa-approval"),
        (
            "simplified:edit-qa-approval",
            "save_continue",
            "simplified:edit-publish-report",
        ),
        (
            "simplified:edit-qa-approval",
            "save_continue",
            "simplified:edit-publish-report",
        ),
        ("simplified:edit-publish-report", "save", "simplified:edit-publish-report"),
        (
            "simplified:edit-publish-report",
            "save_continue",
            "simplified:manage-contact-details",
        ),
        (
            "simplified:manage-contact-details",
            "save",
            "simplified:manage-contact-details",
        ),
        (
            "simplified:manage-contact-details",
            "save_continue",
            "simplified:edit-report-sent-on",
        ),
        (
            "simplified:edit-request-contact-details",
            "save",
            "simplified:edit-request-contact-details",
        ),
        (
            "simplified:edit-request-contact-details",
            "save_continue",
            "simplified:edit-one-week-contact-details",
        ),
        (
            "simplified:edit-one-week-contact-details",
            "save",
            "simplified:edit-one-week-contact-details",
        ),
        (
            "simplified:edit-one-week-contact-details",
            "save_continue",
            "simplified:edit-four-week-contact-details",
        ),
        (
            "simplified:edit-four-week-contact-details",
            "save",
            "simplified:edit-four-week-contact-details",
        ),
        (
            "simplified:edit-four-week-contact-details",
            "save_continue",
            "simplified:edit-report-sent-on",
        ),
        ("simplified:edit-no-psb-response", "save", "simplified:edit-no-psb-response"),
        (
            "simplified:edit-no-psb-response",
            "save_continue",
            "simplified:edit-enforcement-recommendation",
        ),
        ("simplified:edit-report-sent-on", "save", "simplified:edit-report-sent-on"),
        (
            "simplified:edit-report-sent-on",
            "save_continue",
            "simplified:edit-report-one-week-followup",
        ),
        (
            "simplified:edit-report-one-week-followup",
            "save",
            "simplified:edit-report-one-week-followup",
        ),
        (
            "simplified:edit-report-one-week-followup",
            "save_continue",
            "simplified:edit-report-four-week-followup",
        ),
        (
            "simplified:edit-report-four-week-followup",
            "save",
            "simplified:edit-report-four-week-followup",
        ),
        (
            "simplified:edit-report-four-week-followup",
            "save_continue",
            "simplified:edit-report-acknowledged",
        ),
        (
            "simplified:edit-report-acknowledged",
            "save",
            "simplified:edit-report-acknowledged",
        ),
        (
            "simplified:edit-report-acknowledged",
            "save_continue",
            "simplified:edit-12-week-update-requested",
        ),
        (
            "simplified:edit-12-week-update-requested",
            "save",
            "simplified:edit-12-week-update-requested",
        ),
        (
            "simplified:edit-12-week-update-requested",
            "save_continue",
            "simplified:edit-12-week-one-week-followup-final",
        ),
        (
            "simplified:edit-12-week-one-week-followup-final",
            "save",
            "simplified:edit-12-week-one-week-followup-final",
        ),
        (
            "simplified:edit-12-week-one-week-followup-final",
            "save_continue",
            "simplified:edit-12-week-update-request-ack",
        ),
        (
            "simplified:edit-twelve-week-retest",
            "save",
            "simplified:edit-twelve-week-retest",
        ),
        ("simplified:edit-review-changes", "save", "simplified:edit-review-changes"),
        (
            "simplified:edit-review-changes",
            "save_continue",
            "simplified:edit-enforcement-recommendation",
        ),
        (
            "simplified:edit-enforcement-recommendation",
            "save",
            "simplified:edit-enforcement-recommendation",
        ),
        (
            "simplified:edit-enforcement-recommendation",
            "save_continue",
            "simplified:edit-case-close",
        ),
        ("simplified:edit-case-close", "save", "simplified:edit-case-close"),
        (
            "simplified:edit-case-close",
            "save_continue",
            "simplified:edit-statement-enforcement",
        ),
        (
            "simplified:edit-statement-enforcement",
            "save",
            "simplified:edit-statement-enforcement",
        ),
        (
            "simplified:edit-statement-enforcement",
            "save_continue",
            "simplified:edit-equality-body-metadata",
        ),
        (
            "simplified:edit-equality-body-metadata",
            "save",
            "simplified:edit-equality-body-metadata",
        ),
        (
            "simplified:edit-equality-body-metadata",
            "save_continue",
            "simplified:list-equality-body-correspondence",
        ),
    ],
)
def test_platform_case_edit_redirects_based_on_button_pressed(
    case_edit_path,
    button_name,
    expected_redirect_path,
    admin_client,
):
    """
    Test that a successful case update redirects based on the button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "case_completed": "no-decision",
            "version": case.version,
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}'


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        (
            "simplified:edit-12-week-update-request-ack",
            "save",
            "simplified:edit-12-week-update-request-ack",
        ),
        (
            "simplified:edit-12-week-update-request-ack",
            "save_continue",
            "audits:edit-audit-retest-metadata",
        ),
    ],
)
def test_platform_case_with_audit_edit_redirects_based_on_button_pressed(
    case_edit_path,
    button_name,
    expected_redirect_path,
    admin_client,
):
    """
    Test that a successful case with audit update redirects based on the button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(case=case, retest_date=TODAY)

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "case_completed": "no-decision",
            "version": case.version,
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}'


def test_update_request_ack_redirects_when_no_audit(admin_client):
    """
    Test that 12-week update request acknowledged redirects to review changes
    on save and continue when the case has no audit
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-12-week-update-request-ack", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse("simplified:edit-review-changes", kwargs={"pk": case.id})}'
    )


def test_update_request_ack_redirects_when_audit_but_no_retest_date(admin_client):
    """
    Test that 12-week update request acknowledged redirects to review changes
    on save and continue when the case has an audit but retest date is not set
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-12-week-update-request-ack", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse("simplified:edit-twelve-week-retest", kwargs={"pk": case.id})}'
    )


def test_qa_comments_creates_comment(admin_client, admin_user):
    """Test adding a comment using QA comments page"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-qa-comments", kwargs={"pk": case.id}),
        {
            "save": "Button value",
            "version": case.version,
            "body": QA_COMMENT_BODY,
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(case=case)

    assert comment.body == QA_COMMENT_BODY
    assert comment.user == admin_user

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=comment.id
    )

    assert event_history.event_type == EventHistory.Type.CREATE


def test_qa_comments_does_not_create_comment(admin_client, admin_user):
    """Test QA comments page does not create a blank comment"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-qa-comments", kwargs={"pk": case.id}),
        {
            "save": "Button value",
            "version": case.version,
            "body": "",
        },
    )
    assert response.status_code == 302

    assert Comment.objects.filter(case=case).count() == 0


@pytest.mark.django_db
def test_mark_qa_comments_as_read(rf):
    """Test marking QA comments as read"""
    other_user: User = User.objects.create()
    case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME, auditor=other_user
    )
    other_user_qa_comment_reminder: Task = Task.objects.create(
        case=case, user=other_user, type=Task.Type.QA_COMMENT, date=TODAY
    )
    other_user_report_approved_reminder: Task = Task.objects.create(
        case=case, user=other_user, type=Task.Type.REPORT_APPROVED, date=TODAY
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("simplified:mark-qa-comments-as-read", kwargs={"pk": case.id}),
    )
    request.user = request_user
    request._messages = MockMessages()

    qa_comment_reminder: Task = Task.objects.create(
        case=case, user=request_user, type=Task.Type.QA_COMMENT, date=TODAY
    )
    report_approved_reminder: Task = Task.objects.create(
        case=case, user=request_user, type=Task.Type.REPORT_APPROVED, date=TODAY
    )

    response: HttpResponse = mark_qa_comments_as_read(request, pk=case.id)

    assert response.status_code == 302

    assert Task.objects.get(id=other_user_qa_comment_reminder.id).read is False
    assert Task.objects.get(id=other_user_report_approved_reminder.id).read is False

    assert Task.objects.get(id=qa_comment_reminder.id).read is True
    assert Task.objects.get(id=report_approved_reminder.id).read is True

    assert len(request._messages.messages) == 1
    assert request._messages.messages[0][1] == f"{case} comments marked as read"


def test_no_contact_chaser_dates_set(
    admin_client,
):
    """
    Test that updating the no-contact email sent date populates chaser due dates
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    assert case.no_contact_one_week_chaser_due_date is None
    assert case.no_contact_four_week_chaser_due_date is None

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-request-contact-details", kwargs={"pk": case.id}),
        {
            "seven_day_no_contact_email_sent_date_0": TODAY.day,
            "seven_day_no_contact_email_sent_date_1": TODAY.month,
            "seven_day_no_contact_email_sent_date_2": TODAY.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert case_from_db.no_contact_one_week_chaser_due_date is not None
    assert case_from_db.no_contact_four_week_chaser_due_date is not None


def test_link_to_accessibility_statement_displayed(admin_client):
    """
    Test that the link to the accessibility statement is displayed.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=Page.Type.STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        f"""<p class="govuk-body-m">
            <a href="{ACCESSIBILITY_STATEMENT_URL}" target="_blank" class="govuk-link">
                Open accessibility statement page in new tab
            </a>
        </p>""",
        html=True,
    )


def test_statement_page_location_displayed(admin_client):
    """
    Test that the accessibility statement location is displayed.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.STATEMENT,
        url=ACCESSIBILITY_STATEMENT_URL,
        location=PAGE_LOCATION,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_contact_page_location_displayed(admin_client):
    """
    Test that the contact page location is displayed.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.CONTACT,
        url="https://example.com/contact",
        location=PAGE_LOCATION,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_link_to_accessibility_statement_not_displayed(admin_client):
    """
    Test that the link to the accessibility statement is not displayed
    if none has been entered
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "No accessibility statement")


def test_updating_report_sent_date(admin_client):
    """Test that populating the report sent date populates the report followup due dates"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-report-sent-on", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date == ONE_WEEK_FOLLOWUP_DUE_DATE
    assert case_from_db.report_followup_week_4_due_date == FOUR_WEEK_FOLLOWUP_DUE_DATE
    assert (
        case_from_db.report_followup_week_12_due_date == TWELVE_WEEK_FOLLOWUP_DUE_DATE
    )


def test_report_sent_on_warning(admin_client):
    """Test that report sent on page shows warning if case is due to a complaint"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-sent-on", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertNotContains(response, "This case originated from a complaint")

    case.is_complaint = Boolean.YES
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-sent-on", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(response, "This case originated from a complaint")


def test_report_followup_due_dates_changed(admin_client):
    """
    Test that populating the report sent date updates existing report followup due dates
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_1_due_date=OTHER_DATE,
        report_followup_week_4_due_date=OTHER_DATE,
        report_followup_week_12_due_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-report-sent-on", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date != OTHER_DATE
    assert case_from_db.report_followup_week_4_due_date != OTHER_DATE
    assert case_from_db.report_followup_week_12_due_date != OTHER_DATE


def test_report_followup_due_dates_not_changed_if_report_sent_date_already_set(
    admin_client,
):
    """
    Test that updating the report sent date populates report followup due dates
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(report_sent_date=OTHER_DATE)

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-report-sent-on", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date is not None
    assert case_from_db.report_followup_week_4_due_date is not None
    assert case_from_db.report_followup_week_12_due_date is not None


def test_twelve_week_1_week_chaser_due_date_updated(admin_client):
    """
    Test that updating the twelve week update requested date updates the
    twelve week 1 week chaser due date
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        twelve_week_update_requested_date=OTHER_DATE
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-12-week-update-requested", kwargs={"pk": case.id}),
        {
            "twelve_week_update_requested_date_0": UPDATE_REQUESTED_DATE.day,
            "twelve_week_update_requested_date_1": UPDATE_REQUESTED_DATE.month,
            "twelve_week_update_requested_date_2": UPDATE_REQUESTED_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(pk=case.id)

    assert (
        case_from_db.twelve_week_1_week_chaser_due_date
        == UPDATE_REQUESTED_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
    )


def test_case_report_one_week_followup_contains_followup_due_date(admin_client):
    """Test that the case report one week followup view contains the followup due date"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_1_due_date=ONE_WEEK_FOLLOWUP_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(ONE_WEEK_FOLLOWUP_DUE_DATE)}",
    )


def test_case_report_one_week_followup_shows_warning_if_report_ack(admin_client):
    """
    Test that the case report one week followup view shows a warning if the report
    has been acknowledged
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, REPORT_ACKNOWLEDGED_WARNING)

    case.report_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, REPORT_ACKNOWLEDGED_WARNING)


def test_case_report_four_week_followup_contains_followup_due_date(admin_client):
    """Test that the case report four week followup view contains the followup due date"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_4_due_date=FOUR_WEEK_FOLLOWUP_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(FOUR_WEEK_FOLLOWUP_DUE_DATE)}",
    )


def test_case_report_four_week_followup_shows_warning_if_report_ack(admin_client):
    """
    Test that the case report four week followup view shows a warning if the report
    has been acknowledged
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, REPORT_ACKNOWLEDGED_WARNING)

    case.report_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, REPORT_ACKNOWLEDGED_WARNING)


def test_case_report_twelve_week_1_week_chaser_contains_followup_due_date(admin_client):
    """
    Test that the one week followup for final update view contains the one week chaser due date
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        twelve_week_1_week_chaser_due_date=ONE_WEEK_CHASER_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-12-week-one-week-followup-final", kwargs={"pk": case.id}
        )
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(ONE_WEEK_CHASER_DUE_DATE)}",
    )


def test_case_report_twelve_week_1_week_chaser_shows_warning_if_12_week_cores_ack(
    admin_client,
):
    """
    Test that the one week followup for final update view shows a warning if the 12-week
    correspondence has been acknowledged
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-12-week-one-week-followup-final", kwargs={"pk": case.id}
        )
    )

    assert response.status_code == 200

    assertNotContains(response, TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING)

    case.twelve_week_correspondence_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-12-week-one-week-followup-final", kwargs={"pk": case.id}
        )
    )

    assert response.status_code == 200

    assertContains(response, TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING)


def test_no_psb_response_redirects_to_enforcement_recommendation(admin_client):
    """Test no PSB response redirects to enforcement recommendation"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        no_psb_contact=Boolean.YES,
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-no-psb-response", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "no_psb_contact": "on",
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse("simplified:edit-enforcement-recommendation", kwargs={"pk": case.id})}'
    )


@pytest.mark.parametrize(
    "url, domain, expected_number_of_duplicates",
    [
        (HOME_PAGE_URL, ORGANISATION_NAME, 2),
        (HOME_PAGE_URL, "", 1),
        ("https://domain2.com", "Org name", 0),
        ("https://domain2.com", "", 0),
    ],
)
@pytest.mark.django_db
def test_find_duplicate_cases(url, domain, expected_number_of_duplicates):
    """Test find_duplicate_cases returns matching cases"""
    organisation_name_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    domain_case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL
    )

    duplicate_cases: list[SimplifiedCase] = list(find_duplicate_cases(url, domain))

    assert len(duplicate_cases) == expected_number_of_duplicates

    if expected_number_of_duplicates > 0:
        assert duplicate_cases[0] == domain_case

    if expected_number_of_duplicates > 1:
        assert duplicate_cases[1] == organisation_name_case


@pytest.mark.parametrize(
    "case_page_url",
    [
        "simplified:edit-case-metadata",
        "simplified:edit-test-results",
        "simplified:edit-qa-comments",
        "simplified:edit-qa-approval",
        "simplified:edit-publish-report",
        "simplified:manage-contact-details",
        "simplified:edit-contact-create",
        "simplified:edit-request-contact-details",
        "simplified:edit-one-week-contact-details",
        "simplified:edit-four-week-contact-details",
        "simplified:edit-report-sent-on",
        "simplified:edit-report-one-week-followup",
        "simplified:edit-report-four-week-followup",
        "simplified:edit-report-acknowledged",
        "simplified:edit-12-week-update-requested",
        "simplified:edit-12-week-one-week-followup-final",
        "simplified:edit-12-week-update-request-ack",
        "simplified:edit-twelve-week-retest",
        "simplified:edit-review-changes",
        "simplified:edit-enforcement-recommendation",
        "simplified:edit-case-close",
        "simplified:edit-post-case",
        "simplified:status-workflow",
        "simplified:edit-statement-enforcement",
        "simplified:edit-equality-body-metadata",
        "simplified:list-equality-body-correspondence",
        "simplified:create-equality-body-correspondence",
        "simplified:edit-retest-overview",
    ],
)
def test_case_navigation_shown_on_case_pages(case_page_url, admin_client):
    """
    Test that the case navigation sections appear on all case pages
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )

    case_key: str = (
        "case_id"
        if case_page_url
        in [
            "simplified:create-equality-body-correspondence",
            "simplified:create-zendesk-ticket",
            "simplified:edit-contact-create",
        ]
        else "pk"
    )

    response: HttpResponse = admin_client.get(
        reverse(case_page_url, kwargs={case_key: case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/4)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


def test_case_navigation_shown_on_edit_equality_body_cores_page(admin_client):
    """
    Test that the case navigation sections appear on edit equality
    body correspondence page
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/4)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


def test_case_navigation_shown_on_edit_contact_page(admin_client):
    """
    Test that the case navigation sections appear on edit contact page
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    contact: Contact = Contact.objects.create(simplified_case=case)

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-contact-update",
            kwargs={"pk": contact.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/4)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        (
            "simplified:edit-case-metadata",
            "case_details_complete_date",
            "Case metadata",
        ),
        (
            "simplified:edit-request-contact-details",
            "request_contact_details_complete_date",
            "Request contact details",
        ),
        (
            "simplified:edit-one-week-contact-details",
            "one_week_contact_details_complete_date",
            "One-week follow-up",
        ),
        (
            "simplified:edit-four-week-contact-details",
            "four_week_contact_details_complete_date",
            "Four-week follow-up",
        ),
        (
            "simplified:edit-report-sent-on",
            "report_sent_on_complete_date",
            "Report sent on",
        ),
        (
            "simplified:edit-report-one-week-followup",
            "one_week_followup_complete_date",
            "One week follow-up",
        ),
        (
            "simplified:edit-report-four-week-followup",
            "four_week_followup_complete_date",
            "Four week follow-up",
        ),
        (
            "simplified:edit-report-acknowledged",
            "report_acknowledged_complete_date",
            "Report acknowledged",
        ),
        (
            "simplified:edit-12-week-update-requested",
            "twelve_week_update_requested_complete_date",
            "12-week update requested",
        ),
        (
            "simplified:edit-12-week-one-week-followup-final",
            "one_week_followup_final_complete_date",
            "One week follow-up for final update",
        ),
        (
            "simplified:edit-12-week-update-request-ack",
            "twelve_week_update_request_ack_complete_date",
            "12-week update request acknowledged",
        ),
        (
            "simplified:edit-review-changes",
            "review_changes_complete_date",
            "Reviewing changes",
        ),
        (
            "simplified:edit-enforcement-recommendation",
            "enforcement_recommendation_complete_date",
            "Recommendation",
        ),
        ("simplified:edit-case-close", "case_close_complete_date", "Closing the case"),
    ],
)
def test_section_complete_check_displayed_in_nav_details(
    step_url, flag_name, step_name, admin_client
):
    """
    Test that the section complete tick is displayed in list of steps
    when step is complete
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    setattr(case, flag_name, TODAY)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li><b>{step_name}</b>
                <span class="govuk-visually-hidden">complete</span> &check;
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        ("simplified:edit-qa-auditor", "qa_auditor_complete_date", "QA auditor"),
        ("simplified:edit-qa-approval", "qa_approval_complete_date", "QA approval"),
    ],
)
def test_report_section_complete_check_displayed_in_nav_details(
    step_url, flag_name, step_name, admin_client
):
    """
    Test that the report-related section complete tick is displayed in list of steps
    when step is complete
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    setattr(case, flag_name, TODAY)
    case.save()
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li><b>{step_name}</b>
                <span class="govuk-visually-hidden">complete</span> &check;
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        (
            "simplified:edit-publish-report",
            "publish_report_complete_date",
            "Publish report",
        ),
    ],
)
def test_report_with_hidden_subpages_section_complete_check_displayed_in_nav_details(
    step_url, flag_name, step_name, admin_client
):
    """
    Test that the report-related section complete tick is displayed in list of steps
    when step is complete
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    setattr(case, flag_name, TODAY)
    case.save()
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li><b>{step_name}</b>
                <span class="govuk-visually-hidden">complete</span> &check;
                <ul class="amp-nav-list-subpages"> </ul>
        </li>""",
        html=True,
    )


def test_manage_contact_details_page_complete_check_displayed_in_nav_details(
    admin_client,
):
    """
    Test that the Manage contact details complete tick is displayed in list of steps
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        manage_contact_details_complete_date=TODAY
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<li>
            <b>Manage contact details</b>
            <span class="govuk-visually-hidden">complete</span> &check;
            <ul class="amp-nav-list-subpages">
            </ul>
        </li>""",
        html=True,
    )


def test_add_contact_page_in_case_nav_when_current_page(
    admin_client,
):
    """
    Test that the add contact page appears in the case nav
    when it is the current page
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-contact-create", kwargs={"case_id": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<li>
            <a href="/cases/1/manage-contact-details/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">Manage contact details</a>
            <ul class="amp-nav-list-subpages">
                <li class="amp-nav-list-subpages amp-margin-top-5"><b>Add contact</b></li>
            </ul>
        </li>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_link_to_create_test_page_if_none_found(
    admin_client,
):
    """
    Test that the twelve week retest page shows the link to the test results page
    when no test exists on the case.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "This case does not have a test.")

    edit_test_results_url: str = reverse(
        "simplified:edit-test-results", kwargs={"pk": case.id}
    )
    assertContains(
        response,
        f"""<a href="{edit_test_results_url}"
            class="govuk-link govuk-link--no-visited-state">
                testing details
        </a>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_start_retest_button_if_no_retest_exists(
    admin_client,
):
    """
    Test that the twelve week retest page shows start retest button when a
    test exists with no retest.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "This case does not have a retest.")
    assertContains(response, "Click Start retest to move to the testing environment.")

    start_retest_url: str = reverse(
        "audits:audit-retest-start", kwargs={"pk": audit.id}
    )
    assertContains(
        response,
        f"""<a href="{start_retest_url}"
            role="button" draggable="false" class="govuk-button govuk-button--secondary"
            data-module="govuk-button">
            Start retest
        </a>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_if_statement_exists(
    admin_client,
):
    """
    Test that the twelve week retest page shows if statement exists.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case, retest_date=date.today())

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__header amp-width-one-half">Statement exists</th>
            <td class="govuk-table__cell amp-width-one-half">No</td>
        </tr>""",
        html=True,
    )

    StatementPage.objects.create(
        audit=audit, added_stage=StatementPage.AddedStage.TWELVE_WEEK
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__header amp-width-one-half">Statement exists</th>
            <td class="govuk-table__cell amp-width-one-half">Yes</td>
        </tr>""",
        html=True,
    )


def test_case_review_changes_view_contains_no_mention_of_spreadsheet_if_platform_testing(
    admin_client,
):
    """
    Test that the case review changes view contains no mention of the lack of a link
    to the test results if none is on case and the methodology is platform.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-review-changes", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        '<div class="govuk-hint">'
        "There is no test spreadsheet for this case"
        "</div>",
    )


def test_calculate_report_followup_dates():
    """
    Test that the report followup dates are calculated correctly.
    """
    case: SimplifiedCase = SimplifiedCase()
    report_sent_date: date = date(2020, 1, 1)

    updated_case = calculate_report_followup_dates(
        case=case, report_sent_date=report_sent_date
    )

    assert updated_case.report_followup_week_1_due_date == date(2020, 1, 8)
    assert updated_case.report_followup_week_4_due_date == date(2020, 1, 29)
    assert updated_case.report_followup_week_12_due_date == date(2020, 3, 25)


def test_calculate_no_contact_chaser_dates():
    """
    Test that the no contact details chaser dates are calculated correctly.
    """
    case: SimplifiedCase = SimplifiedCase()
    seven_day_no_contact_email_sent_date: date = date(2020, 1, 1)

    updated_case = calculate_no_contact_chaser_dates(
        case=case,
        seven_day_no_contact_email_sent_date=seven_day_no_contact_email_sent_date,
    )

    assert updated_case.no_contact_one_week_chaser_due_date == date(2020, 1, 8)
    assert updated_case.no_contact_four_week_chaser_due_date == date(2020, 1, 29)


def test_calculate_twelve_week_chaser_dates():
    """
    Test that the twelve week chaser dates are calculated correctly.
    """
    case: SimplifiedCase = SimplifiedCase()
    twelve_week_update_requested_date: date = date(2020, 1, 1)

    updated_case = calculate_twelve_week_chaser_dates(
        case=case, twelve_week_update_requested_date=twelve_week_update_requested_date
    )

    assert updated_case.twelve_week_1_week_chaser_due_date == date(2020, 1, 8)


@pytest.mark.parametrize(
    "due_date, expected_help_text",
    [
        (date(2020, 1, 1), "Due 1 January 2020"),
        (None, "None"),
    ],
)
def test_format_due_date_help_text(due_date, expected_help_text):
    """
    Test due date formatting for help text
    """
    assert format_due_date_help_text(due_date) == expected_help_text


@pytest.mark.parametrize(
    "edit_link_label",
    [
        "edit-case-metadata",
        "edit-test-results",
        "edit-qa-approval",
        "edit-publish-report",
        "edit-qa-comments",
        "manage-contact-details",
        "edit-review-changes",
        "edit-case-close",
    ],
)
def test_case_details_shows_edit_links(
    edit_link_label,
    admin_client,
):
    """
    Test case details show edit links when testing methodology is platform.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, edit_link_label)


def test_status_change_message_shown(admin_client):
    """Test updating the case status causes a message to be shown on the next page"""
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)

    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "auditor": user.id,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "version": case.version,
            "save": "Save and continue",
        },
        follow=True,
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<div class="govuk-inset-text">
            Status changed from 'Unassigned case' to 'Test in progress'
        </div>""",
        html=True,
    )


@pytest.mark.django_db
def test_report_approved_notifies_auditor(rf):
    """
    Test approving the report on the QA approval page notifies the auditor
    when the report is approved.
    """
    user: User = User.objects.create()
    case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME, auditor=user
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.post(
        reverse("simplified:edit-qa-approval", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "report_approved_status": SimplifiedCase.ReportApprovedStatus.APPROVED,
            "save": "Button value",
        },
    )
    request.user = request_user

    response: HttpResponse = CaseQAApprovalUpdateView.as_view()(request, pk=case.id)

    assert response.status_code == 302

    task: Task | None = Task.objects.filter(user=user).first()

    assert task is not None
    assert task.description == f"{request_user.get_full_name()} QA approved Case {case}"

    content_type: ContentType = ContentType.objects.get_for_model(Task)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=task.id
    )

    assert event_history.event_type == EventHistory.Type.CREATE


@pytest.mark.django_db
def test_publish_report_no_report(admin_client):
    """
    Test publish report page when not ready to be published
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "To publish this report, you need to:")
    assertContains(response, "Set the report status to <b>Ready to Review</b> in")

    assertNotContains(
        response, "The report is <b>approved</b> and <b>ready for publication</b>."
    )
    assertNotContains(response, 'value="Publish report"')

    assertNotContains(response, "The report is now published and available")
    assertNotContains(response, 'value="Save and continue"')


@pytest.mark.django_db
def test_publish_report_first_time(admin_client):
    """
    Test publish report page when publishing report for first time
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(response, "To publish this report, you need to:")
    assertNotContains(response, "Set the report status to <b>Ready to Review</b> in")

    assertContains(
        response, "The report is <b>approved</b> and <b>ready for publication</b>."
    )
    assertContains(response, 'value="Publish report"')

    assertNotContains(response, "The report is now published and available")
    assertNotContains(response, 'value="Save and continue"')


@mock_aws
def test_publish_report(admin_client):
    """Test publishing a report"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-publish-report", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "create_html_report": "Create HTML report",
        },
        follow=True,
    )

    assert response.status_code == 200

    assertContains(response, "The report is now published and available")


@pytest.mark.django_db
def test_publish_report_already_published(admin_client):
    """
    Test publish report page when report has already been published
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )
    Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(response, "To publish this report, you need to:")
    assertNotContains(response, "Set the report status to <b>Ready to Review</b> in")

    assertNotContains(
        response, "The report is <b>approved</b> and <b>ready for publication</b>."
    )
    assertNotContains(response, 'value="Publish report"')

    assertContains(response, "The report is now published and available")
    assertContains(response, 'value="Save and continue"')


def test_frequently_used_links_displays_trello_url(admin_client):
    """
    Test that the frequently used links are displayed on all edit pages
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url="https://home_page_url.com", trello_url=TRELLO_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-retest-overview", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, TRELLO_URL)


@pytest.mark.django_db
def test_create_case_with_duplicates_shows_previous_url_field(admin_client):
    """
    Test that create case with duplicates found shows URL to previous case field
    """
    SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL,
        organisation_name="other organisation name",
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url="other_url",
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
        },
    )

    assert response.status_code == 200
    assertContains(
        response,
        "If the website has been previously audited, include a link to the case below",
    )


def test_updating_case_create_event(admin_client):
    """Test that updating a case also creates an event"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-case-close", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "case_completed": "no-decision",
            "case_close_complete_date": "on",
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    content_type: ContentType = ContentType.objects.get_for_model(SimplifiedCase)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=case.id
    )

    assert event_history.event_type == EventHistory.Type.UPDATE


def test_update_case_checks_version(admin_client):
    """Test that updating a case shows an error if the version of the case has changed"""
    case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:deactivate-case", kwargs={"pk": case.id}),
        {
            "version": case.version - 1,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {ORGANISATION_NAME} | #S-1 has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_url_name",
    [
        "case-detail",
        "edit-case-metadata",
        "edit-test-results",
        "edit-qa-approval",
        "edit-publish-report",
        "edit-qa-comments",
        "manage-contact-details",
        "edit-twelve-week-retest",
        "edit-review-changes",
        "edit-case-close",
    ],
)
def test_platform_shows_notification_if_fully_compliant(
    edit_url_name,
    admin_client,
):
    """
    Test cases with fully compliant website and accessibility statement show
    notification to that effect on report details page.
    """
    case: SimplifiedCase = create_case_and_compliance(
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
    )

    response: HttpResponse = admin_client.get(
        reverse(f"simplified:{edit_url_name}", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<h3 class="govuk-notification-banner__heading amp-max-width-100">
            The case has a compliant website and a compliant accessibility statement.
        </h3>""",
        html=True,
    )


def test_status_workflow_assign_an_auditor(admin_client, admin_user):
    """
    Test that the status workflow page ticks 'Assign an auditor' only
    when an auditor is assigned.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk_kwargs: dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{reverse('simplified:edit-case-metadata', kwargs=case_pk_kwargs)}"
                class="govuk-link govuk-link--no-visited-state">
                Assign an auditor</a></li>""",
        html=True,
    )

    case.auditor = admin_user
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{reverse('simplified:edit-case-metadata', kwargs=case_pk_kwargs)}"
                class="govuk-link govuk-link--no-visited-state">
                Assign an auditor</a>&check;</li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name,label,field_name,field_value",
    [
        (
            "simplified:edit-no-psb-response",
            "No response from PSB",
            "no_psb_contact",
            Boolean.YES,
        ),
        (
            "simplified:edit-review-changes",
            "Is this case ready for final decision? needs to be Yes",
            "is_ready_for_final_decision",
            Boolean.YES,
        ),
        (
            "simplified:edit-case-close",
            "Case completed requires a decision",
            "case_completed",
            SimplifiedCase.CaseCompleted.COMPLETE_SEND,
        ),
    ],
)
def test_status_workflow_page(path_name, label, field_name, field_value, admin_client):
    """
    Test that the status workflow page ticks its action links
    only when the linked action's value has been set.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk_kwargs: dict[str, int] = {"pk": case.id}
    link_url: str = reverse(path_name, kwargs=case_pk_kwargs)

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    if label == "No response from PSB":
        assertContains(
            response,
            f"""<li> or <a href="{link_url}" class="govuk-link govuk-link--no-visited-state"> {label} </a></li>""",
            html=True,
        )
    else:
        assertContains(
            response,
            f"""<li><a href="{link_url}" class="govuk-link govuk-link--no-visited-state"> {label}</a></li>""",
            html=True,
        )

    setattr(case, field_name, field_value)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    if label == "No response from PSB":
        assertContains(
            response,
            f"""<li> or <a href="{link_url}" class="govuk-link govuk-link--no-visited-state">{label}</a>&check;</li>""",
            html=True,
        )
    else:
        assertContains(
            response,
            f"""<li> <a href="{link_url}" class="govuk-link govuk-link--no-visited-state">{label}</a>&check;</li>""",
            html=True,
        )


def test_status_workflow_links_to_statement_overview(admin_client, admin_user):
    """
    Test that the status workflow page provides a link to the statement overview
    page when the case test uses statement checks. Checkmark set when overview
    statement checks have been entered.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk_kwargs: dict[str, int] = {"pk": case.id}
    audit: Audit = Audit.objects.create(case=case)
    audit_pk_kwargs: dict[str, int] = {"pk": audit.id}

    for statement_check in StatementCheck.objects.all():
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    overview_url: str = reverse(
        "audits:edit-statement-overview", kwargs=audit_pk_kwargs
    )
    assertContains(
        response,
        f"""<li>
            <a href="{overview_url}" class="govuk-link govuk-link--no-visited-state">
                Statement overview not filled in
            </a></li>""",
        html=True,
    )

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{overview_url}" class="govuk-link govuk-link--no-visited-state">
                Statement overview not filled in
            </a>&check;</li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "nav_link_name,nav_link_label",
    [
        (
            "simplified:edit-test-results",
            "Testing details",
        ),
        ("simplified:manage-contact-details", "Manage contact details"),
        (
            "simplified:edit-request-contact-details",
            "Request contact details",
        ),
        (
            "simplified:edit-one-week-contact-details",
            "One-week follow-up",
        ),
        (
            "simplified:edit-four-week-contact-details",
            "Four-week follow-up",
        ),
        ("simplified:edit-report-sent-on", "Report sent on"),
        (
            "simplified:edit-report-one-week-followup",
            "One week follow-up",
        ),
        (
            "simplified:edit-report-four-week-followup",
            "Four week follow-up",
        ),
        (
            "simplified:edit-report-acknowledged",
            "Report acknowledged",
        ),
        (
            "simplified:edit-12-week-update-requested",
            "12-week update requested",
        ),
        (
            "simplified:edit-12-week-one-week-followup-final",
            "One week follow-up for final update",
        ),
        (
            "simplified:edit-12-week-update-request-ack",
            "12-week update request acknowledged",
        ),
        (
            "simplified:edit-review-changes",
            "Reviewing changes",
        ),
    ],
)
def test_navigation_links_shown(
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test case steps' navigation links are shown
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">{nav_link_label}</a>""",
        html=True,
    )


@pytest.mark.parametrize(
    "nav_link_name,nav_link_label",
    [
        (
            "simplified:edit-report-ready-for-qa",
            "Report ready for QA",
        ),
        (
            "simplified:edit-qa-auditor",
            "QA auditor",
        ),
        (
            "simplified:edit-qa-comments",
            "Comments (0)",
        ),
        (
            "simplified:edit-qa-approval",
            "QA approval",
        ),
        (
            "simplified:edit-publish-report",
            "Publish report",
        ),
    ],
)
def test_navigation_links_shown_for_report_pages(
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test case steps' navigation links are shown for report-related pages
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )
    Report.objects.create(case=case)
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">{nav_link_label}</a>""",
        html=True,
    )


def test_outstanding_issues(admin_client):
    """
    Test out standing issues page renders according to URL parameters.
    """
    audit: Audit = create_audit_and_check_results()
    url: str = reverse(
        "simplified:outstanding-issues", kwargs={"pk": audit.simplified_case.id}
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">Page</th>',
        html=True,
    )
    assertContains(response, "Group by page")
    assertNotContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">WCAG issue</th>',
        html=True,
    )
    assertNotContains(response, "Group by WCAG issue")

    response: HttpResponse = admin_client.get(f"{url}?page-view=true")

    assert response.status_code == 200

    assertNotContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">Page</th>',
        html=True,
    )
    assertNotContains(response, "Group by page")
    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">WCAG issue</th>',
        html=True,
    )
    assertContains(response, "Group by WCAG issue")

    response: HttpResponse = admin_client.get(f"{url}?wcag-view=true")

    assert response.status_code == 200

    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">Page</th>',
        html=True,
    )
    assertContains(response, "Group by page")
    assertNotContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">WCAG issue</th>',
        html=True,
    )
    assertNotContains(response, "Group by WCAG issue")


def test_outstanding_issues_new_case(admin_client):
    """
    Test out standing issues page shows placeholder text for case without audit
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse("simplified:outstanding-issues", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "This is a new case and does not have any test data.")


@pytest.mark.parametrize(
    "url_name",
    ["simplified:case-detail", "simplified:edit-case-metadata"],
)
def test_frequently_used_links_displayed(url_name, admin_client):
    """
    Test that the frequently used links are displayed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Outstanding issues")
    assertContains(response, "Email templates")


def test_twelve_week_email_template_contains_issues(admin_client):
    """
    Test twelve week email template contains issues.
    """
    audit: Audit = create_audit_and_check_results()
    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    page.url = "https://example.com"
    page.save()
    Report.objects.create(case=audit.simplified_case)
    email_template: EmailTemplate = EmailTemplate.objects.create(
        template_name="4-12-week-update-request"
    )
    url: str = reverse(
        "simplified:email-template-preview",
        kwargs={"case_id": audit.simplified_case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, ERROR_NOTES)


def test_twelve_week_email_template_contains_no_issues(admin_client):
    """
    Test twelve week email template with no issues contains placeholder text.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    email_template: EmailTemplate = EmailTemplate.objects.create(
        template_name="4-12-week-update-request"
    )
    url: str = reverse(
        "simplified:email-template-preview",
        kwargs={"case_id": audit.simplified_case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "We found no major issues.")


def test_outstanding_issues_are_unfixed_in_email_template_context(admin_client):
    """
    Test outstanding issues (issues_table) contains only unfixed issues
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        notes=OUTSTANDING_ISSUE_NOTES,
    )

    email_template: EmailTemplate = EmailTemplate.objects.create(
        template_name="5a-outstanding-issues-initial-test-notes"
    )
    url: str = reverse(
        "simplified:email-template-preview",
        kwargs={"case_id": audit.simplified_case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, OUTSTANDING_ISSUE_NOTES)

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertNotContains(response, OUTSTANDING_ISSUE_NOTES)


def test_equality_body_correspondence(admin_client):
    """
    Test equality body correspondence page renders according to URL parameters.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    EqualityBodyCorrespondence.objects.create(
        case=case,
        message=RESOLVED_EQUALITY_BODY_MESSAGE,
        notes=RESOLVED_EQUALITY_BODY_NOTES,
        status=EqualityBodyCorrespondence.Status.RESOLVED,
    )
    EqualityBodyCorrespondence.objects.create(
        case=case,
        message=UNRESOLVED_EQUALITY_BODY_MESSAGE,
        notes=UNRESOLVED_EQUALITY_BODY_NOTES,
    )
    url: str = reverse(
        "simplified:list-equality-body-correspondence", kwargs={"pk": case.id}
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, RESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, RESOLVED_EQUALITY_BODY_NOTES)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_NOTES)

    response: HttpResponse = admin_client.get(f"{url}?view=unresolved")

    assert response.status_code == 200

    assertNotContains(response, RESOLVED_EQUALITY_BODY_MESSAGE)
    assertNotContains(response, RESOLVED_EQUALITY_BODY_NOTES)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_NOTES)


def test_equality_body_correspondence_nav_links(admin_client):
    """
    Test equality body correspondence page contains links to to next
    page and parent case.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse(
        "simplified:list-equality-body-correspondence", kwargs={"pk": case.id}
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    retest_overview_url: str = reverse(
        "simplified:edit-retest-overview", kwargs={"pk": case.id}
    )
    case_detail_url: str = reverse("simplified:case-detail", kwargs={"pk": case.id})

    assertContains(
        response,
        f"""<a href="{retest_overview_url}" class="govuk-link govuk-link--no-visited-state">
            Continue to retest overview
        </a>""",
        html=True,
    )
    assertContains(
        response,
        f"""<a href="{case_detail_url}" class="govuk-link govuk-link--no-visited-state">
            Return to view case
        </a>""",
        html=True,
    )


def test_equality_body_correspondence_status_toggle(admin_client):
    """
    Test equality body correspondence page buttons toggles the status
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case,
            message=UNRESOLVED_EQUALITY_BODY_MESSAGE,
            notes=UNRESOLVED_EQUALITY_BODY_NOTES,
        )
    )

    assert (
        equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.UNRESOLVED
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:list-equality-body-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            f"toggle_status_{equality_body_correspondence.id}": "Mark as resolved",
        },
    )

    assert response.status_code == 302

    updated_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(id=equality_body_correspondence.id)
    )

    assert (
        updated_equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.RESOLVED
    )

    response: HttpResponse = admin_client.post(
        reverse("simplified:list-equality-body-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            f"toggle_status_{equality_body_correspondence.id}": "Mark as resolved",
        },
    )

    assert response.status_code == 302

    updated_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(id=equality_body_correspondence.id)
    )

    assert (
        updated_equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.UNRESOLVED
    )


def test_create_equality_body_correspondence_save_return_redirects(admin_client):
    """
    Test that a successful equality body correspondence create redirects
    to list when save_return button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:create-equality-body-correspondence",
            kwargs={"case_id": case.id},
        ),
        {
            "save_return": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "simplified:list-equality-body-correspondence", kwargs={"pk": case.id}
    )


def test_create_equality_body_correspondence_save_redirects(admin_client):
    """
    Test that a successful equality body correspondence create redirects
    to update page when save button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:create-equality-body-correspondence",
            kwargs={"case_id": case.id},
        ),
        {
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(case=case)
    )

    assert response.url == reverse(
        "simplified:edit-equality-body-correspondence",
        kwargs={"pk": equality_body_correspondence.id},
    )


def test_update_equality_body_correspondence_save_return_redirects(admin_client):
    """
    Test that a successful equality body correspondence update redirects
    to list when save_return button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
        {
            "save_return": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "simplified:list-equality-body-correspondence", kwargs={"pk": case.id}
    )


def test_update_equality_body_correspondence_save_redirects(admin_client):
    """
    Test that a successful equality body correspondence update redirects
    to itself when save button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
        {
            "save": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "simplified:edit-equality-body-correspondence",
        kwargs={"pk": equality_body_correspondence.id},
    )


def test_updating_equality_body_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the equality body updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url="https://example.com"
    )
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "enforcement_body": SimplifiedCase.EnforcementBody.ECNI,
            "version": case.version,
            "save": "Button value",
            "home_page_url": "https://example.com",
        },
    )
    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_updating_home_page_url_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the home page URL updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url="https://example.com"
    )
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "home_page_url": "https://example.com/updated",
            "version": case.version,
            "save": "Button value",
            "enforcement_body": SimplifiedCase.EnforcementBody.ECNI,
        },
    )
    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_updating_organisation_name_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the organisation name updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url="https://example.com"
    )
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("simplified:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "organisation_name": "New name",
            "version": case.version,
            "save": "Button value",
            "home_page_url": "https://example.com",
            "enforcement_body": SimplifiedCase.EnforcementBody.ECNI,
        },
    )

    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_case_close(admin_client):
    """
    Test that case close renders as expected:
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL, recommendation_notes=f"* {RECOMMENDATION_NOTE}"
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    # Required columns labelled as such; Missing data labelled as incomplete
    assertContains(response, "Published report | Required and incomplete", html=True)

    # Required data with default value labelled as incomplete
    assertContains(
        response,
        "Enforcement recommendation | Required and incomplete",
        html=True,
    )

    # URL data rendered as link
    assertContains(
        response,
        f"""<a href="{HOME_PAGE_URL}"
            class="govuk-link" target="_blank">
            {HOME_PAGE_URL}</a>""",
        html=True,
    )

    # Edit link label used
    assertContains(
        response,
        """<a href="/cases/1/manage-contact-details/"
            class="govuk-link govuk-link--no-visited-state">
            Go to contact details</a>""",
        html=True,
    )

    # Markdown data rendered as html
    assertContains(response, f"<li>{RECOMMENDATION_NOTE}</li>")

    # Extra label for percentage shown
    assertContains(response, "(Derived from retest results)")


def test_case_close_missing_data(admin_client):
    """
    Test that case close renders as expected when data is missing
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertNotContains(
        response, "All fields are complete and the case can now be closed."
    )

    assertContains(
        response,
        """<li>
            Organisation is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-case-metadata/#id_organisation_name-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Organisation</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Website URL is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-case-metadata/#id_home_page_url-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Website URL</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        "<li>Published report is missing</li>",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Enforcement recommendation is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_recommendation_for_enforcement-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Enforcement recommendation</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Enforcement recommendation notes including exemptions is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_recommendation_notes-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Enforcement recommendation notes including exemptions</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Date when compliance decision email sent to public sector body is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_compliance_email_sent_date-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Date when compliance decision email sent to public sector body</span></a>)</span>
        </li>""",
        html=True,
    )


def test_case_close_no_missing_data(admin_client):
    """
    Test that case close renders as expected when no data is missing
    """
    case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=HOME_PAGE_URL,
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        recommendation_notes=RECOMMENDATION_NOTE,
        compliance_email_sent_date=date.today(),
    )
    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    case.compliance.save()

    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertContains(response, "All fields are complete and the case can now be closed.")


def test_case_overview(admin_client):
    """Test case overview."""
    audit: Audit = create_audit_and_check_results()
    accessibility_statement_page: Page = audit.accessibility_statement_page
    accessibility_statement_page.url = "https://example.com"
    accessibility_statement_page.retest_page_missing_date = TODAY
    accessibility_statement_page.save()
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
        check_result_state=StatementCheckResult.Result.NO,
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": audit.simplified_case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-10 govuk-!-font-size-16">Initial test: 3</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-10 govuk-!-font-size-16">Retest: 3 (0% fixed) (1 deleted page)</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-10 govuk-!-font-size-16">Initial test: 1</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-10 govuk-!-font-size-16">Retest test: No statement found</p>""",
        html=True,
    )


def test_case_email_template_list_view(admin_client):
    """Test case email template list page is rendered"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:email-template-list", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(response, ">Email templates</h1>")


def test_case_email_template_list_view_hides_deleted(admin_client):
    """
    Test case email template list page does not include deleted email
    templates
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.get(
        pk=EXAMPLE_EMAIL_TEMPLATE_ID
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:email-template-list", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(response, email_template.name)

    email_template.is_deleted = True
    email_template.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:email-template-list", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, email_template.name)


def test_case_email_template_preview_view(admin_client):
    """Test case email template list page is rendered"""
    case: SimplifiedCase = SimplifiedCase.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.create(
        template_name="4-12-week-update-request"
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:email-template-preview",
            kwargs={"case_id": case.id, "pk": email_template.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, f">{email_template.name}</h1>")


def test_zendesk_tickets_shown(admin_client):
    """
    Test Zendesk tickets shown in correspondence overview.
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    ZendeskTicket.objects.create(simplified_case=case, summary=ZENDESK_SUMMARY)

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:edit-request-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, ZENDESK_SUMMARY)


def test_enable_correspondence_process(admin_client):
    """Test enabling of correspondence process"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:enable-correspondence-process",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "simplified:edit-request-contact-details",
        kwargs={"pk": case.id},
    )

    case_from_db: SimplifiedCase = SimplifiedCase.objects.get(id=case.id)

    assert case_from_db.enable_correspondence_process is True


def test_enabling_correspondence_process(admin_client):
    """Test enabling of correspondence process pages"""
    case: SimplifiedCase = SimplifiedCase.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:manage-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    for url, label in CORRESPONDENCE_PROCESS_PAGES:
        assertNotContains(
            response,
            f"""<a href="/cases/1/{url}/"
                class="govuk-link govuk-link--no-visited-state govuk-link--no-underline govuk-link--no-underline">
                {label}</a>""",
            html=True,
        )

    case.enable_correspondence_process = True
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(
            "simplified:manage-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    for url, label in CORRESPONDENCE_PROCESS_PAGES:
        assertContains(
            response,
            f"""<a href="/cases/1/{url}/"
                class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                {label}</a>""",
            html=True,
        )


def test_add_contact_details_redirects_correctly(admin_client):
    """
    Test add contact details page redirects based on
    enable_correspondence_process value
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:manage-contact-details",
            kwargs={"pk": case.id},
        ),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "simplified:edit-report-sent-on",
        kwargs={"pk": case.id},
    )

    case.enable_correspondence_process = True
    case.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "simplified:manage-contact-details",
            kwargs={"pk": case.id},
        ),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "simplified:edit-request-contact-details",
        kwargs={"pk": case.id},
    )


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-case-metadata", "Initial test | Testing details"),
        ("manage-contact-details", "Report correspondence | Report sent on"),
        ("edit-no-psb-response", "Closing the case | Recommendation"),
        ("edit-12-week-update-request-ack", "Closing the case | Reviewing changes"),
        ("edit-case-close", "Post case | Statement enforcement"),
    ],
)
def test_next_page_name(path_name, expected_next_page, admin_client):
    """
    Test next page shown for when Save and continue button pressed
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    url: str = reverse(f"simplified:{path_name}", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-case-metadata", "Initial WCAG test | Initial test metadata"),
        (
            "edit-12-week-update-request-ack",
            "12-week WCAG test | 12-week retest metadata",
        ),
    ],
)
def test_next_page_name_with_audit(path_name, expected_next_page, admin_client):
    """
    Test next page shown for when Save and continue button pressed on Case with Audit
    """
    case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(case=case, retest_date=TODAY)
    url: str = reverse(f"simplified:{path_name}", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)
