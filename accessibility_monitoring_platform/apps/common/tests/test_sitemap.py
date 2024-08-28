"""
Test utility functions of cases app
"""

import pytest
from django.contrib.auth.models import User
from django.urls import URLResolver, resolve, reverse

from ...audits.models import Audit, Page, Retest, RetestPage
from ...cases.models import Case
from ...common.models import EmailTemplate
from ..sitemap import (
    PlatformPage,
    get_current_platform_page,
    get_platform_page_name_by_url,
)

EMAIL_TEMPLATE_NAME: str = "1c. Template name"


@pytest.mark.django_db
def test_get_current_platform_page_for_case(rf):
    """Test get_current_platform_page returns expected Case-specific name"""
    case: Case = Case.objects.create()

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
    )
    request.user = request_user

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.name == "Case metadata"
    assert platform_page.get_name() == "Case metadata"
    assert platform_page.url_name == "cases:edit-case-metadata"


@pytest.mark.django_db
def test_get_current_platform_page_for_page(rf):
    """Test get_current_platform_page returns expected Page-specific name"""
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

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.get_name() == "Additional page test"
    assert platform_page.url_name == "audits:edit-audit-page-checks"


@pytest.mark.django_db
def test_get_current_platform_page_for_retest_page(rf):
    """Test get_current_platform_page returns expected RetestPage-specific name"""
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

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.get_name() == "Retest #1 | Additional"
    assert platform_page.url_name == "audits:edit-retest-page-checks"


@pytest.mark.django_db
def test_get_current_platform_page_for_email_template(rf):
    """Test get_current_platform_page returns expected EmailTemplate-specific name"""
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

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.get_name() == EMAIL_TEMPLATE_NAME
    assert platform_page.url_name == "cases:email-template-preview"


@pytest.mark.django_db
def test_get_current_platform_page_for_export(rf):
    """Test get_current_platform_page returns expected name for export"""
    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("exports:export-list"),
    )
    request.user = request_user

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.get_name() == "EHRC CSV export manager"
    assert platform_page.url_name == "exports:export-list"

    request = rf.get(
        f'{reverse("exports:export-list")}?enforcement_body=ecni',
    )

    platform_page: PlatformPage = get_current_platform_page(request)

    assert platform_page.get_name() == "ECNI CSV export manager"
    assert platform_page.url_name == "exports:export-list"


def test_get_platform_page_name_by_url():
    """Test that page names can be retrieved by URL"""
    assert get_platform_page_name_by_url("/cases/") == "Search"
    assert (
        get_platform_page_name_by_url("/account/login/")
        == "Page name not found for two_factor:login"
    )
    assert (
        get_platform_page_name_by_url("no-such-url") == "URL not found for no-such-url"
    )
