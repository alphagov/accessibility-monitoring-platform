""" Tests - test for comments view """
import pytest
from pytest_django.asserts import assertContains
from datetime import datetime

from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.test import RequestFactory, Client
from django.urls import reverse

from ...cases.models import Case
from ...notifications.models import Notification

from ..models import Comment, CommentHistory
from ..views import save_comment_history, add_comment_notification
from .create_user import create_user, USER_PASSWORD


@pytest.mark.django_db
def test_save_comment_history():
    """Tests if comment history function saves edited comment in CommentHistory"""
    user0: User = create_user()
    comment: Comment = Comment(
        user=user0,
        page="page",
        body="this is a comment",
        created_date=datetime.now(),
    )
    comment.save()

    comment2: Comment = Comment(
        id=1,
        user=user0,
        page="page",
        body="this is a newer comment",
        created_date=datetime.now(),
    )

    res: bool = save_comment_history(comment=comment2)
    assert res is True

    comment_history: CommentHistory = CommentHistory.objects.get(id=1)
    assert (
        str(comment_history)
        == "Comment this is a comment was updated to this is a newer comment"
    )


@pytest.mark.django_db
def test_add_comment_notification(rf):
    """Test if add_comment_notification creates a notification"""
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )

    user0: User = create_user()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0

    comment_path: str = (reverse("cases:edit-qa-process", kwargs={"pk": case.id}),)  # type: ignore

    comment: Comment = Comment(
        case=case,
        user=user0,
        page="edit-qa-process",
        body="this is a comment",
        created_date=datetime.now(),
        path=comment_path,
    )
    comment.save()
    res: bool = add_comment_notification(request=request, comment=comment)
    assert res is True

    user1: User = create_user()
    request2: WSGIRequest = rf.get("/")
    request2.user = user1

    comment2: Comment = Comment(
        case=case,
        user=user1,
        page="edit-qa-process",
        body="this is a comment by a second user",
        created_date=datetime.now(),
        path=comment_path,
    )
    comment2.save()

    res: bool = add_comment_notification(request=request2, comment=comment2)
    assert res is True
    assert len(Notification.objects.all()) == 1


@pytest.mark.django_db
def test_post_comment():
    """Test to post comment"""
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user0: User = create_user()
    client: Client = Client()
    client.login(username=user0.username, password=USER_PASSWORD)

    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        )
    )
    response: HttpResponse = client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": case.id}),  # type: ignore
        data={"body": "this is a comment"},
        follow=True,
    )
    assert response.status_code == 200
    assertContains(
        response,
        """<h1 class="govuk-heading-xl" style="margin-bottom:15px">QA process</h1>""",
    )
    assertContains(response, "1 comment")
    assertContains(response, "this is a comment")
    assert len(Comment.objects.all()) == 1


@pytest.mark.django_db
def test_delete_comment():
    """Test to delete comment"""
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user0: User = create_user()
    client: Client = Client()
    client.login(username=user0.username, password=USER_PASSWORD)
    client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),  # type: ignore
    )
    response: HttpResponse = client.post(
        reverse("comments:create-case-comment", kwargs={"case_id": case.id}),  # type: ignore
        data={"body": "this is a comment"},
        follow=True,
    )
    assert response.status_code == 200
    assert Comment.objects.get(id=1).hidden is False

    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        ),
    )
    response: HttpResponse = client.post(
        reverse(
            "comments:remove-comment",
            kwargs={"pk": 1},  # type: ignore
        ),
        follow=True,
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<h1 class="govuk-heading-xl" style="margin-bottom:15px">QA process</h1>""",
    )
    assertContains(response, "0 comments")
    assert Comment.objects.get(id=1).hidden is True


@pytest.mark.django_db
def test_edit_comment():
    """Test for editing comment"""
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user: User = create_user()
    client: Client = Client()
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
        data={"body": "this is a comment"},
        follow=True,
    )

    # Editing comment
    client.get(
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id},  # type: ignore
        )
    )
    response: HttpResponse = client.post(
        reverse("comments:edit-comment", kwargs={"pk": 1}),  # type: ignore
        data={"body": "this is an updated comment"},
        follow=True,
    )
    assertContains(
        response,
        """<h1 class="govuk-heading-xl" style="margin-bottom:15px">QA process</h1>""",
    )
    assertContains(response, "1 comment")
    assertContains(response, "this is an updated comment")
    assertContains(response, "Last edited")
    assert len(Comment.objects.all()) == 1
    assert len(CommentHistory.objects.all()) == 1
