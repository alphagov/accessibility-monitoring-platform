""" Tests - test for notifications template tags """
import pytest

from django.template import Context, Template
from django.http import HttpRequest
from django.contrib.auth.models import User

from ..models import Notification


@pytest.mark.django_db
def test_template_tag_read_notification_renders_correctly(rf):
    """
    Tests to see if template tag read_notification marks a notification as read
    """
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user

    notification: Notification = Notification.objects.create(
        user=user, body="this is a notification", path=request.path
    )
    assert not notification.read

    context: Context = Context({"request": request})
    template_to_render = Template(
        "{% load notifications %}" "{% read_notification request=request %}"
    )
    template_to_render.render(context)

    notification_on_db: Notification = Notification.objects.get(id=notification.id)  # type: ignore

    assert notification_on_db.read
