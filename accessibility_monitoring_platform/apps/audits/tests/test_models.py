"""
Tests for cases models
"""
import pytest
from datetime import datetime
from typing import List, Optional

from django.db.models.query import QuerySet

from ...cases.models import Case
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
    TEST_TYPE_AXE,
    TEST_TYPE_MANUAL,
    TEST_TYPE_PDF,
    WcagDefinition,
    CHECK_RESULT_ERROR,
    CHECK_RESULT_NO_ERROR,
    RETEST_CHECK_RESULT_DEFAULT,
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
    ]:
        Page.objects.create(audit=audit, page_type=page_type)
    Page.objects.create(audit=audit, page_type=PAGE_TYPE_EXTRA, is_deleted=True)
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
        check_result_state: str = (
            CHECK_RESULT_ERROR
            if page.page_type in [PAGE_TYPE_HOME, PAGE_TYPE_PDF]
            else CHECK_RESULT_NO_ERROR
        )
        if page.page_type == PAGE_TYPE_PDF:
            CheckResult.objects.create(
                audit=audit,
                page=page,
                check_result_state=check_result_state,
                type=pdf_wcag_definition.type,
                wcag_definition=pdf_wcag_definition,
            )
        else:
            for wcag_definition in html_wcag_definitions:
                CheckResult.objects.create(
                    audit=audit,
                    page=page,
                    check_result_state=check_result_state,
                    type=wcag_definition.type,
                    wcag_definition=wcag_definition,
                )

    return audit


@pytest.mark.django_db
def test_audit_every_pages_returns_all_pages():
    """
    Deleted and pages which were not found are also excluded.
    """
    audit: Audit = create_audit_and_pages()

    assert len(audit.every_page) == 6


@pytest.mark.django_db
def test_audit_testable_pages_returns_expected_page():
    """
    Deleted, not found and pages without URLs excluded.
    """
    audit: Audit = create_audit_and_pages()
    testable_page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_HOME, url="https://example.com"
    )
    Page.objects.create(
        audit=audit,
        page_type=PAGE_TYPE_HOME,
        url="https://example.com",
        not_found="yes",
    )

    assert len(audit.testable_pages) == 1
    assert audit.testable_pages[0].id == testable_page.id  # type: ignore


@pytest.mark.django_db
def test_page_string():
    """
    Test Page string is name if present otherwise type
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.every_page[0]

    assert str(page) == "Additional"

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
                if check.check_result_state == CHECK_RESULT_ERROR
            ]
        )
        == 3
    )


@pytest.mark.django_db
def test_audit_failed_check_results_for_deleted_page_not_returned():
    """
    Test failed_check_results attribute of audit returns only check results where failed is "yes"
    and associated page has not been deleted.
    """
    audit: Audit = create_audit_and_check_results()
    page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_PDF)
    page.is_deleted = True
    page.save()

    assert len(audit.failed_check_results) == 2


@pytest.mark.django_db
def test_audit_accessibility_state_ment_page_returns_page():
    """
    Accessibility Statement page returned
    """
    audit: Audit = create_audit_and_pages()
    page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_STATEMENT)

    assert audit.accessibility_statement_page == page


@pytest.mark.django_db
def test_page_all_check_results_returns_check_results():
    """
    Test all_check_results attribute of page returns expected check results.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)

    assert len(home_page.all_check_results) == 2
    assert home_page.all_check_results[0].type == TEST_TYPE_AXE
    assert home_page.all_check_results[1].type == TEST_TYPE_MANUAL


@pytest.mark.django_db
def test_check_result_returns_id_and_fields_for_retest():
    """
    Test check_result attribute of dict_for_retest returns id and fields for retest form.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)
    check_result: CheckResult = home_page.all_check_results[0]

    assert check_result.dict_for_retest == {
        "id": check_result.id,  # type: ignore
        "retest_state": RETEST_CHECK_RESULT_DEFAULT,
        "retest_notes": "",
    }


@pytest.mark.django_db
def test_report_data_updated_time():
    """
    Test that saving a CheckResult updates its Audit's report
    data updated time.
    """
    audit: Audit = create_audit_and_pages()
    page: Optional[Page] = audit.page_audit.all().first()  # type: ignore
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME
    )

    assert audit.report_data_updated_time is None

    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CHECK_RESULT_ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert audit.report_data_updated_time is not None

    first_report_data_updated_time: Optional[datetime] = audit.report_data_updated_time

    check_result.save()

    assert audit.report_data_updated_time > first_report_data_updated_time
