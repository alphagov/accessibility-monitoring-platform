"""
Test utility functions of cases app
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from ...audits.models import Audit, Page, Retest, RetestPage
from ...cases.models import Case
from ...common.models import EmailTemplate
from ..page_name_utils import PageName, get_amp_page_name


def test_page_name():
    """Test PageName class returns expected name string"""
    page_name: PageName = PageName(name="{page.page_title} test")

    assert page_name.get_name() == "{page.page_title} test"

    page_name: PageName = PageName(name="{page.page_title} test", format_string=True)
    page: Page = Page(name="Page name")

    assert page_name.get_name(page=page) == "Page name page test"


@pytest.mark.django_db
def test_get_amp_page_namei_for_case(rf):
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
        name="1c. Template name"
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

    assert get_amp_page_name(request) == "1c. Template name"
