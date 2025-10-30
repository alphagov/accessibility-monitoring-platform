"""
Tests for comments views
"""

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...detailed.models import DetailedCase
from ...mobile.models import MobileCase
from ...reports.models import Report
from ...simplified.models import SimplifiedCase
from ..models import Comment


@pytest.mark.parametrize(
    "case_model_class, comment_edit_path, button_name, expected_redirect_path",
    [
        (
            DetailedCase,
            "comments:edit-qa-comment-detailed",
            "save_return",
            "detailed:edit-qa-comments",
        ),
        (
            DetailedCase,
            "comments:edit-qa-comment-detailed",
            "remove_comment",
            "detailed:edit-qa-comments",
        ),
        (
            MobileCase,
            "comments:edit-qa-comment-mobile",
            "save_return",
            "mobile:edit-qa-comments",
        ),
        (
            MobileCase,
            "comments:edit-qa-comment-mobile",
            "remove_comment",
            "mobile:edit-qa-comments",
        ),
        (
            SimplifiedCase,
            "comments:edit-qa-comment-simplified",
            "save_return",
            "simplified:edit-qa-comments",
        ),
        (
            SimplifiedCase,
            "comments:edit-qa-comment-simplified",
            "remove_comment",
            "simplified:edit-qa-comments",
        ),
    ],
)
def test_edit_qa_comment_redirects_based_on_button_pressed(
    case_model_class,
    comment_edit_path,
    button_name,
    expected_redirect_path,
    admin_client,
):
    """
    Test that a successful case update redirects based on the button pressed
    and the type of case.
    """
    case: DetailedCase | MobileCase | SimplifiedCase = case_model_class.objects.create()
    user: User = User.objects.create(first_name="Joe", last_name="Bloggs")
    comment: Comment = Comment.objects.create(base_case=case, user=user)

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
        == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}?#qa-discussion'
    )


def test_qa_comment_removal(admin_client, admin_user):
    """Test removing QA comment by hiding it"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    comment: Comment = Comment.objects.create(
        base_case=simplified_case, user=admin_user
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "comments:edit-qa-comment-simplified", kwargs={"pk": simplified_case.id}
        ),
        {
            "remove_comment": "Button value",
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(base_case=simplified_case)

    assert comment.hidden is True


def test_qa_comment_removal_not_allowed(admin_client):
    """Test other users cannot hide QA comment"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create(first_name="Joe", last_name="Bloggs")
    comment: Comment = Comment.objects.create(base_case=simplified_case, user=user)

    response: HttpResponse = admin_client.post(
        reverse(
            "comments:edit-qa-comment-simplified", kwargs={"pk": simplified_case.id}
        ),
        {
            "remove_comment": "Button value",
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(base_case=simplified_case)

    assert comment.hidden is False


def test_edit_qa_comment_appears_in_case_nav(admin_client, admin_user):
    """Test edit or delete comment page appears in case navigation"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Report.objects.create(base_case=simplified_case)
    comment: Comment = Comment.objects.create(
        base_case=simplified_case, user=admin_user
    )

    response: HttpResponse = admin_client.get(
        reverse("comments:edit-qa-comment-simplified", kwargs={"pk": comment.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<ul class="amp-nav-list-subpages">
            <li class="amp-nav-list-subpages amp-margin-top-5">
                <b>Edit or delete comment</b>
            </li>
        </ul>""",
        html=True,
    )
