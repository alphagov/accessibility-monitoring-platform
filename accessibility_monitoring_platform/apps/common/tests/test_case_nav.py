"""
Test utility functions of cases app
"""

from datetime import date
from typing import List

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Audit, Page
from ...cases.models import Case
from ..case_nav import (
    NavPage,
    NavSection,
    build_case_nav_sections,
    build_closing_the_case_nav_sections,
)


def test_case_nav_context_mixin_for_case(admin_client):
    """Test case nav context mixin populates context correctly"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, "Case details")
    assertContains(response, "<b>Case metadata</b>")


def test_nav_section_number_pages_and_subpages():
    """Test NavSection.number_pages_and_subpages"""

    assert NavSection(name="Section").number_pages_and_subpages() == 0
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url="url",
                    complete=None,
                    subpages=[NavPage(url="url1a", complete=None)],
                )
            ],
        ).number_pages_and_subpages()
        == 2
    )


def test_nav_section_number_complete():
    """Test NavSection.number_complete"""
    today: date = date.today()

    assert NavSection(name="Section").number_complete() == 0
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url="url",
                    complete=None,
                    subpages=[NavPage(url="url1a", complete=None)],
                )
            ],
        ).number_complete()
        == 0
    )
    assert (
        NavSection(
            name="Section", pages=[NavPage(url="url", complete=today)]
        ).number_complete()
        == 1
    )
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(
                    url="url",
                    complete=today,
                    subpages=[
                        NavPage(url="url2a", complete=today),
                    ],
                ),
                NavPage(url="url2", complete=today),
            ],
        ).number_complete()
        == 3
    )


@pytest.mark.django_db
def test_build_case_nav_sections_no_audit():
    """Test build_case_nav_sections when case has no audit"""
    case: Case = Case.objects.create()

    nav_sections: List[NavSection] = build_case_nav_sections(case=case)

    assert len(nav_sections) == 1

    nav_section: NavSection = nav_sections[0]

    assert nav_section.name == "Case details"
    assert nav_section.disabled is False
    assert len(nav_section.pages) == 1

    nav_page: NavPage = nav_section.pages[0]

    assert nav_page.url == "/cases/1/edit-case-metadata/"
    assert nav_page.complete is False


@pytest.mark.django_db
def test_build_closing_the_case_nav_sections():
    """Test build_case_nav_sections when case has audit"""
    case: Case = Case.objects.create()

    nav_sections: List[NavSection] = build_closing_the_case_nav_sections(case=case)

    assert len(nav_sections) == 1

    nav_section: NavSection = nav_sections[0]

    assert nav_section.name == "Closing the case"
    assert len(nav_section.pages) == 3

    assert nav_section.pages[0].name == "Reviewing changes"
    assert nav_section.pages[1].name == "Enforcement recommendation"
    assert nav_section.pages[2].name == "Closing the case"
