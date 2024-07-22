"""
Test utility functions of cases app
"""

import pytest
from django.contrib.auth.models import User
from django.urls import URLResolver, resolve, reverse

from ...audits.models import Audit, Page, Retest, RetestPage
from ...cases.models import Case
from ...common.models import EmailTemplate
from ..page_name_utils import PageName, get_amp_page_name

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


@pytest.mark.django_db
def test_get_amp_page_name_for_case(rf):
    """Test get_amp_page_name returns expected Case-specific name"""
    case: Case = Case.objects.create()

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
    )
    request.user = request_user

    assert get_amp_page_name(request) == "Case metadata"


@pytest.mark.django_db
def test_get_amp_page_name_for_page(rf):
    """Test get_amp_page_name returns expected Page-specific name"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id}),
    )
    request.user = request_user

    assert get_amp_page_name(request) == "Additional page test"


@pytest.mark.django_db
def test_get_amp_page_name_for_retest_page(rf):
    """Test get_amp_page_name returns expected RetestPage-specific name"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    retest: Retest = Retest.objects.create(case=case)
    retest_page: RetestPage = RetestPage.objects.create(retest=retest, page=page)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-retest-page-checks", kwargs={"pk": retest_page.id}),
    )
    request.user = request_user

    assert get_amp_page_name(request) == "Retest #1 | Additional"


@pytest.mark.django_db
def test_get_amp_page_name_for_email_template(rf):
    """Test get_amp_page_name returns expected EmailTemplate-specific name"""
    case: Case = Case.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.create(
        name=EMAIL_TEMPLATE_NAME
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse(
            "cases:email-template-preview",
            kwargs={"pk": email_template.id, "case_id": case.id},
        ),
    )
    request.user = request_user

    assert get_amp_page_name(request) == EMAIL_TEMPLATE_NAME
