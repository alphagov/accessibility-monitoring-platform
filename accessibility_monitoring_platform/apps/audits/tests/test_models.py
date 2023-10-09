"""
Tests for cases models
"""
import pytest

from datetime import date, datetime, timezone
from typing import List
from unittest.mock import patch, Mock

from pytest_django.asserts import assertQuerysetEqual

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
    ArchiveAccessibilityStatementCheck,
    RETEST_CHECK_RESULT_FIXED,
    ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_PREFIXES,
    SCOPE_STATE_VALID,
    StatementCheck,
    StatementCheckResult,
    STATEMENT_CHECK_TYPE_OVERVIEW,
    STATEMENT_CHECK_NOT_TESTED,
    STATEMENT_CHECK_NO,
    STATEMENT_CHECK_YES,
)

PAGE_NAME = "Page name"
WCAG_TYPE_AXE_NAME: str = "Axe WCAG"
WCAG_TYPE_MANUAL_NAME: str = "Manual WCAG"
WCAG_TYPE_PDF_NAME: str = "PDF WCAG"
WCAG_DESCRIPTION: str = "WCAG definition description"
DATETIME_AUDIT_UPDATED: datetime = datetime(2021, 9, 20, tzinfo=timezone.utc)
DATETIME_PAGE_UPDATED: datetime = datetime(2021, 9, 22, tzinfo=timezone.utc)
DATETIME_CHECK_RESULT_UPDATED: datetime = datetime(2021, 9, 24, tzinfo=timezone.utc)
INITIAL_NOTES: str = "Initial notes"
FINAL_NOTES: str = "Final notes"
INCOMPLETE_DEADLINE_TEXT: str = "Incomplete deadline text"
INSUFFICIENT_DEADLINE_TEXT: str = "Insufficient deadline text"
ERROR_NOTES: str = "Error notes"


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


def create_audit_and_statement_check_results() -> Audit:
    """Create an audit with all types of statement checks"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for count, statement_check in enumerate(StatementCheck.objects.all()):
        check_result_state: str = (
            STATEMENT_CHECK_NO if count % 2 == 0 else STATEMENT_CHECK_YES
        )
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=check_result_state,
        )
    StatementCheckResult.objects.create(
        audit=audit,
        report_comment="Custom statement issue",
    )
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
                    notes=ERROR_NOTES,
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
def test_audit_every_pages_returns_pdf_and_statement_last():
    """Statement page returned last. PDF page second-last"""
    audit: Audit = create_audit_and_pages()

    assert audit.every_page.last().page_type == PAGE_TYPE_STATEMENT
    assert list(audit.every_page)[-2].page_type == PAGE_TYPE_PDF


@pytest.mark.django_db
def test_page_get_absolute_url():
    """
    Test Page.get_absolute_url is as expected
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.accessibility_statement_page

    assert page.get_absolute_url() == f"/audits/pages/{page.id}/edit-audit-page-checks/"


@pytest.mark.django_db
def test_page_str():
    """
    Test Page.__str__ is as expected
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.accessibility_statement_page

    assert page.__str__() == "Accessibility statement"


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
def test_page_anchor():
    """
    Test Page anchor string
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.every_page[0]

    assert page.anchor == f"test-page-{page.id}"


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

    assert len(audit.failed_check_results) == 3

    page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_PDF)
    page.is_deleted = True
    page.save()

    assert len(audit.failed_check_results) == 2


@pytest.mark.django_db
def test_audit_failed_check_results_for_missing_page_not_returned():
    """
    Test failed_check_results attribute of audit returns only check results
    where retest page missing is not set.
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_check_results) == 3

    page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_PDF)
    page.retest_page_missing_date = date.today()
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
def test_accessibility_statement_found():
    """
    Test that an accessibility statement was found.
    """
    audit: Audit = create_audit_and_pages()
    page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_STATEMENT)

    assert audit.accessibility_statement_found is False

    page.url = "https://example.com/statement"
    page.save()

    assert audit.accessibility_statement_found is True

    page.not_found = BOOLEAN_TRUE
    page.save()

    assert audit.accessibility_statement_found is False


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


@pytest.mark.django_db
def test_audit_updated_updated():
    """Test the audit updated field is updated"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_UPDATED)):
        audit.save()

    assert audit.updated == DATETIME_AUDIT_UPDATED


@pytest.mark.django_db
def test_page_updated_updated():
    """Test the page updated field is updated"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        page.save()

    assert page.updated == DATETIME_PAGE_UPDATED


@pytest.mark.django_db
def test_check_result_updated_updated():
    """Test the check result updated field is updated"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(type=TEST_TYPE_AXE)
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit, page=page, type=TEST_TYPE_AXE, wcag_definition=wcag_definition
    )
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_UPDATED)
    ):
        check_result.save()

    assert check_result.updated == DATETIME_CHECK_RESULT_UPDATED


def test_accessibility_statement_check():
    """
    Test that an accessibility statement check has the expected attributes.
    """
    audit: Audit = Audit(
        archive_scope_notes=INITIAL_NOTES, archive_audit_retest_scope_notes=FINAL_NOTES
    )

    accessibility_statement_check: ArchiveAccessibilityStatementCheck = (
        ArchiveAccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.field_name_prefix == "scope"
    assert accessibility_statement_check.valid_values == ["present"]
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
        ("archive_scope_state", "present", False),
        ("archive_scope_state", "not-present", True),
        ("archive_scope_state", "incomplete", True),
        ("archive_scope_state", "other", True),
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

    accessibility_statement_check: ArchiveAccessibilityStatementCheck = (
        ArchiveAccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.initially_invalid == expected_value


@pytest.mark.parametrize(
    "audit_field_name, audit_field_value, expected_value",
    [
        ("archive_audit_retest_scope_state", "present", True),
        ("archive_audit_retest_scope_state", "not-present", False),
        ("archive_audit_retest_scope_state", "incomplete", False),
        ("archive_audit_retest_scope_state", "other", False),
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

    accessibility_statement_check: ArchiveAccessibilityStatementCheck = (
        ArchiveAccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
    )

    assert accessibility_statement_check.finally_fixed == expected_value


@pytest.mark.parametrize(
    "audit_field_name, audit_field_value, expected_value",
    [
        ("archive_audit_retest_scope_state", "present", False),
        ("archive_audit_retest_scope_state", "not-present", True),
        ("archive_audit_retest_scope_state", "incomplete", True),
        ("archive_audit_retest_scope_state", "other", True),
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

    accessibility_statement_check: ArchiveAccessibilityStatementCheck = (
        ArchiveAccessibilityStatementCheck(field_name_prefix="scope", audit=audit)
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

    for count, field_name_prefix in enumerate(
        ARCHIVE_ACCESSIBILITY_STATEMENT_CHECK_PREFIXES
    ):
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

    audit.archive_scope_state = SCOPE_STATE_VALID

    assert audit.accessibility_statement_initially_invalid_checks_count == 11


def test_audit_accessibility_statement_fixed_count():
    """
    Test that an audit has the expected number of fixed accessibility statement
    checks.
    """
    audit: Audit = Audit()

    assert audit.fixed_accessibility_statement_checks_count == 0

    audit.archive_audit_retest_scope_state = SCOPE_STATE_VALID

    assert audit.fixed_accessibility_statement_checks_count == 1


def test_audit_accessibility_statement_finally_invalid():
    """
    Test that an audit has the expected finally invalid accessibility statement
    checks.
    """
    audit: Audit = Audit()

    assert len(audit.finally_invalid_accessibility_statement_checks) == 12

    audit.archive_audit_retest_scope_state = SCOPE_STATE_VALID

    assert len(audit.finally_invalid_accessibility_statement_checks) == 11


def test_statement_check_str():
    """Tests an StatementCheck __str__ contains the expected string"""
    statement_check: StatementCheck = StatementCheck(label="Label")

    assert statement_check.__str__() == "Label (Custom statement issues)"

    statement_check.success_criteria = "Success criteria"

    assert (
        statement_check.__str__() == "Label: Success criteria (Custom statement issues)"
    )


@pytest.mark.django_db
def test_statement_check_results_str():
    """Tests an StatementCheckResult __str__ contains the expected string"""
    audit: Audit = create_audit_and_statement_check_results()
    statement_check_result: StatementCheckResult = (
        audit.overview_statement_check_results.first()
    )

    assert (
        statement_check_result.__str__()
        == f"{audit} | {statement_check_result.statement_check}"
    )

    custom_statement_check_result: StatementCheckResult = (
        audit.custom_statement_check_results.first()
    )

    assert custom_statement_check_result.__str__() == f"{audit} | Custom"


@pytest.mark.django_db
def test_audit_statement_check_results():
    """
    Tests an audit.statement_check_results contains the matching statement check
    results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    statement_check_results: StatementCheckResult = StatementCheckResult.objects.filter(
        audit=audit
    )

    assertQuerysetEqual(audit.statement_check_results, statement_check_results)


@pytest.mark.django_db
def test_audit_uses_statement_checks():
    """
    Tests an audit.uses_statement_checks shows if statement check results exist
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert audit.uses_statement_checks is False

    audit: Audit = create_audit_and_statement_check_results()

    assert audit.uses_statement_checks is True


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
        ("custom", "custom"),
    ],
)
@pytest.mark.django_db
def test_audit_specific_statement_check_results(type, attr):
    """
    Tests specific audit statement_check_results property contains the matching
    statement check results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    statement_check_results: StatementCheckResult = StatementCheckResult.objects.filter(
        audit=audit, type=type
    )

    assertQuerysetEqual(
        getattr(audit, f"{attr}_statement_check_results"),
        statement_check_results,
    )


@pytest.mark.django_db
def test_audit_overview_statement_checks_complete():
    """Tests audit overview_statement_checks_complete property"""
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.overview_statement_checks_complete is True

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = STATEMENT_CHECK_NOT_TESTED
        statement_check_result.save()
        break

    assert audit.overview_statement_checks_complete is False


@pytest.mark.django_db
def test_audit_failed_statement_check_results():
    """
    Tests an audit.failed_statement_check_results contains the failed statement
    check results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    failed_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit, check_result_state=STATEMENT_CHECK_NO
        )
    )

    assertQuerysetEqual(
        audit.failed_statement_check_results, failed_statement_check_results
    )


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
        ("custom", "custom"),
    ],
)
@pytest.mark.django_db
def test_audit_specific_outstanding_statement_check_results(type, attr):
    """
    Tests specific audit outstanding_statement_check_results property contains the
    matching failed statement check results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    failed_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit, type=type, check_result_state=STATEMENT_CHECK_NO
        )
    )

    assertQuerysetEqual(
        getattr(audit, f"{attr}_outstanding_statement_check_results"),
        failed_statement_check_results,
    )


@pytest.mark.django_db
def test_audit_statement_check_result_statement_found():
    """
    Tests an audit.statement_check_result_statement_found shows if all
    overview statement checks have passed
    """
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.statement_check_result_statement_found is False

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = STATEMENT_CHECK_YES
        statement_check_result.save()

    assert audit.statement_check_result_statement_found is True


@pytest.mark.django_db
def test_audit_all_overview_statement_checks_have_passed():
    """
    Tests an audit.all_overview_statement_checks_have_passed shows if all
    statement check results have passed on test or retest
    """
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.all_overview_statement_checks_have_passed is False

    overview_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit,
            type=STATEMENT_CHECK_TYPE_OVERVIEW,
        )
    )
    for statement_check_result in overview_statement_check_results:
        statement_check_result.check_result_state = STATEMENT_CHECK_YES
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is True

    for statement_check_result in overview_statement_check_results:
        statement_check_result.check_result_state = STATEMENT_CHECK_NO
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is False

    for statement_check_result in overview_statement_check_results:
        statement_check_result.retest_state = STATEMENT_CHECK_YES
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is True


@pytest.mark.django_db
def test_all_overview_statement_checks_have_passed():
    """
    Tests an audit has all statement checks on overview set to yes.
    """
    audit: Audit = create_audit_and_statement_check_results()
    overview_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit,
            type=STATEMENT_CHECK_TYPE_OVERVIEW,
        )
    )

    assert audit.all_overview_statement_checks_have_passed is False

    for overview_statement_check_result in overview_statement_check_results:
        overview_statement_check_result.check_result_state = STATEMENT_CHECK_YES
        overview_statement_check_result.save()

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.all_overview_statement_checks_have_passed is True


def test_report_accessibility_issues():
    """Test the accessibility issues includes user-edited text"""
    audit: Audit = Audit(
        archive_accessibility_statement_deadline_not_complete_wording=INCOMPLETE_DEADLINE_TEXT,
        archive_accessibility_statement_deadline_not_sufficient_wording=INSUFFICIENT_DEADLINE_TEXT,
    )

    assert audit.report_accessibility_issues == []

    audit.archive_accessibility_statement_deadline_not_complete = BOOLEAN_TRUE

    assert audit.report_accessibility_issues == [INCOMPLETE_DEADLINE_TEXT]

    audit.archive_accessibility_statement_deadline_not_sufficient = BOOLEAN_TRUE

    assert audit.report_accessibility_issues == [
        INCOMPLETE_DEADLINE_TEXT,
        INSUFFICIENT_DEADLINE_TEXT,
    ]


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
        ("custom", "custom"),
    ],
)
@pytest.mark.django_db
def test_audit_specific_outstanding_statement_check_results(type, attr):
    """
    Tests specific audit outstanding_statement_check_results property contains
    the expected statement check results.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    statement_check: StatementCheck = StatementCheck.objects.filter(type=type).first()
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=type,
        statement_check=statement_check,
    )
    attr_name: str = f"{attr}_outstanding_statement_check_results"

    assert getattr(audit, attr_name).exists() is False
    assert audit.outstanding_statement_check_results.count() == 0

    statement_check_result.check_result_state = STATEMENT_CHECK_NO
    statement_check_result.save()

    assert getattr(audit, attr_name).exists() is True
    assert getattr(audit, attr_name).first() == statement_check_result
    assert audit.outstanding_statement_check_results.count() == 1

    statement_check_result.retest_state = STATEMENT_CHECK_YES
    statement_check_result.save()

    assert getattr(audit, attr_name).exists() is False
    assert audit.outstanding_statement_check_results.count() == 0


@pytest.mark.django_db
def test_fixed_statement_checks_are_returned():
    """
    Tests fixed statement checks are those which initially failed but
    passed on a retest.
    """
    audit: Audit = create_audit_and_statement_check_results()
    statement_check_results: QuerySet[
        StatementCheckResult
    ] = StatementCheckResult.objects.filter(
        audit=audit,
    )

    assert statement_check_results.count() > 2

    passed_statement_check_result: StatementCheckResult = (
        statement_check_results.first()
    )
    passed_statement_check_result.check_result_state = STATEMENT_CHECK_YES
    passed_statement_check_result.retest_state = STATEMENT_CHECK_YES
    passed_statement_check_result.save()

    fixed_statement_check_result: StatementCheckResult = statement_check_results.last()
    fixed_statement_check_result.check_result_state = STATEMENT_CHECK_NO
    fixed_statement_check_result.retest_state = STATEMENT_CHECK_YES
    fixed_statement_check_result.save()

    assert audit.passed_statement_check_results.first() == passed_statement_check_result
    assert audit.fixed_statement_check_results.first() == fixed_statement_check_result


@pytest.mark.django_db
def test_set_accessibility_statement_state_called_on_statement_page_update():
    """
    Test that saving a statement page triggers a setting of the statement
    state on the case.
    """
    case: Case = Case.objects.create()
    mock_set_accessibility_statement_states = Mock()
    case.set_accessibility_statement_states = mock_set_accessibility_statement_states
    audit: Audit = Audit.objects.create(case=case)

    Page.objects.create(audit=audit, page_type=PAGE_TYPE_STATEMENT)

    mock_set_accessibility_statement_states.assert_called_once()


@pytest.mark.django_db
def test_set_accessibility_statement_state_not_called_on_non_statement_page_update():
    """
    Test that saving a non-statement page does not trigger a setting of the statement
    state on the case.
    """
    case: Case = Case.objects.create()
    mock_set_accessibility_statement_states = Mock()
    case.set_accessibility_statement_states = mock_set_accessibility_statement_states
    audit: Audit = Audit.objects.create(case=case)

    Page.objects.create(audit=audit)

    mock_set_accessibility_statement_states.assert_not_called()


@pytest.mark.django_db
def test_set_accessibility_statement_state_called_on_statement_check_update():
    """
    Test that saving a statement check triggers a setting of the statement
    state on the case.
    """
    case: Case = Case.objects.create()
    mock_set_accessibility_statement_states = Mock()
    case.set_accessibility_statement_states = mock_set_accessibility_statement_states
    audit: Audit = Audit.objects.create(case=case)
    statement_check: StatementCheck = StatementCheck.objects.filter(type=type).first()

    StatementCheckResult.objects.create(
        audit=audit,
        type=type,
        statement_check=statement_check,
    )

    mock_set_accessibility_statement_states.assert_called_once()
