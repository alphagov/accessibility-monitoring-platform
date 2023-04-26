"""
Tests for comments views
"""
import pytest

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import Case
from ...common.models import (
    Event,
    EVENT_TYPE_MODEL_UPDATE,
)

from ..models import Comment


@pytest.mark.parametrize(
    "comment_edit_path, button_name, expected_redirect_path",
    [
        ("comments:edit-qa-comment", "save_return", "cases:edit-qa-process"),
        ("comments:edit-qa-comment", "remove_comment", "cases:edit-qa-process"),
    ],
)
def test_edit_qa_comment_redirects_based_on_button_pressed(
    comment_edit_path,
    button_name,
    expected_redirect_path,
    admin_client,
):
    """
    Test that a successful case update redirects based on the button pressed
    when the case testing methodology is platform
    """
    case: Case = Case.objects.create()
    user: User = User.objects.create(first_name="Joe", last_name="Bloggs")
    comment: Comment = Comment.objects.create(case=case, user=user)

    response: HttpResponse = admin_client.post(
        reverse(comment_edit_path, kwargs={"pk": comment.id}),
        {
            button_name: "Button value",
            "body": "new body text",
        },
    )
    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}?discussion=open#qa-discussion'
    )

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event: Event = Event.objects.get(content_type=content_type, object_id=comment.id)

    assert event.type == EVENT_TYPE_MODEL_UPDATE


def test_qa_comment_removal(admin_client, admin_user):
    """Test removing QA comment by hiding it"""
    case: Case = Case.objects.create()
    comment: Comment = Comment.objects.create(case=case, user=admin_user)

    response: HttpResponse = admin_client.post(
        reverse("comments:edit-qa-comment", kwargs={"pk": case.id}),
        {
            "remove_comment": "Button value",
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(case=case)

    assert comment.hidden is True


def test_qa_comment_removal_not_allowed(admin_client):
    """Test other users cannot hide QA comment"""
    case: Case = Case.objects.create()
    user: User = User.objects.create(first_name="Joe", last_name="Bloggs")
    comment: Comment = Comment.objects.create(case=case, user=user)

    response: HttpResponse = admin_client.post(
        reverse("comments:edit-qa-comment", kwargs={"pk": case.id}),
        {
            "remove_comment": "Button value",
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(case=case)

    assert comment.hidden is False
