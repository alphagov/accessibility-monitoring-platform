"""
Test utility functions of cases app
"""

import pytest

from ...audits.models import Audit, Page
from ...cases.models import Case
from ..case_nav import NavPage, NavSection, NavSubPage, build_case_nav_sections


def test_nav_section_number_complete():
    """Test NavSection.number_complete"""

    assert NavSection(name="Section").number_complete() == 0
    assert (
        NavSection(
            name="Section", pages=[NavPage(name="Page", url="url", complete=False)]
        ).number_complete()
        == 0
    )
    assert (
        NavSection(
            name="Section", pages=[NavPage(name="Page", url="url", complete=True)]
        ).number_complete()
        == 1
    )
    assert (
        NavSection(
            name="Section",
            pages=[
                NavPage(name="Page", url="url", complete=True),
                NavPage(name="Page 2", url="url2", complete=True),
            ],
        ).number_complete()
        == 2
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
                    name="Case metadata",
                    url="/cases/1/edit-case-metadata/",
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
    Page.objects.create(audit=audit, url="https://example.com")

    assert build_case_nav_sections(case=case) == [
        NavSection(
            name="Case details",
            disabled=False,
            pages=[
                NavPage(
                    name="Case metadata",
                    url="/cases/1/edit-case-metadata/",
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
                    name="Initial test metadata",
                    url="/audits/1/edit-audit-metadata/",
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    name="Add or remove pages",
                    url="/audits/1/edit-audit-pages/",
                    complete=None,
                    subpages=[
                        NavSubPage(
                            name="Additional page test",
                            url="/audits/pages/1/edit-audit-page-checks/",
                            complete=None,
                        )
                    ],
                ),
                NavPage(
                    name="Website compliance decision",
                    url="/audits/1/edit-website-decision/",
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    name="Test summary",
                    url="/audits/1/edit-audit-wcag-summary/",
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
                    name="Statement links",
                    url="/audits/1/edit-statement-pages/",
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    name="Statement overview",
                    url="/audits/1/edit-statement-overview/",
                    complete=None,
                    subpages=[
                        NavSubPage(
                            name="Statement information",
                            url="/audits/1/edit-statement-website/",
                            complete=None,
                        ),
                        NavSubPage(
                            name="Compliance status",
                            url="/audits/1/edit-statement-compliance/",
                            complete=None,
                        ),
                        NavSubPage(
                            name="Non-accessible content",
                            url="/audits/1/edit-statement-non-accessible/",
                            complete=None,
                        ),
                        NavSubPage(
                            name="Statement preparation",
                            url="/audits/1/edit-statement-preparation/",
                            complete=None,
                        ),
                        NavSubPage(
                            name="Feedback and enforcement procedure",
                            url="/audits/1/edit-statement-feedback/",
                            complete=None,
                        ),
                        NavSubPage(
                            name="Custom statement issues",
                            url="/audits/1/edit-statement-custom/",
                            complete=None,
                        ),
                    ],
                ),
                NavPage(
                    name="Initial disproportionate burden claim",
                    url="/audits/1/edit-initial-disproportionate-burden/",
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    name="Initial statement compliance decision",
                    url="/audits/1/edit-statement-decision/",
                    complete=None,
                    subpages=None,
                ),
                NavPage(
                    name="Test summary",
                    url="/audits/1/edit-audit-statement-summary/",
                    complete=None,
                    subpages=None,
                ),
            ],
        ),
    ]
