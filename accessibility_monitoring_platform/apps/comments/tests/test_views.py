""" Tests - test for comments view """
import pytest

from typing import Optional

from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.urls import reverse

from pytest_django.asserts import assertContains

from ...cases.models import Case
from ...notifications.models import Notification

from ..models import Comment, CommentHistory
from ..views import save_comment_history, add_comment_notification
from .create_user import create_user, USER_PASSWORD

COMMENT_TEXT: str = "this is a comment"
UPDATED_COMMENT_TEXT: str = "this is an updated comment"
NEWER_COMMENT_TEXT: str = "this is a newer comment"


@pytest.mark.django_db
def test_save_comment_history():
    """Tests if comment history function saves edited comment in CommentHistory"""
    user: User = create_user()
    comment: Comment = Comment(
        user=user,
        page="page",
        body=COMMENT_TEXT,
    )
    comment.save()

    newer_comment: Comment = Comment(
        id=1,
        user=user,
        page="page",
        body=NEWER_COMMENT_TEXT,
    )

    result: bool = save_comment_history(comment=newer_comment)
    assert result

    comment_history: Optional[CommentHistory] = CommentHistory.objects.filter(
        comment=comment
    ).first()
    assert (
        str(comment_history)
        == f"Comment this is a comment was updated to {NEWER_COMMENT_TEXT}"
    )


@pytest.mark.django_db
def test_add_comment_notification(rf):
    """
    Test if add_comment_notification creates a notification.

    Users do not notify themselves so a seond user is required.
    """
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )

    user: User = create_user()
    request: WSGIRequest = rf.get("/")
    request.user = user

    comment_path: str = reverse("cases:edit-qa-process", kwargs={"pk": case.id})  # type: ignore

    comment: Comment = Comment(
        case=case,
        user=user,
        page="edit-qa-process",
        body=COMMENT_TEXT,
        path=comment_path,
    )
    comment.save()

    assert add_comment_notification(request=request, comment=comment)
    assert Notification.objects.count() == 0

    second_user: User = create_user()
    second_request: WSGIRequest = rf.get("/")
    second_request.user = second_user

    second_comment: Comment = Comment(
        case=case,
        user=second_user,
        page="edit-qa-process",
        body="this is a comment by a second user",
        path=comment_path,
    )
    second_comment.save()

    assert add_comment_notification(request=second_request, comment=second_comment)
    assert Notification.objects.count() == 1


@pytest.mark.django_db
def test_comment_create(client):
    """Test creating a comment"""
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user: User = create_user()
    client.login(username=user.username, password=USER_PASSWORD)

    qa_process_response: HttpResponse = client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        )
    )

    assert qa_process_response.status_code == 200

    create_comment_response: HttpResponse = client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": case.id}),  # type: ignore
        data={"body": COMMENT_TEXT},
        follow=True,
    )

    assert create_comment_response.status_code == 200
    assertContains(
        create_comment_response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-15">QA process</h1>""",
    )
    assertContains(create_comment_response, "1 comment")
    assertContains(create_comment_response, COMMENT_TEXT)
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_delete_comment(client):
    """Test deleting a comment"""
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user: User = create_user()
    client.login(username=user.username, password=USER_PASSWORD)

    client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),  # type: ignore
    )

    create_comment_response: HttpResponse = client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": case.id}),  # type: ignore
        data={"body": COMMENT_TEXT},
        follow=True,
    )

    assert create_comment_response.status_code == 200

    comment: Comment = Comment.objects.get(id=1)

    assert not comment.hidden

    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        ),
    )

    delete_comment_response: HttpResponse = client.post(
        reverse(
            "comments:remove-comment",
            kwargs={"pk": 1},  # type: ignore
        ),
        follow=True,
    )

    assert delete_comment_response.status_code == 200
    assertContains(
        delete_comment_response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-15">QA process</h1>""",
    )
    assertContains(delete_comment_response, "0 comments")

    updated_comment: Comment = Comment.objects.get(id=1)

    assert updated_comment.hidden


@pytest.mark.django_db
def test_edit_comment(client):
    """Test for editing comment"""
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user: User = create_user()
    client.login(username=user.username, password=USER_PASSWORD)

    # Posting comment
    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        )
    )
    client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": case.id}),  # type: ignore
        data={"body": COMMENT_TEXT},
        follow=True,
    )

    # Editing comment
    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        )
    )

    edit_comment_response: HttpResponse = client.post(
        reverse("comments:edit-comment", kwargs={"pk": 1}),  # type: ignore
        data={"body": UPDATED_COMMENT_TEXT},
        follow=True,
    )
    assertContains(
        edit_comment_response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-15">QA process</h1>""",
    )
    assertContains(edit_comment_response, "1 comment")
    assertContains(edit_comment_response, UPDATED_COMMENT_TEXT)
    assertContains(edit_comment_response, "Last edited")
    assert Comment.objects.count() == 1
    assert CommentHistory.objects.count() == 1


@pytest.mark.django_db
def test_comment_associated_for_correct_case(client):
    """
    There was a bug whereby new comments were associated with the most recently
    loaded case. This test is to check that that bug has not returned.
    """
    first_case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    latest_case_loaded: Case = Case.objects.create(
        home_page_url="https://www.website2.com",
        organisation_name="org2 name",
    )
    user: User = create_user()
    client.login(username=user.username, password=USER_PASSWORD)

    qa_process_response: HttpResponse = client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": first_case.id},  # type: ignore
        )
    )

    assert qa_process_response.status_code == 200

    more_recent_case_response: HttpResponse = client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": latest_case_loaded.id},  # type: ignore
        )
    )

    assert more_recent_case_response.status_code == 200

    create_comment_response: HttpResponse = client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": first_case.id}),  # type: ignore
        data={"body": COMMENT_TEXT},
        follow=True,
    )

    assert create_comment_response.status_code == 200
    assertContains(
        create_comment_response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-15">QA process</h1>""",
    )
    assertContains(create_comment_response, "1 comment")
    assertContains(create_comment_response, COMMENT_TEXT)
    assert Comment.objects.count() == 1

    Comment.objects.get(case=first_case)
