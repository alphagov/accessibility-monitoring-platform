""" Tests - test for comments template tags """
import pytest
from datetime import datetime
from django.template import Context, Template
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from ...cases.models import Case
from .create_user import create_user


@pytest.mark.django_db
def test_template_tag_renders_correctly():
    """comments_app template tag renders correctly"""
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
    context: Context = Context(
        {
            "case": case,
            "request": request,
        }
    )
    template_to_render: Template = Template(
        "{% load comments %}"
        "{% comments_app request=request case_id=case.id page='qa_process' %}"
    )
    rendered_template: str = template_to_render.render(context)
    assert (
        """<h2 class="govuk-heading-l" id="comments"> Comments </h2>"""
        in rendered_template
    )
