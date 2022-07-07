""" Tests - test for comments template tags """
import pytest
from datetime import datetime

from django.template import Context, Template
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest

from ...cases.models import Case
from .create_user import create_user


@pytest.mark.django_db
def test_template_tag_renders_correctly(rf):
    """comments_app template tag renders correctly"""
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    user: User = create_user()
    request: WSGIRequest = rf.get("/")
    request.user = user
    context: Context = Context(
        {
            "case": case,
            "request": request,
        }
    )
    template_to_render: Template = Template(
        "{% load comments %}" "{% comments_app request=request case=case %}"
    )
    rendered_template: str = template_to_render.render(context)
    assert (
        """<h2 class="govuk-heading-l" id="comments"> Comments </h2>"""
        in rendered_template
    )
