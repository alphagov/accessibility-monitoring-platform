"""
Tests for cases views
"""

from datetime import date

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...comments.models import Comment
from ...common.models import QA_AUDITOR_GROUP_NAME
from ...detailed.csv_export import (
    DETAILED_CASE_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ...notifications.models import Task
from ..models import (
    DetailedCase,
    DetailedCaseHistory,
    DetailedEventHistory,
    ZendeskTicket,
)
from ..views import mark_qa_comments_as_read

CASE_FOLDER_URL: str = "https://drive.google.com/drive/folders/xxxxxxx"
CASE_FOLDER_LINK: str = f"""
    <a href="{CASE_FOLDER_URL}"
        rel="noreferrer noopener" target="_blank" class="govuk-link">
        Case folder</a>"""
CASE_FOLDER_URL_FIELD_LINK: str = """
    <a href="/detailed/1/case-metadata/#id_case_folder_url-label"
        class="govuk-link govuk-link--no-visited-state">
        Enter case folder URL</a>"""
ZENDESK_SUMMARY: str = "Zendesk ticket summary"
ZENDESK_URL: str = "https://zendesk.com/tickets/1"
TODAY: date = date.today()
QA_COMMENT_BODY: str = "QA comment body"
ORGANISATION_NAME: str = "Organisation name"
HOME_PAGE_URL: str = "https://domain.com"
RECOMMENDATION_INFO: str = "Recommendation note"
EQUALITY_BODY_REPORT_URL: str = "https://eb-report.com"


class MockMessages:
    def __init__(self):
        self.messages = []

    def add(self, level: str, message: str, extra_tags: str) -> None:
        self.messages.append((level, message, extra_tags))


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "detailed:case-create",
            '<h1 class="govuk-heading-xl">Create detailed case</h1>',
        ),
    ],
)
def test_non_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the non-case-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content, html=True)


def test_case_folder_url_shown(admin_client):
    """Test Case folder URL shown in banner when populated."""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(
            "detailed:case-detail",
            kwargs={"pk": detailed_case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, CASE_FOLDER_URL_FIELD_LINK, html=True)
    assertNotContains(response, CASE_FOLDER_LINK, html=True)

    detailed_case.case_folder_url = CASE_FOLDER_URL
    detailed_case.save()

    response: HttpResponse = admin_client.get(
        reverse(
            "detailed:case-detail",
            kwargs={"pk": detailed_case.id},
        )
    )

    assert response.status_code == 200

    assertNotContains(response, CASE_FOLDER_URL_FIELD_LINK, html=True)
    assertContains(response, CASE_FOLDER_LINK, html=True)


def test_zendesk_tickets_shown(admin_client):
    """
    Test Zendesk tickets shown in correspondence overview.
    """
    detailed_case: DetailedCase = DetailedCase.objects.create()
    ZendeskTicket.objects.create(detailed_case=detailed_case, summary=ZENDESK_SUMMARY)

    response: HttpResponse = admin_client.get(
        reverse(
            "detailed:edit-request-contact-details",
            kwargs={"pk": detailed_case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, ZENDESK_SUMMARY)


def test_create_zendesk_ticket_view(admin_client):
    """Test that the create Zendesk ticket view works"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("detailed:create-zendesk-ticket", kwargs={"case_id": detailed_case.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/detailed/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(
        detailed_case=detailed_case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: DetailedEventHistory = DetailedEventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == DetailedEventHistory.Type.CREATE


def test_update_zendesk_ticket_view(admin_client):
    """Test that the update Zendesk ticket view works"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        detailed_case=detailed_case
    )

    response: HttpResponse = admin_client.post(
        reverse("detailed:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/detailed/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(
        detailed_case=detailed_case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: DetailedEventHistory = DetailedEventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == DetailedEventHistory.Type.UPDATE


def test_confirm_delete_zendesk_ticket_view(admin_client):
    """Test that the confirm delete Zendesk ticket view works"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        detailed_case=detailed_case
    )

    assert zendesk_ticket.is_deleted is False

    response: HttpResponse = admin_client.post(
        reverse(
            "detailed:confirm-delete-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}
        ),
        {"is_deleted": True, "delete": "Remove ticket"},
    )

    assert response.status_code == 302
    assert response.url == "/detailed/1/zendesk-tickets/"

    zendesk_ticket_from_db: ZendeskTicket = ZendeskTicket.objects.get(
        id=zendesk_ticket.id
    )

    assert zendesk_ticket_from_db.is_deleted is True

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event_history: DetailedEventHistory = DetailedEventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == DetailedEventHistory.Type.UPDATE


def test_unresponsive_psb_save_message(admin_client):
    """Test that a message is shown when the Unresponsive PSB page is saved"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("detailed:edit-unresponsive-psb", kwargs={"pk": detailed_case.id}),
        {"version": detailed_case.version, "no_psb_contact": True, "save": "Save"},
        follow=True,
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<div class="govuk-inset-text">Page saved</div>""",
        html=True,
    )


def test_qa_comments_creates_comment(admin_client, admin_user):
    """Test adding a comment using QA comments page"""
    qa_auditor_group: Group = Group.objects.create(name=QA_AUDITOR_GROUP_NAME)
    qa_auditor: User = User.objects.create()
    qa_auditor_group.user_set.add(qa_auditor)
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    response: HttpResponse = admin_client.post(
        reverse("detailed:edit-qa-comments", kwargs={"pk": detailed_case.id}),
        {
            "save": "Button value",
            "version": detailed_case.version,
            "body": QA_COMMENT_BODY,
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(base_case=detailed_case)

    assert comment.body == QA_COMMENT_BODY
    assert comment.user == admin_user

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event_history: DetailedEventHistory = DetailedEventHistory.objects.get(
        content_type=content_type, object_id=comment.id
    )

    assert event_history.event_type == DetailedEventHistory.Type.CREATE

    reminder: Task = Task.objects.get(base_case=detailed_case, user=qa_auditor)

    assert reminder.type == Task.Type.QA_COMMENT
    assert (
        reminder.description == f"  left a message in discussion:\n\n{QA_COMMENT_BODY}"
    )


def test_qa_comments_does_not_create_comment(admin_client, admin_user):
    """Test QA comments page does not create a blank comment"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("detailed:edit-qa-comments", kwargs={"pk": detailed_case.id}),
        {
            "save": "Button value",
            "version": detailed_case.version,
            "body": "",
        },
    )
    assert response.status_code == 302

    assert Comment.objects.filter(base_case=detailed_case).count() == 0


@pytest.mark.django_db
def test_mark_qa_comments_as_read(rf):
    """Test marking QA comments as read"""
    other_user: User = User.objects.create()
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME, auditor=other_user
    )
    other_user_qa_comment_reminder: Task = Task.objects.create(
        base_case=detailed_case,
        user=other_user,
        type=Task.Type.QA_COMMENT,
        date=TODAY,
    )
    other_user_report_approved_reminder: Task = Task.objects.create(
        base_case=detailed_case,
        user=other_user,
        type=Task.Type.REPORT_APPROVED,
        date=TODAY,
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("detailed:mark-qa-comments-as-read", kwargs={"pk": detailed_case.id}),
    )
    request.user = request_user
    request._messages = MockMessages()

    qa_comment_reminder: Task = Task.objects.create(
        base_case=detailed_case,
        user=request_user,
        type=Task.Type.QA_COMMENT,
        date=TODAY,
    )
    report_approved_reminder: Task = Task.objects.create(
        base_case=detailed_case,
        user=request_user,
        type=Task.Type.REPORT_APPROVED,
        date=TODAY,
    )

    response: HttpResponse = mark_qa_comments_as_read(request, pk=detailed_case.id)

    assert response.status_code == 302

    assert Task.objects.get(id=other_user_qa_comment_reminder.id).read is False
    assert Task.objects.get(id=other_user_report_approved_reminder.id).read is False

    assert Task.objects.get(id=qa_comment_reminder.id).read is True
    assert Task.objects.get(id=report_approved_reminder.id).read is True

    assert len(request._messages.messages) == 1
    assert (
        request._messages.messages[0][1] == f"{detailed_case} comments marked as read"
    )


@pytest.mark.parametrize(
    "columns_for_export, export_url",
    [
        (DETAILED_CASE_COLUMNS_FOR_EXPORT, "detailed:case-export-list"),
        (
            DETAILED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
            "detailed:export-equality-body-cases",
        ),
        (
            DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
            "detailed:export-feedback-survey-cases",
        ),
    ],
)
def test_case_export_list_view(admin_client, columns_for_export, export_url):
    """Test that the case export list view returns csv data"""
    case_columns_to_export_str: str = ",".join(
        column.column_header for column in columns_for_export
    )
    response: HttpResponse = admin_client.get(reverse(export_url))

    assert response.status_code == 200
    assertContains(response, case_columns_to_export_str)


def test_closing_the_case_page(admin_client):
    """Test that closing the case page renders as expected"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        home_page_url=HOME_PAGE_URL, recommendation_info=f"* {RECOMMENDATION_INFO}"
    )

    response: HttpResponse = admin_client.get(
        reverse("detailed:edit-case-close", kwargs={"pk": detailed_case.id}),
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
        """<a href="/detailed/1/manage-contact-details/"
            class="govuk-link govuk-link--no-visited-state">
            Go to contact details</a>""",
        html=True,
    )

    # Markdown data rendered as html
    assertContains(response, f"<li>{RECOMMENDATION_INFO}</li>")


def test_closing_the_case_page_close_missing_data(admin_client):
    """Test that closing the case page renders as expected when data is missing"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("detailed:edit-case-close", kwargs={"pk": detailed_case.id}),
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
        """<p class="govuk-body-m amp-margin-bottom-5"><b>Organisation | Required and incomplete</b></p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-5">No data available</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m">
            <a href="/detailed/1/case-metadata/#id_organisation_name-label" class="govuk-link govuk-link--no-visited-state">
            Edit<span class="govuk-visually-hidden"> Organisation</span></a></p>""",
        html=True,
    )


def test_closing_the_case_page_no_missing_data(admin_client):
    """Test that closing the case page renders as expected when no data is missing"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=HOME_PAGE_URL,
        equality_body_report_url=EQUALITY_BODY_REPORT_URL,
        recommendation_for_enforcement=DetailedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        recommendation_info=RECOMMENDATION_INFO,
        recommendation_decision_sent_date=date.today(),
    )

    response: HttpResponse = admin_client.get(
        reverse("detailed:edit-case-close", kwargs={"pk": detailed_case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertContains(response, "All fields are complete and the case can now be closed.")


def test_status_update_creates_history(admin_client, admin_user):
    """Test status update adds to history"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    assert DetailedCaseHistory.objects.filter(detailed_case=detailed_case).count() == 0

    response: HttpResponse = admin_client.post(
        reverse("detailed:edit-case-status", kwargs={"pk": detailed_case.id}),
        {
            "save": "Button value",
            "version": detailed_case.version,
            "status": "200-complete",
        },
    )
    assert response.status_code == 302

    assert DetailedCaseHistory.objects.filter(detailed_case=detailed_case).count() == 1


@pytest.mark.parametrize(
    "old_report_sent_date, new_report_sent_date, old_twelve_week_deadline_date, expected_twelve_week_deadline_date",
    [
        (None, None, None, None),
        (None, date(2020, 1, 1), None, date(2020, 3, 25)),
        (None, date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 2)),
        (date(2020, 1, 2), date(2020, 1, 1), None, date(2020, 3, 25)),
        (date(2020, 1, 1), date(2020, 1, 1), None, None),
    ],
)
def test_report_sent_date_populates_12_week_deadline(
    old_report_sent_date,
    new_report_sent_date,
    old_twelve_week_deadline_date,
    expected_twelve_week_deadline_date,
    admin_client,
):
    """Test that populating the report sent date populates the 12-week deadline"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        report_sent_date=old_report_sent_date,
        twelve_week_deadline_date=old_twelve_week_deadline_date,
    )

    if new_report_sent_date:
        new_report_sent_date_day: int = new_report_sent_date.day
        new_report_sent_date_month: int = new_report_sent_date.month
        new_report_sent_date_year: int = new_report_sent_date.year
    else:
        new_report_sent_date_day: str = ""
        new_report_sent_date_month: str = ""
        new_report_sent_date_year: str = ""

    response: HttpResponse = admin_client.post(
        reverse("detailed:edit-report-sent", kwargs={"pk": detailed_case.id}),
        {
            "version": detailed_case.version,
            "report_sent_date_0": new_report_sent_date_day,
            "report_sent_date_1": new_report_sent_date_month,
            "report_sent_date_2": new_report_sent_date_year,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    updated_detailed_case: DetailedCase = DetailedCase.objects.get(id=detailed_case.id)

    assert (
        updated_detailed_case.twelve_week_deadline_date
        == expected_twelve_week_deadline_date
    )
