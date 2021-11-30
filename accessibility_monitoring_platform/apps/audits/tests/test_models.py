"""
Tests for cases models
"""
import pytest
from typing import List

from django.db.models.query import QuerySet

from ...cases.models import Case
from ...common.models import BOOLEAN_TRUE, BOOLEAN_FALSE
from ..models import (
    Audit,
    Page,
    CheckResult,
    PAGE_TYPE_EXTRA,
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
    PAGE_TYPE_ALL,
    TEST_TYPE_AXE,
    TEST_TYPE_MANUAL,
    TEST_TYPE_PDF,
    WcagDefinition,
)

PAGE_NAME = "Page name"
WCAG_TYPE_AXE_NAME: str = "Axe WCAG"
WCAG_TYPE_MANUAL_NAME: str = "Manual WCAG"
WCAG_TYPE_PDF_NAME: str = "PDF WCAG"


def create_audit_and_pages() -> Audit:
    """Create an audit with all types of page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for page_type in [
        PAGE_TYPE_EXTRA,
        PAGE_TYPE_HOME,
        PAGE_TYPE_CONTACT,
        PAGE_TYPE_STATEMENT,
        PAGE_TYPE_PDF,
        PAGE_TYPE_FORM,
        PAGE_TYPE_ALL,
    ]:
        Page.objects.create(audit=audit, type=page_type)
    Page.objects.create(audit=audit, type=PAGE_TYPE_EXTRA, is_deleted=True)
    Page.objects.create(audit=audit, type=PAGE_TYPE_EXTRA, not_found=BOOLEAN_TRUE)
    return audit


def create_audit_and_check_results() -> Audit:
    """Create an audit with failed check results"""
    html_wcag_definitions: List[WcagDefinition] = [
        WcagDefinition.objects.create(type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME),
        WcagDefinition.objects.create(
            type=TEST_TYPE_MANUAL, name=WCAG_TYPE_MANUAL_NAME
        ),
    ]
    pdf_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME
    )

    audit: Audit = create_audit_and_pages()
    pages: QuerySet[Page] = audit.page_audit.all()  # type: ignore

    for page in pages:
        failed: str = (
            BOOLEAN_TRUE
            if page.type in [PAGE_TYPE_HOME, PAGE_TYPE_PDF]
            else BOOLEAN_FALSE
        )
        if page.type == PAGE_TYPE_PDF:
            CheckResult.objects.create(
                audit=audit,
                page=page,
                failed=failed,
                type=pdf_wcag_definition.type,
                wcag_definition=pdf_wcag_definition,
            )
        else:
            for wcag_definition in html_wcag_definitions:
                CheckResult.objects.create(
                    audit=audit,
                    page=page,
                    failed=failed,
                    type=wcag_definition.type,
                    wcag_definition=wcag_definition,
                )

    return audit


@pytest.mark.django_db
def test_audit_all_pages_returns_all_pages_except_pdf():
    """
    Test all_pages attribute of audit does not include pages of type pdf.
    Deleted and pages which were not found are also excluded.
    """
    audit: Audit = create_audit_and_pages()

    assert len(audit.all_pages) == 6
    assert PAGE_TYPE_PDF not in [page.type for page in audit.all_pages]


@pytest.mark.django_db
def test_audit_html_pages_returns_all_pages_except_all_pages():
    """
    Test html_pages attribute of audit does not include pages of types PDF or all.
    """
    audit: Audit = create_audit_and_pages()
    page_types: List[str] = [page.type for page in audit.html_pages]

    assert len(audit.html_pages) == 5
    assert PAGE_TYPE_PDF not in page_types
    assert PAGE_TYPE_ALL not in page_types


@pytest.mark.django_db
def test_audit_standard_pages_returns_no_extra_or_all_pages():
    """
    Test standard_pages attribute of audit does not include pages of type PDF,
    all pages or extra.
    """
    audit: Audit = create_audit_and_pages()
    page_types: List[str] = [page.type for page in audit.standard_pages]

    assert len(audit.standard_pages) == 5
    assert PAGE_TYPE_ALL not in page_types
    assert PAGE_TYPE_EXTRA not in page_types


@pytest.mark.django_db
def test_audit_extra_pages_returns_only_extra_pages():
    """
    Test extra_pages attribute of audit returns only pages of type extra.
    """
    audit: Audit = create_audit_and_pages()

    assert len(audit.extra_pages) == 1
    assert list(audit.extra_pages)[0].type == PAGE_TYPE_EXTRA


@pytest.mark.django_db
def test_page_string():
    """
    Test Page string is name if present otherwise type
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.all_pages[0]

    assert str(page) == "Page"

    page.name = PAGE_NAME

    assert str(page) == PAGE_NAME


@pytest.mark.django_db
def test_audit_failed_check_results_returns_only_failed_checks():
    """
    Test failed_check_results attribute of audit returns only check results where failed is "yes".
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_check_results) == 3
    assert (
        len(
            [
                check
                for check in audit.failed_check_results
                if check.failed == BOOLEAN_TRUE
            ]
        )
        == 3
    )


@pytest.mark.django_db
def test_audit_failed_axe_check_results_returns_only_axe_failed_checks():
    """
    Test failed_axe_check_results attribute of audit returns only axe check results where failed is "yes".
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_axe_check_results) == 1
    assert audit.failed_axe_check_results[0].failed == BOOLEAN_TRUE
    assert audit.failed_axe_check_results[0].type == TEST_TYPE_AXE


@pytest.mark.django_db
def test_audit_failed_manual_check_results_returns_only_manual_failed_checks():
    """
    Test failed_manual_check_results attribute of audit returns only manual check results where failed is "yes".
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_manual_check_results) == 1
    assert audit.failed_manual_check_results[0].failed == BOOLEAN_TRUE
    assert audit.failed_manual_check_results[0].type == TEST_TYPE_MANUAL


@pytest.mark.django_db
def test_audit_failed_pdf_check_results_returns_only_pdf_failed_checks():
    """
    Test failed_pdf_check_results attribute of audit returns only pdf check results where failed is "yes".
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_pdf_check_results) == 1
    assert audit.failed_pdf_check_results[0].failed == BOOLEAN_TRUE
    assert audit.failed_pdf_check_results[0].type == TEST_TYPE_PDF


@pytest.mark.django_db
def test_page_all_check_results_returns_check_results():
    """
    Test all_check_results attribute of page returns expected check results.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, type=PAGE_TYPE_HOME)

    assert len(home_page.all_check_results) == 2
    assert home_page.all_check_results[0].type == TEST_TYPE_AXE
    assert home_page.all_check_results[1].type == TEST_TYPE_MANUAL


@pytest.mark.django_db
def test_page_axe_check_results_returns_only_axe_check_results():
    """
    Test axe_check_results attribute of page returns only axe check results.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, type=PAGE_TYPE_HOME)

    assert len(home_page.axe_check_results) == 1
    assert home_page.axe_check_results[0].type == TEST_TYPE_AXE


@pytest.mark.django_db
def test_page_manual_check_results_returns_only_manual_check_results():
    """
    Test manual_check_results attribute of page returns only manual check results.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, type=PAGE_TYPE_HOME)

    assert len(home_page.manual_check_results) == 1
    assert home_page.manual_check_results[0].type == TEST_TYPE_MANUAL


@pytest.mark.django_db
def test_page_pdf_check_results_returns_only_pdf_check_results():
    """
    Test pdf_check_results attribute of page returns only pdf check results.
    """
    audit: Audit = create_audit_and_check_results()
    pdf_page: Page = Page.objects.get(audit=audit, type=PAGE_TYPE_PDF)

    assert len(pdf_page.all_check_results) == 1
    assert pdf_page.pdf_check_results[0].type == TEST_TYPE_PDF
