"""
Test utility functions of cases app
"""

import pytest
from django.contrib.auth.models import User
from django.urls import URLResolver, resolve, reverse

from ...audits.models import Audit, Page, Retest, RetestPage
from ...cases.models import Case
from ...common.models import EmailTemplate
from ..page_name_utils import AmpPage, PageName, get_amp_page_name_by_url

EMAIL_TEMPLATE_NAME: str = "1c. Template name"


def test_page_name_literal():
    """Test PageName class returns expected name string"""
    page_name: PageName = PageName(name="Search")
    url_resolver: URLResolver = resolve("/cases/")

    assert page_name.get_name(url_resolver) == "Search"


@pytest.mark.django_db
def test_page_name_derived_from_object():
    """Test PageName class returns expected name string"""
    email_template: EmailTemplate = EmailTemplate.objects.create(
        name=EMAIL_TEMPLATE_NAME
    )
    page_name: PageName = PageName(
        name="{email_template.name} preview",
        page_object_name="email_template",
        page_object_class=EmailTemplate,
    )
    url_resolver: URLResolver = resolve(
        f"/common/{email_template.id}/email-template-preview/"
    )

    assert (
        page_name.get_name(url_resolver=url_resolver)
        == EMAIL_TEMPLATE_NAME + " preview"
    )


def test_get_amp_page_name_by_url():
    """Test that page names can be retrieved by URL"""
    assert get_amp_page_name_by_url("/cases/") == "Search"
    assert (
        get_amp_page_name_by_url("/account/login/")
        == "Page name not found for two_factor:login"
    )
    assert get_amp_page_name_by_url("no-such-url") == "URL not found for no-such-url"
