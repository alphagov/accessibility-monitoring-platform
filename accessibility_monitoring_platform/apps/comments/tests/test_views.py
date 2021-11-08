""" Tests - test for comments view """
import pytest
from pytest_django.asserts import assertContains
from datetime import datetime
from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from ..models import Comments, CommentsHistory
from ...cases.models import Case
from ...notifications.models import Notifications
from ..views import save_comment_history, add_comment_notification
from .create_user import create_user, USER_PASSWORD


@pytest.mark.django_db
def test_save_comment_history():
    """Tests if comment history function saves edited comments in CommentsHistory"""
    user0: User = create_user()
    comment: Comments = Comments(
        user=user0,
        page="page",
        body="this is a comment",
        created_date=datetime.now(),
    )
    comment.save()

    comment2: Comments = Comments(
        id=1,
        user=user0,
        page="page",
        body="this is a newer comment",
        created_date=datetime.now(),
    )

    res: bool = save_comment_history(obj=comment2)
    assert res is True

    comment_history: CommentsHistory = CommentsHistory.objects.get(id=1)
    assert str(comment_history) == "Comment this is a comment was updated to this is a newer comment"


@pytest.mark.django_db
def test_add_comment_notification():
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

    middleware: SessionMiddleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    request.session["comment_path"] = "/cases/1/edit-qa-process/"

    comment: Comments = Comments(
        case=case,
        user=user0,
        page="edit-qa-process",
        body="this is a comment",
        created_date=datetime.now(),
        path=request.session["comment_path"]
    )
    comment.save()
    res: bool = add_comment_notification(request=request, obj=comment)
    assert res is True

    user1: User = create_user()
    factory: RequestFactory = RequestFactory()
    request2: WSGIRequest = factory.get("/")
    request2.user = user1

    middleware: SessionMiddleware = SessionMiddleware()
    middleware.process_request(request2)
    request2.session.save()
    request2.session["comment_path"] = "/cases/1/edit-qa-process/"

    comment2: Comments = Comments(
        case=case,
        user=user1,
        page="edit-qa-process",
        body="this is a comment by a second user",
        created_date=datetime.now(),
        path=request2.session["comment_path"]
    )
    comment2.save()

    res: bool = add_comment_notification(request=request2, obj=comment2)
    assert res is True
    assert len(Notifications.objects.all()) == 1


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
        reverse("comments:post-comment"),  # type: ignore
        data={"body": "this is a comment"},
        follow=True
    )
    assert response.status_code == 200
    assertContains(response, """<h1 class="govuk-heading-xl" style="margin-bottom:15px">Edit case | QA process</h1>""")
    assertContains(response, "1 comment")
    assertContains(response, "this is a comment")
    assert len(Comments.objects.all()) == 1


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
        reverse(
            "cases:edit-qa-process",
            kwargs={"pk": case.id}  # type: ignore
        ),
    )
    response: HttpResponse = client.post(
        reverse("comments:post-comment"),  # type: ignore
        data={"body": "this is a comment"},
        follow=True
    )
    assert response.status_code == 200
    assert Comments.objects.get(id=1).hidden is False

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
        follow=True
    )

    assert response.status_code == 200
    assertContains(response, """<h1 class="govuk-heading-xl" style="margin-bottom:15px">Edit case | QA process</h1>""")
    assertContains(response, "0 comments")
    assert Comments.objects.get(id=1).hidden is True


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
        reverse("comments:post-comment"),  # type: ignore
        data={"body": "this is a comment"},
        follow=True
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
        follow=True
    )
    assertContains(response, """<h1 class="govuk-heading-xl" style="margin-bottom:15px">Edit case | QA process</h1>""")
    assertContains(response, "1 comment")
    assertContains(response, "this is an updated comment")
    assertContains(response, "Last edited")
    assert len(Comments.objects.all()) == 1
    assert len(CommentsHistory.objects.all()) == 1
