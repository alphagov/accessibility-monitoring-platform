""" Tests - test for comments forms """
import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.handlers.wsgi import WSGIRequest
from ..forms import SubmitCommentForm, EditCommentForm
from ..models import Comments

USER_PASSWORD = "12345"


def create_user() -> User:
    """Creates a user and auto increments the email/username

    Returns:
        User: A user model
    """
    num: int = len(User.objects.all())
    user: User = User.objects.create(
        username=f"user{num}@email.com",
        email=f"user{num}@email.com"
    )
    user.set_password(USER_PASSWORD)
    user.save()
    return user


@pytest.mark.django_db
def test_submit_comment_form_form_valid():
    """SubmitCommentForm returns True when validating valid form"""
    form: SubmitCommentForm = SubmitCommentForm(data={"body": "this is a comment"})
    assert form.is_valid() is True


@pytest.mark.django_db
def test_edit_comment_form_form_valid():
    """EditCommentForm returns True when validating valid form"""
    user0: User = create_user()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0
    form: EditCommentForm = EditCommentForm(
        data={"body": "this is a comment"},
        initial={"request": request},
        instance=Comments(user=user0)
    )
    assert form.is_valid() is True


@pytest.mark.django_db
def test_edit_comment_form_form_invalid():
    """EditCommentForm returns False when validating invalid form"""
    user0: User = create_user()
    user1: User = create_user()

    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0

    form: EditCommentForm = EditCommentForm(
        data={"body": "this is a comment"},
        initial={"request": request},
        instance=Comments(user=user1)
    )

    assert form.is_valid() is False
