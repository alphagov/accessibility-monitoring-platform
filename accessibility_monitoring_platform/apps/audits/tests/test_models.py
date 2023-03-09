"""
Tests for cases models
"""
import pytest
from typing import List

from django.db.models.query import QuerySet

from ...cases.models import Case
from ...common.models import BOOLEAN_TRUE
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
    AccessibilityStatementCheck,
    RETEST_CHECK_RESULT_FIXED,
    ACCESSIBILITY_STATEMENT_CHECK_PREFIXES,
    SCOPE_STATE_VALID,
)

PAGE_NAME = "Page name"
WCAG_TYPE_AXE_NAME: str = "Axe WCAG"
WCAG_TYPE_MANUAL_NAME: str = "Manual WCAG"
WCAG_TYPE_PDF_NAME: str = "PDF WCAG"
WCAG_DESCRIPTION: str = "WCAG definition description"
INITIAL_NOTES: str = "Initial notes"
FINAL_NOTES: str = "Final notes"


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
    pages: QuerySet[Page] = audit.page_audit.all()

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
def test_audit_every_pages_returns_pdf_last():
    """PDF page returned last."""
    audit: Audit = create_audit_and_pages()

    assert audit.every_page.last().page_type == PAGE_TYPE_PDF


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
    assert audit.testable_pages[0].id == testable_page.id


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
def test_page_all_check_results_returns_pdf_check_results_last():
    """
    Test all_check_results attribute of page returns PDF-page check results last.
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_check_results) == 3
    assert audit.failed_check_results.last().page.page_type == PAGE_TYPE_PDF


@pytest.mark.django_db
def test_check_result_returns_id_and_fields_for_retest():
    """
    Test check_result attribute of dict_for_retest returns id and fields for retest form.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)
    check_result: CheckResult = home_page.all_check_results[0]

    assert check_result.dict_for_retest == {
        "id": check_result.id,
        "retest_state": RETEST_CHECK_RESULT_DEFAULT,
        "retest_notes": "",
    }


def test_wcag_definition_strings():
    """
    Test WCAG definitions return expected string values.
    """
    wcag_definition: WcagDefinition = WcagDefinition(
        type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME
    )
    assert str(wcag_definition) == f"{WCAG_TYPE_PDF_NAME} (PDF)"

    wcag_definition_with_description: WcagDefinition = WcagDefinition(
        type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME, description=WCAG_DESCRIPTION
    )
    assert (
        str(wcag_definition_with_description)
        == f"{WCAG_TYPE_PDF_NAME}: {WCAG_DESCRIPTION} (PDF)"
    )


@pytest.mark.django_db
def test_accessibility_statement_initially_found():
    """
    Test that an accessibility statement was initially found.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    # No page
    assert audit.accessibility_statement_initially_found is False

    page: Page = Page.objects.create(audit=audit, page_type=PAGE_TYPE_STATEMENT)

    # No URL
    assert audit.accessibility_statement_initially_found is False

    page.url = "https://example.com"
    page.save()

    # Not found flag not set
    assert audit.accessibility_statement_initially_found is True

    page.not_found = BOOLEAN_TRUE
    page.save()

    # Not found flag set
    assert audit.accessibility_statement_initially_found is False


@pytest.mark.django_db
def test_twelve_week_accessibility_statement_found():
    """
    Test that an accessibility statement was found on 12-week retest.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert audit.twelve_week_accessibility_statement_found is False

    audit.twelve_week_accessibility_statement_url = "https://example.com/statement"

    assert audit.twelve_week_accessibility_statement_found is True


def test_accessibility_statement_check():
    """
    Test that an accessibility statement check has the expected attributes.
    """
    audit: Audit = Audit(
        scope_notes=INITIAL_NOTES, audit_retest_scope_notes=FINAL_NOTES
    )

    accessibility_statement_check: AccessibilityStatementCheck = (
        AccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.field_name_prefix == "scope"
    assert accessibility_statement_check.valid_value == "present"
    assert accessibility_statement_check.label == "Scope"
    assert accessibility_statement_check.initial_state == "not-present"
    assert accessibility_statement_check.initial_state_display == "Not included"
    assert accessibility_statement_check.initial_notes == INITIAL_NOTES
    assert accessibility_statement_check.final_state == "not-present"
    assert accessibility_statement_check.final_state_display == "Not included"
    assert accessibility_statement_check.final_notes == FINAL_NOTES
    assert accessibility_statement_check.initially_invalid is True
    assert accessibility_statement_check.finally_fixed is False
    assert accessibility_statement_check.finally_invalid is True


@pytest.mark.parametrize(
    "audit_field_name, audit_field_value, expected_value",
    [
        ("scope_state", "present", False),
        ("scope_state", "not-present", True),
        ("scope_state", "incomplete", True),
        ("scope_state", "other", True),
    ],
)
def test_accessibility_statement_check_initially_valid(
    audit_field_name, audit_field_value, expected_value
):
    """
    Test that an accessibility statement check has the expected value for
    initially invalid.
    """
    audit: Audit = Audit()
    setattr(audit, audit_field_name, audit_field_value)

    accessibility_statement_check: AccessibilityStatementCheck = (
        AccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.initially_invalid == expected_value


@pytest.mark.parametrize(
    "audit_field_name, audit_field_value, expected_value",
    [
        ("audit_retest_scope_state", "present", True),
        ("audit_retest_scope_state", "not-present", False),
        ("audit_retest_scope_state", "incomplete", False),
        ("audit_retest_scope_state", "other", False),
    ],
)
def test_accessibility_statement_check_finally_fixed(
    audit_field_name, audit_field_value, expected_value
):
    """
    Test that an accessibility statement check has the expected value for
    finally fixed.
    """
    audit: Audit = Audit()
    setattr(audit, audit_field_name, audit_field_value)

    accessibility_statement_check: AccessibilityStatementCheck = (
        AccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.finally_fixed == expected_value


@pytest.mark.parametrize(
    "audit_field_name, audit_field_value, expected_value",
    [
        ("audit_retest_scope_state", "present", False),
        ("audit_retest_scope_state", "not-present", True),
        ("audit_retest_scope_state", "incomplete", True),
        ("audit_retest_scope_state", "other", True),
    ],
)
def test_accessibility_statement_check_finally_invalid(
    audit_field_name, audit_field_value, expected_value
):
    """
    Test that an accessibility statement check has the expected value for
    finally invalid.
    """
    audit: Audit = Audit()
    setattr(audit, audit_field_name, audit_field_value)

    accessibility_statement_check: AccessibilityStatementCheck = (
        AccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.finally_invalid == expected_value


@pytest.mark.django_db
def test_audit_fixed_check_results():
    """
    Test that fixed_check_results returns the expected values.
    """
    audit: Audit = create_audit_and_check_results()

    assert audit.fixed_check_results.count() == 0

    home_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)
    check_result: CheckResult = home_page.all_check_results[0]
    check_result.retest_state = RETEST_CHECK_RESULT_FIXED
    check_result.save()

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.fixed_check_results.count() == 1
    assert updated_audit.fixed_check_results[0].id == check_result.id


@pytest.mark.django_db
def test_audit_unfixed_check_results():
    """
    Test that unfixed_check_results returns the expected values.
    """
    audit: Audit = create_audit_and_check_results()

    assert audit.unfixed_check_results.count() == 3

    check_result: CheckResult = audit.unfixed_check_results[0]
    check_result.retest_state = RETEST_CHECK_RESULT_FIXED
    check_result.save()

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.unfixed_check_results.count() == 2


def test_audit_accessibility_statement_checks():
    """
    Test that an audit has the expected accessibility statement checks.
    """
    audit: Audit = Audit()

    assert len(audit.accessibility_statement_checks) == 13

    for count, field_name_prefix in enumerate(ACCESSIBILITY_STATEMENT_CHECK_PREFIXES):
        assert (
            audit.accessibility_statement_checks[count].field_name_prefix
            == field_name_prefix
        )


def test_audit_accessibility_statement_initially_invalid_count():
    """
    Test that an audit has the expected number of initially invalid
    accessibility statement checks.
    """
    audit: Audit = Audit()

    assert audit.accessibility_statement_initially_invalid_checks_count == 12

    audit.scope_state = SCOPE_STATE_VALID

    assert audit.accessibility_statement_initially_invalid_checks_count == 11


def test_audit_accessibility_statement_fixed_count():
    """
    Test that an audit has the expected number of fixed accessibility statement
    checks.
    """
    audit: Audit = Audit()

    assert audit.fixed_accessibility_statement_checks_count == 0

    audit.audit_retest_scope_state = SCOPE_STATE_VALID

    assert audit.fixed_accessibility_statement_checks_count == 1


def test_audit_accessibility_statement_finally_invalid():
    """
    Test that an audit has the expected finally invalid accessibility statement
    checks.
    """
    audit: Audit = Audit()

    assert len(audit.finally_invalid_accessibility_statement_checks) == 12

    audit.audit_retest_scope_state = SCOPE_STATE_VALID

    assert len(audit.finally_invalid_accessibility_statement_checks) == 11
