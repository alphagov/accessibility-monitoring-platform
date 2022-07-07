""" Tests - test for comments forms """
import pytest

from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest

from ..forms import SubmitCommentForm, EditCommentForm
from ..models import Comment

from .create_user import create_user


@pytest.mark.django_db
def test_submit_comment_form_form_valid():
    """SubmitCommentForm returns True when validating valid form"""
    form: SubmitCommentForm = SubmitCommentForm(data={"body": "this is a comment"})
    assert form.is_valid() is True


@pytest.mark.django_db
def test_edit_comment_form_form_valid(rf):
    """EditCommentForm returns True when validating valid form"""
    user: User = create_user()
    request: WSGIRequest = rf.get("/")
    request.user = user
    form: EditCommentForm = EditCommentForm(
        data={"body": "this is a comment"},
        initial={"request": request},
        instance=Comment(user=user),
    )
    assert form.is_valid() is True


@pytest.mark.django_db
def test_edit_comment_form_form_invalid(rf):
    """EditCommentForm returns False when validating invalid form"""
    user0: User = create_user()
    user1: User = create_user()

    request: WSGIRequest = rf.get("/")
    request.user = user0

    form: EditCommentForm = EditCommentForm(
        data={"body": "this is a comment"},
        initial={"request": request},
        instance=Comment(user=user1),
    )

    assert form.is_valid() is False
