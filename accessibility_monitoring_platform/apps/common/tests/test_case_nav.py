"""
Test utility functions of cases app
"""

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Audit, Page
from ...cases.models import Case
from ..case_nav import (
    NavPage,
    NavSection,
    NavSubPage,
    PageName,
    build_case_nav_sections,
)


def test_page_name():
    page_name: PageName = PageName(name="{page.page_title} test")

    assert page_name.get_name() == "{page.page_title} test"

    page_name: PageName = PageName(name="{page.page_title} test", format_string=True)
    page: Page = Page(name="Page name")

    assert page_name.get_name(page=page) == "Page name page test"


def test_case_nav_context_mixin_for_case(admin_client):
    """Test case nav context mixin populates context correctly"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, "amp-nav-details")
    assertContains(response, "Initial WCAG test")


def test_case_nav_context_mixin_for_audit(admin_client):
    """Test case nav context mixin populates context correctly"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id})
    )

    assert response.status_code == 200

    assertContains(response, "amp-nav-details")
    assertContains(response, "Initial WCAG test")


def test_case_nav_context_mixin_for_page(admin_client):
    """Test case nav context mixin populates context correctly"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id})
    )

    assert response.status_code == 200

    assertContains(response, "amp-nav-details")
    assertContains(response, "Initial WCAG test")


def test_nav_section_number_pages_and_subpages():
    """Test NavSection.number_pages_and_subpages"""

    assert NavSection(name="Section").number_pages_and_subpages() == 0
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url_name="url",
                    complete=False,
                    subpages=[NavSubPage(url_name="url1a", complete=False)],
                )
            ],
        ).number_pages_and_subpages()
        == 2
    )


def test_nav_section_number_complete():
    """Test NavSection.number_complete"""

    assert NavSection(name="Section").number_complete() == 0
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url_name="url",
                    complete=False,
                    subpages=[NavSubPage(url_name="url1a", complete=False)],
                )
            ],
        ).number_complete()
        == 0
    )
    assert (
        NavSection(
            name="Section", pages=[NavPage(url_name="url", complete=True)]
        ).number_complete()
        == 1
    )
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url_name="url",
                    complete=True,
                    subpages=[
                        NavSubPage(url_name="url2a", complete=True),
                    ],
                ),
                NavPage(url_name="url2", complete=True),
            ],
        ).number_complete()
        == 3
    )


@pytest.mark.django_db
def test_build_case_nav_sections_no_audit():
    """Test build_case_nav_sections when case has no audit"""
    case: Case = Case.objects.create()

    assert build_case_nav_sections(case=case) == [
        NavSection(
            name="Case details",
            disabled=False,
            pages=[
                NavPage(
                    url_name="cases:edit-case-metadata",
                    url_kwargs={"pk": 1},
                    complete=None,
                )
            ],
        )
    ]


@pytest.mark.django_db
def test_build_case_nav_sections_with_audit():
    """Test build_case_nav_sections when case has audit"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")

    assert build_case_nav_sections(case=case) == [
        NavSection(
            name="Case details",
            disabled=False,
            pages=[
                NavPage(
                    url_name="cases:edit-case-metadata",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                )
            ],
        ),
        NavSection(
            name="Initial WCAG test",
            disabled=False,
            pages=[
                NavPage(
                    url_name="audits:edit-audit-metadata",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    url_name="audits:edit-audit-pages",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=[
                        NavSubPage(
                            url_name="audits:edit-audit-page-checks",
                            url_kwargs={"pk": 1},
                            name_kwargs={"page": page},
                            complete=None,
                        )
                    ],
                ),
                NavPage(
                    url_name="audits:edit-website-decision",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    url_name="audits:edit-audit-wcag-summary",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
            ],
        ),
        NavSection(
            name="Initial statement",
            disabled=False,
            pages=[
                NavPage(
                    url_name="audits:edit-statement-pages",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    url_name="audits:edit-statement-overview",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=[
                        NavSubPage(
                            url_name="audits:edit-statement-website",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                        NavSubPage(
                            url_name="audits:edit-statement-compliance",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                        NavSubPage(
                            url_name="audits:edit-statement-non-accessible",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                        NavSubPage(
                            url_name="audits:edit-statement-preparation",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                        NavSubPage(
                            url_name="audits:edit-statement-feedback",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                        NavSubPage(
                            url_name="audits:edit-statement-custom",
                            url_kwargs={"pk": 1},
                            name_kwargs=None,
                            complete=None,
                        ),
                    ],
                ),
                NavPage(
                    url_name="audits:edit-initial-disproportionate-burden",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    url_name="audits:edit-statement-decision",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    url_name="audits:edit-audit-statement-summary",
                    url_kwargs={"pk": 1},
                    complete=None,
                    subpages=None,
                ),
            ],
        ),
    ]
