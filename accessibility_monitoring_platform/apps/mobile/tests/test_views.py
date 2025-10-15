"""Tests for mobile views"""

from datetime import date

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...comments.models import Comment
from ...notifications.models import Task
from ..csv_export import (
    MOBILE_CASE_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..models import EventHistory, MobileCase, MobileZendeskTicket
from ..views import mark_qa_comments_as_read

CASE_FOLDER_URL: str = "https://drive.google.com/drive/folders/xxxxxxx"
CASE_FOLDER_LINK: str = f"""
    <a href="{CASE_FOLDER_URL}"
        rel="noreferrer noopener" target="_blank" class="govuk-link">
        Case folder</a>"""
CASE_FOLDER_URL_FIELD_LINK: str = """
    <a href="/mobile/1/case-metadata/#id_case_folder_url-label"
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
            "mobile:case-create",
            '<h1 class="govuk-heading-xl">Create mobile case</h1>',
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
    mobile_case: MobileCase = MobileCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(
            "mobile:case-detail",
            kwargs={"pk": mobile_case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, CASE_FOLDER_URL_FIELD_LINK, html=True)
    assertNotContains(response, CASE_FOLDER_LINK, html=True)

    mobile_case.case_folder_url = CASE_FOLDER_URL
    mobile_case.save()

    response: HttpResponse = admin_client.get(
        reverse(
            "mobile:case-detail",
            kwargs={"pk": mobile_case.id},
        )
    )

    assert response.status_code == 200

    assertNotContains(response, CASE_FOLDER_URL_FIELD_LINK, html=True)
    assertContains(response, CASE_FOLDER_LINK, html=True)


def test_zendesk_tickets_shown(admin_client):
    """
    Test Zendesk tickets shown in correspondence overview.
    """
    mobile_case: MobileCase = MobileCase.objects.create()
    MobileZendeskTicket.objects.create(mobile_case=mobile_case, summary=ZENDESK_SUMMARY)

    response: HttpResponse = admin_client.get(
        reverse(
            "mobile:edit-request-contact-details",
            kwargs={"pk": mobile_case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, ZENDESK_SUMMARY)


def test_create_zendesk_ticket_view(admin_client):
    """Test that the create Zendesk ticket view works"""
    mobile_case: MobileCase = MobileCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("mobile:create-zendesk-ticket", kwargs={"case_id": mobile_case.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/mobile/1/zendesk-tickets/"

    zendesk_ticket: MobileZendeskTicket = MobileZendeskTicket.objects.filter(
        mobile_case=mobile_case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(MobileZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.CREATE


def test_update_zendesk_ticket_view(admin_client):
    """Test that the update Zendesk ticket view works"""
    mobile_case: MobileCase = MobileCase.objects.create()
    zendesk_ticket: MobileZendeskTicket = MobileZendeskTicket.objects.create(
        mobile_case=mobile_case
    )

    response: HttpResponse = admin_client.post(
        reverse("mobile:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/mobile/1/zendesk-tickets/"

    zendesk_ticket: MobileZendeskTicket = MobileZendeskTicket.objects.filter(
        mobile_case=mobile_case
    ).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(MobileZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.UPDATE


def test_confirm_delete_zendesk_ticket_view(admin_client):
    """Test that the confirm delete Zendesk ticket view works"""
    mobile_case: MobileCase = MobileCase.objects.create()
    zendesk_ticket: MobileZendeskTicket = MobileZendeskTicket.objects.create(
        mobile_case=mobile_case
    )

    assert zendesk_ticket.is_deleted is False

    response: HttpResponse = admin_client.post(
        reverse(
            "mobile:confirm-delete-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}
        ),
        {"is_deleted": True, "delete": "Remove ticket"},
    )

    assert response.status_code == 302
    assert response.url == "/mobile/1/zendesk-tickets/"

    zendesk_ticket_from_db: MobileZendeskTicket = MobileZendeskTicket.objects.get(
        id=zendesk_ticket.id
    )

    assert zendesk_ticket_from_db.is_deleted is True

    content_type: ContentType = ContentType.objects.get_for_model(MobileZendeskTicket)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event_history.event_type == EventHistory.Type.UPDATE


def test_unresponsive_psb_save_message(admin_client):
    """Test that a message is shown when the Unresponsive PSB page is saved"""
    mobile_case: MobileCase = MobileCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("mobile:edit-unresponsive-psb", kwargs={"pk": mobile_case.id}),
        {"version": mobile_case.version, "no_psb_contact": True, "save": "Save"},
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
    qa_auditor_group: Group = Group.objects.create(name="QA auditor")
    qa_auditor: User = User.objects.create()
    qa_auditor_group.user_set.add(qa_auditor)
    mobile_case: MobileCase = MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    response: HttpResponse = admin_client.post(
        reverse("mobile:edit-qa-comments", kwargs={"pk": mobile_case.id}),
        {
            "save": "Button value",
            "version": mobile_case.version,
            "body": QA_COMMENT_BODY,
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(base_case=mobile_case)

    assert comment.body == QA_COMMENT_BODY
    assert comment.user == admin_user

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event_history: EventHistory = EventHistory.objects.get(
        content_type=content_type, object_id=comment.id
    )

    assert event_history.event_type == EventHistory.Type.CREATE

    reminder: Task = Task.objects.get(base_case=mobile_case, user=qa_auditor)

    assert reminder.type == Task.Type.QA_COMMENT
    assert (
        reminder.description == f"  left a message in discussion:\n\n{QA_COMMENT_BODY}"
    )


def test_qa_comments_does_not_create_comment(admin_client, admin_user):
    """Test QA comments page does not create a blank comment"""
    mobile_case: MobileCase = MobileCase.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("mobile:edit-qa-comments", kwargs={"pk": mobile_case.id}),
        {
            "save": "Button value",
            "version": mobile_case.version,
            "body": "",
        },
    )
    assert response.status_code == 302

    assert Comment.objects.filter(base_case=mobile_case).count() == 0


@pytest.mark.django_db
def test_mark_qa_comments_as_read(rf):
    """Test marking QA comments as read"""
    other_user: User = User.objects.create()
    mobile_case: MobileCase = MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME, auditor=other_user
    )
    other_user_qa_comment_reminder: Task = Task.objects.create(
        base_case=mobile_case,
        user=other_user,
        type=Task.Type.QA_COMMENT,
        date=TODAY,
    )
    other_user_report_approved_reminder: Task = Task.objects.create(
        base_case=mobile_case,
        user=other_user,
        type=Task.Type.REPORT_APPROVED,
        date=TODAY,
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("mobile:mark-qa-comments-as-read", kwargs={"pk": mobile_case.id}),
    )
    request.user = request_user
    request._messages = MockMessages()

    qa_comment_reminder: Task = Task.objects.create(
        base_case=mobile_case,
        user=request_user,
        type=Task.Type.QA_COMMENT,
        date=TODAY,
    )
    report_approved_reminder: Task = Task.objects.create(
        base_case=mobile_case,
        user=request_user,
        type=Task.Type.REPORT_APPROVED,
        date=TODAY,
    )

    response: HttpResponse = mark_qa_comments_as_read(request, pk=mobile_case.id)

    assert response.status_code == 302

    assert Task.objects.get(id=other_user_qa_comment_reminder.id).read is False
    assert Task.objects.get(id=other_user_report_approved_reminder.id).read is False

    assert Task.objects.get(id=qa_comment_reminder.id).read is True
    assert Task.objects.get(id=report_approved_reminder.id).read is True

    assert len(request._messages.messages) == 1
    assert request._messages.messages[0][1] == f"{mobile_case} comments marked as read"


@pytest.mark.parametrize(
    "columns_for_export, export_url",
    [
        (MOBILE_CASE_COLUMNS_FOR_EXPORT, "mobile:case-export-list"),
        (
            MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
            "mobile:export-equality-body-cases",
        ),
        (
            MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
            "mobile:export-feedback-survey-cases",
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
    mobile_case: MobileCase = MobileCase.objects.create(
        home_page_url=HOME_PAGE_URL, recommendation_info=f"* {RECOMMENDATION_INFO}"
    )

    response: HttpResponse = admin_client.get(
        reverse("mobile:edit-case-close", kwargs={"pk": mobile_case.id}),
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
        """<a href="/mobile/1/manage-contact-details/"
            class="govuk-link govuk-link--no-visited-state">
            Go to contact details</a>""",
        html=True,
    )

    # Markdown data rendered as html
    assertContains(response, f"<li>{RECOMMENDATION_INFO}</li>")


def test_closing_the_case_page_close_missing_data(admin_client):
    """Test that closing the case page renders as expected when data is missing"""
    mobile_case: MobileCase = MobileCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("mobile:edit-case-close", kwargs={"pk": mobile_case.id}),
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
            <a href="/mobile/1/case-metadata/#id_organisation_name-label" class="govuk-link govuk-link--no-visited-state">
            Edit<span class="govuk-visually-hidden"> Organisation</span></a></p>""",
        html=True,
    )


def test_closing_the_case_page_no_missing_data(admin_client):
    """Test that closing the case page renders as expected when no data is missing"""
    mobile_case: MobileCase = MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=HOME_PAGE_URL,
        equality_body_report_url=EQUALITY_BODY_REPORT_URL,
        recommendation_for_enforcement=MobileCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        recommendation_info=RECOMMENDATION_INFO,
        recommendation_decision_sent_date=date.today(),
    )

    response: HttpResponse = admin_client.get(
        reverse("mobile:edit-case-close", kwargs={"pk": mobile_case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertContains(response, "All fields are complete and the case can now be closed.")
