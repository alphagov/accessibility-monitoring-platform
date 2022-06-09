""" Tests - test for notifications template tags """
import pytest
from datetime import datetime
from django.template import Context, Template
from django.test import RequestFactory
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.models import User
from ..models import Notification
from .create_user import create_user


@pytest.mark.django_db
def test_template_tag_notifications_count_renders_correctly():
    """Tests to check whether template tag notifications_count returns the correct number of unread notifications"""
    user0: User = create_user()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0

    context: Context = Context({"request": request})
    template_to_render: Template = Template(
        "{% load notifications %}" "{% notifications_count request=request %}"
    )
    rendered_template: str = template_to_render.render(context)
    assert "0" in rendered_template

    Notification(
        user=user0, body="this is a notification", created_date=datetime.now()
    ).save()
    context: Context = Context({"request": request})
    template_to_render: Template = Template(
        "{% load notifications %}" "{% notifications_count request=request %}"
    )
    rendered_template: str = template_to_render.render(context)
    assert "1" in rendered_template


@pytest.mark.django_db
def test_template_tag_read_notification_renders_correctly():
    """Tests to see if template tag read_notification marks a notification as read"""
    user0: User = create_user()
    Notification(
        user=user0,
        body="this is a notification",
        created_date=datetime.now(),
        path="/",
    ).save()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0

    context: Context = Context({"request": request})
    template_to_render = Template(
        "{% load notifications %}" "{% read_notification request=request %}"
    )
    template_to_render.render(context)

    notification: Notification = Notification.objects.get(id=1)
    assert notification.read is True
