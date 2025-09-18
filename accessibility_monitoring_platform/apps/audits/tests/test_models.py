"""
Tests for cases models
"""

from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.db.models.query import QuerySet
from pytest_django.asserts import assertQuerySetEqual

from ...common.models import Boolean
from ...simplified.models import SimplifiedCase
from ..models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
    build_issue_identifier,
)
from ..utils import create_checkresults_for_retest

TODAY = date.today()
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
STATEMENT_LINK: str = "https://example.com/accessibility-statement"
ACCESSIBILITY_PAGE_STATEMENT_CHECK_ID: int = 1
REPORT_COMMENT: str = "Report comment"


def create_retest_and_retest_check_results(
    simplified_case: SimplifiedCase | None = None,
):
    """Create retest and associated data"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    if simplified_case is None:
        simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
        audit: Audit = Audit.objects.create(simplified_case=simplified_case)
        home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
        statement_page: Page = Page.objects.create(
            audit=audit, page_type=Page.Type.STATEMENT
        )
        home_page_check_result: CheckResult = CheckResult.objects.create(
            audit=audit,
            page=home_page,
            check_result_state=CheckResult.Result.ERROR,
            retest_state=CheckResult.RetestResult.NOT_FIXED,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
        statement_page_check_result: CheckResult = CheckResult.objects.create(
            audit=audit,
            page=statement_page,
            check_result_state=CheckResult.Result.NO_ERROR,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )

        retest: Retest = Retest.objects.create(simplified_case=simplified_case)
        home_retest_page: RetestPage = RetestPage.objects.create(
            retest=retest,
            page=home_page,
        )
        statement_retest_page: RetestPage = RetestPage.objects.create(
            retest=retest,
            page=statement_page,
        )
        RetestCheckResult.objects.create(
            retest=retest,
            retest_page=home_retest_page,
            check_result=home_page_check_result,
            retest_state=CheckResult.RetestResult.NOT_FIXED,
        )
        RetestCheckResult.objects.create(
            retest=retest,
            retest_page=statement_retest_page,
            check_result=statement_page_check_result,
            retest_state=CheckResult.RetestResult.FIXED,
        )
        return retest
    else:
        last_retest: Retest = Retest.objects.filter(
            simplified_case=simplified_case
        ).first()
        new_retest: Retest = Retest.objects.create(simplified_case=simplified_case)
        for last_retest_page in last_retest.retestpage_set.all():
            new_retest_page = RetestPage.objects.create(
                retest=new_retest,
                page=last_retest_page.page,
            )
            for (
                last_retest_check_result
            ) in last_retest_page.retestcheckresult_set.all():
                RetestCheckResult.objects.create(
                    retest=new_retest,
                    retest_page=new_retest_page,
                    check_result=last_retest_check_result.check_result,
                )
        return new_retest


def create_audit_and_pages() -> Audit:
    """Create an audit with all types of page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    for page_type in [
        Page.Type.EXTRA,
        Page.Type.HOME,
        Page.Type.CONTACT,
        Page.Type.STATEMENT,
        Page.Type.PDF,
        Page.Type.FORM,
    ]:
        Page.objects.create(audit=audit, page_type=page_type)
    Page.objects.create(audit=audit, page_type=Page.Type.EXTRA, is_deleted=True)
    return audit


def create_audit_and_statement_check_results() -> Audit:
    """Create an audit with all types of statement checks"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    for count, statement_check in enumerate(StatementCheck.objects.all()):
        check_result_state: str = (
            StatementCheckResult.Result.NO
            if count % 2 == 0
            else StatementCheckResult.Result.YES
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


def create_retest_and_statement_check_results() -> Retest:
    """Create a retest with all types of statement checks"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    for count, statement_check in enumerate(StatementCheck.objects.all()):
        check_result_state: str = (
            StatementCheckResult.Result.NO
            if count % 2 == 0
            else StatementCheckResult.Result.YES
        )
        RetestStatementCheckResult.objects.create(
            retest=retest,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=check_result_state,
        )
    RetestStatementCheckResult.objects.create(
        retest=retest,
        comment="Custom statement issue",
    )
    return retest


def create_audit_and_check_results() -> Audit:
    """Create an audit with failed check results"""
    html_wcag_definitions: list[WcagDefinition] = [
        WcagDefinition.objects.create(
            type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
        ),
        WcagDefinition.objects.create(
            type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
        ),
    ]
    pdf_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )

    audit: Audit = create_audit_and_pages()
    pages: QuerySet[Page] = audit.page_audit.all()

    for page in pages:
        check_result_state: str = (
            CheckResult.Result.ERROR
            if page.page_type in [Page.Type.HOME, Page.Type.PDF]
            else CheckResult.Result.NO_ERROR
        )
        if page.page_type == Page.Type.PDF:
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
def test_audit_absolute_url():
    """Test Audit.get_absolute_url()"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.get_absolute_url() == "/audits/1/edit-audit-metadata/"


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

    assert audit.every_page.last().page_type == Page.Type.STATEMENT
    assert list(audit.every_page)[-2].page_type == Page.Type.PDF


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
def test_html_page_page_title():
    """
    Test Page.page_title is as expected for HTML page
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.accessibility_statement_page

    assert page.page_title == "Accessibility statement page"


@pytest.mark.django_db
def test_pdf_page_page_title():
    """
    Test Page.page_title is as expected for PDF page
    """
    create_audit_and_pages()
    page: Page = Page.objects.get(page_type=Page.Type.PDF)
    page.name = "File"
    page.save()

    assert page.page_title == "File"


@pytest.mark.django_db
def test_audit_testable_pages_returns_expected_page():
    """
    Deleted, not found and pages without URLs excluded.
    """
    audit: Audit = create_audit_and_pages()
    testable_page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.HOME,
        url="https://example.com",
        not_found="yes",
    )

    assert len(audit.testable_pages) == 1
    assert audit.testable_pages[0].id == testable_page.id


@pytest.mark.django_db
def test_audit_retestable_pages_returns_expected_page():
    """
    Deleted, not found, pages without URLs and missing pages excluded.
    """
    audit: Audit = create_audit_and_pages()
    retestable_page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.HOME,
        url="https://example.com",
        not_found="yes",
        retest_page_missing_date=date.today(),
    )

    assert len(audit.retestable_pages) == 1
    assert audit.retestable_pages[0].id == retestable_page.id


@pytest.mark.django_db
def test_audit_missing_at_retest_pages():
    """Test missing at retest pages."""
    audit: Audit = create_audit_and_pages()
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )

    assert len(audit.missing_at_retest_pages) == 0

    page.retest_page_missing_date = TODAY
    page.save()

    assert len(audit.missing_at_retest_pages) == 1
    assert audit.missing_at_retest_pages[0] == page


@pytest.mark.django_db
def test_audit_missing_at_retest_check_results():
    """Test missing at retest check results."""
    audit: Audit = create_audit_and_pages()
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert len(audit.missing_at_retest_check_results) == 0

    page.retest_page_missing_date = TODAY
    page.save()

    assert len(audit.missing_at_retest_check_results) == 1
    assert audit.missing_at_retest_check_results[0] == check_result


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
                if check.check_result_state == CheckResult.Result.ERROR
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

    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.PDF)
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

    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.PDF)
    page.retest_page_missing_date = date.today()
    page.save()

    assert len(audit.failed_check_results) == 2


@pytest.mark.django_db
def test_audit_failed_check_results_for_is_contact_page_page_not_returned():
    """
    Test failed_check_results attribute of audit returns only check results where failed is "yes"
    and associated page has not got is_contact_page (used for form pages) is not set.
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_check_results) == 3

    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.PDF)
    page.is_contact_page = Boolean.YES
    page.save()

    assert len(audit.failed_check_results) == 2


@pytest.mark.django_db
def test_audit_accessibility_statement_page_returns_page():
    """
    Accessibility Statement page returned
    """
    audit: Audit = create_audit_and_pages()
    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.STATEMENT)

    assert audit.accessibility_statement_page == page


@pytest.mark.django_db
def test_page_all_check_results_returns_check_results():
    """
    Test all_check_results attribute of page returns expected check results.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)

    assert len(home_page.all_check_results) == 2
    assert home_page.all_check_results[0].type == WcagDefinition.Type.AXE
    assert home_page.all_check_results[1].type == WcagDefinition.Type.MANUAL


@pytest.mark.django_db
def test_page_all_check_results_returns_pdf_check_results_last():
    """
    Test all_check_results attribute of page returns PDF-page check results last.
    """
    audit: Audit = create_audit_and_check_results()

    assert len(audit.failed_check_results) == 3
    assert audit.failed_check_results.last().page.page_type == Page.Type.PDF


@pytest.mark.django_db
def test_page_page_title():
    """Test Page.page_title returns expected title."""
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    pdf_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.PDF)

    assert home_page.page_title == "Home page"
    assert pdf_page.page_title == "PDF"

    home_page.name = "Homepage"
    home_page.save()
    pdf_page.name = "Document"
    pdf_page.save()

    assert home_page.page_title == "Homepage page"
    assert pdf_page.page_title == "Document"


@pytest.mark.django_db
def test_check_result_returns_id_and_fields_for_retest():
    """
    Test check_result attribute of form_initial returns id and fields for retest form.
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    check_result: CheckResult = home_page.all_check_results[0]

    assert check_result.retest_form_initial == {
        "id": check_result.id,
        "retest_state": CheckResult.RetestResult.NOT_RETESTED,
        "retest_notes": "",
        "check_result": check_result,
    }


def test_wcag_definition_strings():
    """
    Test WCAG definitions return expected string values.
    """
    wcag_definition: WcagDefinition = WcagDefinition(
        type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )
    assert str(wcag_definition) == f"{WCAG_TYPE_PDF_NAME} (PDF)"

    wcag_definition_with_description: WcagDefinition = WcagDefinition(
        type=WcagDefinition.Type.PDF,
        name=WCAG_TYPE_PDF_NAME,
        description=WCAG_DESCRIPTION,
    )
    assert (
        str(wcag_definition_with_description)
        == f"{WCAG_TYPE_PDF_NAME}: {WCAG_DESCRIPTION} (PDF)"
    )


@pytest.mark.django_db
def test_wcag_definition_start_end_date_range():
    """
    Test that an WCAG definition within a date range returned.
    """
    WcagDefinition.objects.all().delete()
    past_date: date = date(2020, 1, 1)
    current_date: date = date(2023, 1, 1)
    future_date: date = date(2024, 1, 1)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    WcagDefinition.objects.create(date_end=past_date)
    WcagDefinition.objects.create(date_start=future_date)

    assert WcagDefinition.objects.all().count() == 3

    assert WcagDefinition.objects.on_date(current_date).count() == 1

    assert WcagDefinition.objects.on_date(current_date).first() == wcag_definition


@pytest.mark.django_db
def test_accessibility_statement_initially_found():
    """
    Test that an accessibility statement was initially found.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    # No page
    assert audit.accessibility_statement_initially_found is False

    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    # Not found flag not set
    assert audit.accessibility_statement_initially_found is True

    statement_page.added_stage = StatementPage.AddedStage.TWELVE_WEEK
    statement_page.save()

    # Not found flag set
    assert audit.accessibility_statement_initially_found is False


@pytest.mark.django_db
def test_accessibility_statement_found():
    """
    Test that an accessibility statement was found.
    """
    audit: Audit = create_audit_and_pages()
    statement_page: StatementPage = StatementPage.objects.create(
        audit=audit, url=STATEMENT_LINK
    )

    assert audit.accessibility_statement_found is True

    statement_page.added_stage = StatementPage.AddedStage.TWELVE_WEEK
    statement_page.save()

    assert audit.accessibility_statement_found is True


@pytest.mark.django_db
def test_audit_updated_updated():
    """Test the audit updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_UPDATED)):
        audit.save()

    assert audit.updated == DATETIME_AUDIT_UPDATED


@pytest.mark.django_db
def test_page_updated_updated():
    """Test the page updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        page.save()

    assert page.updated == DATETIME_PAGE_UPDATED


@pytest.mark.django_db
def test_check_result_updated_updated():
    """Test the check result updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=WcagDefinition.Type.AXE,
        wcag_definition=wcag_definition,
    )
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_UPDATED)
    ):
        check_result.save()

    assert check_result.updated == DATETIME_CHECK_RESULT_UPDATED


@pytest.mark.django_db
def test_audit_fixed_check_results():
    """
    Test that fixed_check_results returns the expected values.
    """
    audit: Audit = create_audit_and_check_results()

    assert audit.fixed_check_results.count() == 0

    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    check_result: CheckResult = home_page.all_check_results[0]
    check_result.retest_state = CheckResult.RetestResult.FIXED
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
    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.unfixed_check_results.count() == 2


def test_statement_check_str():
    """Tests an StatementCheck __str__ contains the expected string"""
    statement_check: StatementCheck = StatementCheck(label="Label")

    assert statement_check.__str__() == "Label (Custom statement issues)"

    statement_check.success_criteria = "Success criteria"

    assert (
        statement_check.__str__() == "Label: Success criteria (Custom statement issues)"
    )


@pytest.mark.django_db
def test_statement_check_result_edit_initial_url_name():
    """
    Tests an StatementCheckResult edit_initial_url_name contains the expected string
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_check: StatementCheck = StatementCheck.objects.create(
        type=StatementCheck.Type.COMPLIANCE
    )
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit, statement_check=statement_check, type=statement_check.type
    )

    assert (
        statement_check_result.edit_initial_url_name
        == "audits:edit-statement-compliance"
    )


@pytest.mark.django_db
def test_statement_check_edit_12_week_url_name():
    """
    Tests an StatementCheckResult edit_12_week_url_name contains the expected string
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_check: StatementCheck = StatementCheck.objects.create(
        type=StatementCheck.Type.COMPLIANCE
    )
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit, statement_check=statement_check, type=statement_check.type
    )

    assert (
        statement_check_result.edit_12_week_url_name
        == "audits:edit-retest-statement-compliance"
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
        == f"{audit} | {statement_check_result.statement_check} [{statement_check_result.issue_identifier}]"
    )

    custom_statement_check_result: StatementCheckResult = (
        audit.custom_statement_check_results.first()
    )

    assert (
        custom_statement_check_result.__str__()
        == f"{audit} | Custom [{custom_statement_check_result.issue_identifier}]"
    )


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

    assertQuerySetEqual(audit.statement_check_results, statement_check_results)


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

    assertQuerySetEqual(
        getattr(audit, f"{attr}_statement_check_results"),
        statement_check_results,
    )


@pytest.mark.django_db
def test_audit_statement_found_check():
    """Tests audit statement_found_check property"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_found_check: StatementCheck = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).first()
    statement_found_check_result: StatementCheckResult = (
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_found_check.type,
            statement_check=statement_found_check,
        )
    )

    assert audit.statement_found_check == statement_found_check_result


@pytest.mark.django_db
def test_audit_statement_structure_check():
    """Tests audit statement_structure_check property"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_structure_check: StatementCheck = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).last()
    statement_structure_check_result: StatementCheckResult = (
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_structure_check.type,
            statement_check=statement_structure_check,
        )
    )

    assert audit.statement_structure_check == statement_structure_check_result


@pytest.mark.django_db
def test_audit_overview_statement_checks_complete():
    """Tests audit overview_statement_checks_complete property"""
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.overview_statement_checks_complete is True

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = (
            StatementCheckResult.Result.NOT_TESTED
        )
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
            audit=audit, check_result_state=StatementCheckResult.Result.NO
        )
    )

    assertQuerySetEqual(
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
    ],
)
@pytest.mark.django_db
def test_audit_contains_specific_outstanding_statement_check_results(type, attr):
    """
    Tests audit contains specific statement check results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    failed_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit, type=type, check_result_state=StatementCheckResult.Result.NO
        )
    )

    assertQuerySetEqual(
        getattr(audit, f"{attr}_outstanding_statement_check_results"),
        failed_statement_check_results,
    )


@pytest.mark.django_db
def test_audit_contains_custom_outstanding_statement_check_results():
    """
    Tests audit contains specific statement check results.
    """
    audit: Audit = create_audit_and_statement_check_results()
    failed_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit, type=StatementCheck.Type.CUSTOM
        )
    )

    assertQuerySetEqual(
        audit.custom_outstanding_statement_check_results,
        failed_statement_check_results,
    )


@pytest.mark.django_db
def test_audit_outstanding_statement_check_results_includes_new_failures():
    """
    Tests specific audit outstanding_statement_check_results property contains any
    errors found for the first time on 12-week retest.
    """
    audit: Audit = create_audit_and_statement_check_results()
    untested_statement_check_result: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit, check_result_state=StatementCheckResult.Result.NOT_TESTED
        ).first()
    )
    untested_statement_check_result.retest_state = StatementCheckResult.Result.NO
    untested_statement_check_result.save()

    assert untested_statement_check_result in audit.outstanding_statement_check_results


@pytest.mark.django_db
def test_audit_statement_check_result_statement_found():
    """
    Tests an audit.statement_check_result_statement_found shows if all
    overview statement checks have passed
    """
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.statement_check_result_statement_found is False

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
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
            type=StatementCheck.Type.OVERVIEW,
        )
    )
    for statement_check_result in overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is True

    for statement_check_result in overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.NO
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is False

    for statement_check_result in overview_statement_check_results:
        statement_check_result.retest_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert audit.all_overview_statement_checks_have_passed is True


@pytest.mark.django_db
def test_audit_all_overview_statement_checks_have_passed_when_none():
    """
    Tests audit all overview statement checks have passed is false when
    there are no such checks.
    """
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.all_overview_statement_checks_have_passed is False


@pytest.mark.django_db
def test_all_overview_statement_checks_have_passed():
    """
    Tests an audit has all statement checks on overview set to yes.
    """
    audit: Audit = create_audit_and_statement_check_results()
    overview_statement_check_results: StatementCheckResult = (
        StatementCheckResult.objects.filter(
            audit=audit,
            type=StatementCheck.Type.OVERVIEW,
        )
    )

    assert audit.all_overview_statement_checks_have_passed is False

    for overview_statement_check_result in overview_statement_check_results:
        overview_statement_check_result.check_result_state = (
            StatementCheckResult.Result.YES
        )
        overview_statement_check_result.save()

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.all_overview_statement_checks_have_passed is True


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
    ],
)
@pytest.mark.django_db
def test_audit_specific_outstanding_statement_check_results(type, attr):
    """
    Tests specific audit outstanding_statement_check_results property contains
    the expected statement check results.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_check: StatementCheck = StatementCheck.objects.filter(type=type).first()
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=type,
        statement_check=statement_check,
    )
    attr_name: str = f"{attr}_outstanding_statement_check_results"

    assert getattr(audit, attr_name).exists() is False
    assert audit.outstanding_statement_check_results.count() == 0

    statement_check_result.check_result_state = StatementCheckResult.Result.NO
    statement_check_result.save()

    assert getattr(audit, attr_name).exists() is True
    assert getattr(audit, attr_name).first() == statement_check_result
    assert audit.outstanding_statement_check_results.count() == 1

    statement_check_result.retest_state = StatementCheckResult.Result.YES
    statement_check_result.save()

    assert getattr(audit, attr_name).exists() is False
    assert audit.outstanding_statement_check_results.count() == 0


@pytest.mark.django_db
def test_audit_specific_outstanding_custom_statement_check_results():
    """
    Tests specific audit custom_outstanding_statement_check_results property contains
    the expected statement check results.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.custom_outstanding_statement_check_results.exists() is False
    assert audit.outstanding_statement_check_results.count() == 0

    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=StatementCheck.Type.CUSTOM,
    )

    assert audit.custom_outstanding_statement_check_results.exists() is True
    assert (
        audit.custom_outstanding_statement_check_results.first()
        == statement_check_result
    )
    assert audit.outstanding_statement_check_results.count() == 1

    statement_check_result.retest_state = StatementCheckResult.Result.YES
    statement_check_result.save()

    assert audit.custom_outstanding_statement_check_results.exists() is False
    assert audit.outstanding_statement_check_results.count() == 0


@pytest.mark.django_db
def test_fixed_statement_checks_are_returned():
    """
    Tests fixed statement checks are those which initially failed but
    passed on a retest.
    """
    audit: Audit = create_audit_and_statement_check_results()
    statement_check_results: QuerySet[StatementCheckResult] = (
        StatementCheckResult.objects.filter(
            audit=audit,
        )
    )

    assert statement_check_results.count() > 2

    passed_statement_check_result: StatementCheckResult = (
        statement_check_results.first()
    )
    passed_statement_check_result.check_result_state = StatementCheckResult.Result.YES
    passed_statement_check_result.retest_state = StatementCheckResult.Result.YES
    passed_statement_check_result.save()

    fixed_statement_check_result: StatementCheckResult = statement_check_results.last()
    fixed_statement_check_result.check_result_state = StatementCheckResult.Result.NO
    fixed_statement_check_result.retest_state = StatementCheckResult.Result.YES
    fixed_statement_check_result.save()

    assert audit.passed_statement_check_results.first() == passed_statement_check_result
    assert audit.fixed_statement_check_results.first() == fixed_statement_check_result


@pytest.mark.django_db
def test_statement_check_start_end_date_range():
    """
    Test that an statement check within a date range returned.
    """
    StatementCheck.objects.all().delete()
    past_date: date = date(2020, 1, 1)
    current_date: date = date(2023, 1, 1)
    future_date: date = date(2024, 1, 1)
    wcag_definition: StatementCheck = StatementCheck.objects.create()
    StatementCheck.objects.create(date_end=past_date)
    StatementCheck.objects.create(date_start=future_date)

    assert StatementCheck.objects.all().count() == 3

    assert StatementCheck.objects.on_date(current_date).count() == 1

    assert StatementCheck.objects.on_date(current_date).first() == wcag_definition


def test_retest_str():
    """Test Retest.__str__"""
    assert str(Retest(id_within_case=0)) == "12-week retest"
    assert str(Retest(id_within_case=1)) == "Retest #1"


@pytest.mark.django_db
def test_fixed_checks_count_at_12_week():
    """Test fixed checks count at 12-week retest"""
    audit: Audit = create_audit_and_check_results()
    retest: Retest = Retest.objects.create(simplified_case=audit.simplified_case)

    assert retest.fixed_checks_count == 0

    check_result: CheckResult = audit.checkresult_audit.all().first()
    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    assert retest.fixed_checks_count == 1

    check_result.page.not_found = Boolean.YES
    check_result.page.save()

    assert retest.fixed_checks_count == 0


@pytest.mark.django_db
def test_fixed_checks_count_in_retests():
    """Test fixed checks count at equality body restart"""
    audit: Audit = create_audit_and_check_results()
    page: Page = audit.page_audit.all().first()
    retest: Retest = Retest.objects.create(simplified_case=audit.simplified_case)
    retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )
    check_result: CheckResult = audit.checkresult_audit.all().first()
    retest_check_result: RetestCheckResult = RetestCheckResult.objects.create(
        retest=retest,
        retest_page=retest_page,
        check_result=check_result,
    )

    assert retest.fixed_checks_count == 0

    retest_check_result.retest_state = CheckResult.RetestResult.FIXED
    retest_check_result.save()

    assert retest.fixed_checks_count == 1

    retest_page.page.not_found = Boolean.YES
    retest_page.page.save()

    assert retest.fixed_checks_count == 0


@pytest.mark.django_db
def test_retest_is_incomplete():
    """Test retest compliance status is still default"""
    audit: Audit = create_audit_and_check_results()
    retest: Retest = Retest.objects.create(simplified_case=audit.simplified_case)

    assert retest.is_incomplete is True

    retest.retest_compliance_state = Retest.Compliance.COMPLIANT

    assert retest.is_incomplete is False


@pytest.mark.django_db
def test_returning_original_retest():
    """Test original retest contains the retest with id_within_case of 0"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    first_retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=0
    )
    second_retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=1
    )

    assert first_retest.original_retest == first_retest
    assert second_retest.original_retest == first_retest


@pytest.mark.django_db
def test_returning_previous_retest():
    """
    Test previous retest contains the retest with next lowest id_within_case
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest_0: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=0
    )
    retest_1: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=1
    )
    retest_2: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=2
    )

    assert retest_0.previous_retest is None
    assert retest_1.previous_retest == retest_0
    assert retest_2.previous_retest == retest_1


@pytest.mark.django_db
def test_returning_latest_retest():
    """
    Test latest retest contains the most recent retest
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Retest.objects.create(simplified_case=simplified_case, id_within_case=0)
    retest_1: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=1
    )

    assert retest_1.latest_retest == retest_1

    retest_2: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=2
    )

    assert retest_1.latest_retest == retest_2


@pytest.mark.django_db
def test_retest_page_heading():
    """Test heading returned by retest page"""
    retest: Retest = create_retest_and_retest_check_results()
    retest_page: RetestPage = retest.retestpage_set.get(page__page_type=Page.Type.HOME)

    assert retest_page.heading == "Retest #1 | Home"


@pytest.mark.django_db
def test_retest_page_all_check_results():
    """Test all_check_results returned by retest page"""
    retest: Retest = create_retest_and_retest_check_results()
    retest_page: RetestPage = retest.retestpage_set.get(page__page_type=Page.Type.HOME)

    assertQuerySetEqual(
        retest_page.all_check_results, retest_page.retestcheckresult_set.all()
    )


@pytest.mark.django_db
def test_retest_page_unfixed_check_results():
    """Test unfixed_check_results returned by retest page"""
    retest: Retest = create_retest_and_retest_check_results()
    home_retest_page: RetestPage = retest.retestpage_set.get(
        page__page_type=Page.Type.HOME
    )
    statement_retest_page: RetestPage = retest.retestpage_set.get(
        page__page_type=Page.Type.STATEMENT
    )

    assert home_retest_page.unfixed_check_results.count() == 1
    assert (
        home_retest_page.unfixed_check_results.first().retest_state
        == CheckResult.RetestResult.NOT_FIXED
    )
    assert statement_retest_page.unfixed_check_results.count() == 0


@pytest.mark.django_db
def test_retest_page_original_check_results():
    """Test original_check_results returned by retest page"""
    original_retest: Retest = create_retest_and_retest_check_results()
    original_retest.id_within_case = 0
    original_retest.save()
    page: Page = original_retest.retestpage_set.all().first().page
    retest: Retest = Retest.objects.create(
        simplified_case=original_retest.simplified_case
    )
    retest_page: RetestPage = RetestPage.objects.create(retest=retest, page=page)

    assert retest_page.original_check_results.count() == 1
    assert retest_page.original_check_results.first().retest_page.page == page


@pytest.mark.django_db
def test_retest_check_result_original_retest_check_result():
    """Test original_retest_check_result returned by retest retest_check_result"""
    original_retest: Retest = create_retest_and_retest_check_results()
    original_retest.id_within_case = 0
    original_retest.save()
    original_retest_page: RetestPage = original_retest.retestpage_set.all().first()
    original_retest_check_result: RetestCheckResult = (
        original_retest_page.retestcheckresult_set.all().first()
    )

    new_retest: Retest = create_retest_and_retest_check_results(
        simplified_case=original_retest.simplified_case
    )
    new_retest_page: RetestPage = new_retest.retestpage_set.all().first()
    new_retest_check_result: RetestCheckResult = (
        new_retest_page.retestcheckresult_set.all().first()
    )

    assert new_retest_check_result.original_retest_check_result is not None
    assert (
        new_retest_check_result.original_retest_check_result
        == original_retest_check_result
    )


@pytest.mark.django_db
def test_retest_check_result_latest_retest_check_result():
    """Test latest_retest_check_result returned by retest retest_check_result"""
    original_retest: Retest = create_retest_and_retest_check_results()
    original_retest.id_within_case = 0
    original_retest.save()
    original_retest_page: RetestPage = original_retest.retestpage_set.all().first()
    original_retest_check_result: RetestCheckResult = (
        original_retest_page.retestcheckresult_set.all().first()
    )

    new_retest: Retest = create_retest_and_retest_check_results(
        simplified_case=original_retest.simplified_case
    )
    new_retest_page: RetestPage = new_retest.retestpage_set.all().first()
    new_retest_check_result: RetestCheckResult = (
        new_retest_page.retestcheckresult_set.all().first()
    )

    assert (
        original_retest_check_result.latest_retest_check_result
        == new_retest_check_result
    )


@pytest.mark.django_db
def test_retest_check_result_previous_retest_check_result():
    """Test previous_retest_check_result returned by retest retest_check_result"""
    original_retest: Retest = create_retest_and_retest_check_results()
    original_retest.id_within_case = 0
    original_retest.save()
    original_retest_page: RetestPage = original_retest.retestpage_set.all().first()
    original_retest_check_result: RetestCheckResult = (
        original_retest_page.retestcheckresult_set.all().first()
    )

    new_retest: Retest = create_retest_and_retest_check_results(
        simplified_case=original_retest.simplified_case
    )
    new_retest_page: RetestPage = new_retest.retestpage_set.all().first()
    new_retest_check_result: RetestCheckResult = (
        new_retest_page.retestcheckresult_set.all().first()
    )

    assert (
        new_retest_check_result.previous_retest_check_result
        == original_retest_check_result
    )


@pytest.mark.django_db
def test_retest_check_result_all_retest_check_result():
    """Test all_retest_check_result returned by retest retest_check_result"""
    original_retest: Retest = create_retest_and_retest_check_results()
    original_retest.id_within_case = 0
    original_retest.save()
    original_retest_page: RetestPage = original_retest.retestpage_set.all().first()
    original_retest_check_result: RetestCheckResult = (
        original_retest_page.retestcheckresult_set.all().first()
    )

    new_retest: Retest = create_retest_and_retest_check_results(
        simplified_case=original_retest.simplified_case
    )
    new_retest_page: RetestPage = new_retest.retestpage_set.all().first()
    new_retest_check_result: RetestCheckResult = (
        new_retest_page.retestcheckresult_set.all().first()
    )

    assert new_retest_check_result.all_retest_check_results.count() == 2
    assert (
        new_retest_check_result.all_retest_check_results.first()
        == original_retest_check_result
    )
    assert (
        new_retest_check_result.all_retest_check_results.last()
        == new_retest_check_result
    )


@pytest.mark.django_db
def test_audit_statement_pages():
    """Test audit statement pages"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert not audit.statement_pages

    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    assert audit.statement_pages.count() == 1
    assert audit.statement_pages.first() == statement_page

    statement_page.is_deleted = True
    statement_page.save()

    assert not audit.statement_pages


@pytest.mark.django_db
def test_audit_accessibility_statement_initially_found():
    """Test audit statement initially found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.accessibility_statement_initially_found is False

    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    assert audit.accessibility_statement_initially_found is True

    statement_page.added_stage = StatementPage.AddedStage.TWELVE_WEEK
    statement_page.save()

    assert audit.accessibility_statement_initially_found is False


@pytest.mark.django_db
def test_audit_twelve_week_accessibility_statement_found():
    """Test audit statement found at twelve-week retest"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.twelve_week_accessibility_statement_found is False

    statement_page: StatementPage = StatementPage.objects.create(
        audit=audit, added_stage=StatementPage.AddedStage.TWELVE_WEEK
    )

    assert audit.twelve_week_accessibility_statement_found is True

    statement_page.added_stage = StatementPage.AddedStage.INITIAL
    statement_page.save()

    assert audit.twelve_week_accessibility_statement_found is False


@pytest.mark.django_db
def test_audit_accessibility_statement_found():
    """Test audit statement found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.accessibility_statement_found is False

    statement_page: StatementPage = StatementPage.objects.create(
        audit=audit, url=STATEMENT_LINK
    )

    assert audit.accessibility_statement_found is True

    statement_page.is_deleted = True
    statement_page.save()

    assert audit.accessibility_statement_found is False


def test_statement_page_str():
    """
    Test the string representation of the statement page is the backup
    url or url.
    """
    statement_page: StatementPage = StatementPage()

    assert str(statement_page) == ""

    statement_page.backup_url = "backup"

    assert str(statement_page) == "backup"

    statement_page.url = "url"

    assert str(statement_page) == "url"


@pytest.mark.django_db
def test_latest_statement_link_found():
    """
    Test that the latest statement link is returned even when
    it is not on the latest statement page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    early_statement_page: StatementPage = StatementPage.objects.create(audit=audit)
    StatementPage.objects.create(audit=audit)

    assert audit.latest_statement_link is None

    early_statement_page.url = STATEMENT_LINK
    early_statement_page.save()

    assert audit.latest_statement_link == STATEMENT_LINK


@pytest.mark.django_db
def test_all_retest_pages():
    """Test all_retest_pages for page returned by retest"""
    retest: Retest = create_retest_and_retest_check_results()
    retest_pages: QuerySet[RetestPage] = RetestPage.objects.filter(retest=retest)
    retest_page: RetestPage = retest_pages.first()
    page: Page = retest_page.page
    all_retest_pages_for_page: QuerySet[RetestPage] = RetestPage.objects.filter(
        page=page
    )

    assertQuerySetEqual(retest_page.all_retest_pages, all_retest_pages_for_page)


@pytest.mark.django_db
def test_statement_initially_found_using_overview_statement_check_results():
    """Tests an all the overview statement check results are 'Yes'"""
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.statement_initially_found is False

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert audit.statement_initially_found is True


@pytest.mark.django_db
def test_statement_found_at_12_week_retest_using_overview_statement_check_results():
    """Tests an all the overview statement check results retest states are 'Yes'"""
    audit: Audit = create_audit_and_statement_check_results()

    assert audit.statement_found_at_12_week_retest is False

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.retest_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert audit.statement_found_at_12_week_retest is True


@pytest.mark.django_db
def test_retest_statement_check_results():
    """Test Retest.statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(retest=retest)
    )

    assertQuerySetEqual(retest.statement_check_results, retest_statement_check_results)


@pytest.mark.django_db
def test_retest_failed_statement_check_results():
    """Test Retest.failed_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_failed_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, check_result_state=StatementCheckResult.Result.NO
        )
    )

    assertQuerySetEqual(
        retest.failed_statement_check_results, retest_failed_statement_check_results
    )


@pytest.mark.django_db
def test_retest_overview_statement_check_results():
    """Test Retest.overview_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_overview_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.OVERVIEW
        )
    )

    assertQuerySetEqual(
        retest.overview_statement_check_results, retest_overview_statement_check_results
    )


@pytest.mark.django_db
def test_retest_all_overview_statement_checks_have_passed():
    """Test Retest.all_overview_statement_checks_have_passed"""
    retest: Retest = create_retest_and_statement_check_results()

    assert retest.all_overview_statement_checks_have_passed is False

    retest_overview_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.OVERVIEW
        )
    )
    for (
        retest_overview_statement_check_result
    ) in retest_overview_statement_check_results:
        retest_overview_statement_check_result.check_result_state = (
            StatementCheckResult.Result.YES
        )
        retest_overview_statement_check_result.save()

    assert retest.all_overview_statement_checks_have_passed is True


@pytest.mark.django_db
def test_retest_website_statement_check_results():
    """Test Retest.website_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_website_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.WEBSITE
        )
    )

    assertQuerySetEqual(
        retest.website_statement_check_results, retest_website_statement_check_results
    )


@pytest.mark.django_db
def test_retest_compliance_statement_check_results():
    """Test Retest.compliance_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_compliance_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.COMPLIANCE
        )
    )

    assertQuerySetEqual(
        retest.compliance_statement_check_results,
        retest_compliance_statement_check_results,
    )


@pytest.mark.django_db
def test_retest_non_accessible_statement_check_results():
    """Test Retest.non_accessible_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_non_accessible_statement_check_results: QuerySet[
        RetestStatementCheckResult
    ] = RetestStatementCheckResult.objects.filter(
        retest=retest, type=StatementCheck.Type.NON_ACCESSIBLE
    )

    assertQuerySetEqual(
        retest.non_accessible_statement_check_results,
        retest_non_accessible_statement_check_results,
    )


@pytest.mark.django_db
def test_retest_preparation_statement_check_results():
    """Test Retest.preparation_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_preparation_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.PREPARATION
        )
    )

    assertQuerySetEqual(
        retest.preparation_statement_check_results,
        retest_preparation_statement_check_results,
    )


@pytest.mark.django_db
def test_retest_feedback_statement_check_results():
    """Test Retest.feedback_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_feedback_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.FEEDBACK
        )
    )

    assertQuerySetEqual(
        retest.feedback_statement_check_results,
        retest_feedback_statement_check_results,
    )


@pytest.mark.django_db
def test_retest_custom_statement_check_results():
    """Test Retest.custom_statement_check_results"""
    retest: Retest = create_retest_and_statement_check_results()
    retest_custom_statement_check_results: QuerySet[RetestStatementCheckResult] = (
        RetestStatementCheckResult.objects.filter(
            retest=retest, type=StatementCheck.Type.CUSTOM
        )
    )

    assertQuerySetEqual(
        retest.custom_statement_check_results,
        retest_custom_statement_check_results,
    )


@pytest.mark.django_db
def test_retest_statement_check_results_str():
    """Test RetestStatementCheckResult.__str__()"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_statement_check_result: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.create(retest=retest)
    )

    assert (
        retest_statement_check_result.__str__()
        == f"{retest} | Custom [{retest_statement_check_result.issue_identifier}]"
    )

    statement_check: StatementCheck = StatementCheck.objects.get(
        id=ACCESSIBILITY_PAGE_STATEMENT_CHECK_ID
    )
    retest_statement_check_result.statement_check = statement_check
    retest_statement_check_result.save()

    assert (
        retest_statement_check_result.__str__()
        == f"{retest} | {statement_check} [{retest_statement_check_result.issue_identifier}]"
    )


@pytest.mark.django_db
def test_retest_statement_check_results_label():
    """Test RetestStatementCheckResult.label"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_statement_check_result: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.create(retest=retest)
    )

    assert retest_statement_check_result.label == "Custom"

    statement_check: StatementCheck = StatementCheck.objects.get(
        id=ACCESSIBILITY_PAGE_STATEMENT_CHECK_ID
    )
    retest_statement_check_result.statement_check = statement_check
    retest_statement_check_result.save()

    assert retest_statement_check_result.label == "Is there an accessibility page?"


@pytest.mark.django_db
def test_check_result_matching_wcag_with_retest_notes_check_results():
    """
    Test CheckResult.matching_wcag_with_retest_notes_check_results returns other
    check results on the other pages with the same WCAG definition and retest notes
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    contact_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.CONTACT)
    coronavirus_page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.CORONAVIRUS
    )
    first_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    second_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=contact_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        retest_notes="Sample note",
    )
    third_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=coronavirus_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        retest_notes="Another note",
    )

    assert first_check_result.matching_wcag_with_retest_notes_check_results.count() == 2
    assert (
        first_check_result.matching_wcag_with_retest_notes_check_results.first()
        == second_check_result
    )
    assert (
        first_check_result.matching_wcag_with_retest_notes_check_results.last()
        == third_check_result
    )


@pytest.mark.django_db
def test_retest_check_result_matching_wcag_retest_check_results():
    """
    Test RetestCheckResult.matching_wcag_retest_check_results returns
    retest check results on the other pages with the same WCAG definition
    and with retest notes
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    contact_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.CONTACT)
    coronavirus_page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.CORONAVIRUS
    )
    first_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    second_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=contact_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        retest_notes="Sample note",
    )
    third_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=coronavirus_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        retest_notes="Another note",
    )
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_home_page: RetestPage = RetestPage.objects.create(
        retest=retest, page=home_page
    )
    retest_contact_page: RetestPage = RetestPage.objects.create(
        retest=retest, page=contact_page
    )
    retest_coronavirus_page: RetestPage = RetestPage.objects.create(
        retest=retest, page=coronavirus_page
    )
    first_retest_check_result: RetestCheckResult = RetestCheckResult.objects.create(
        retest=retest,
        retest_page=retest_home_page,
        check_result=first_check_result,
        retest_notes="Retest retest note one",
    )
    second_retest_check_result: RetestCheckResult = RetestCheckResult.objects.create(
        retest=retest,
        retest_page=retest_contact_page,
        check_result=second_check_result,
        retest_notes="Retest retest note two",
    )
    third_retest_check_result: RetestCheckResult = RetestCheckResult.objects.create(
        retest=retest,
        retest_page=retest_coronavirus_page,
        check_result=third_check_result,
        retest_notes="Retest retest note three",
    )

    assert first_retest_check_result.matching_wcag_retest_check_results.count() == 2
    assert (
        first_retest_check_result.matching_wcag_retest_check_results.first()
        == second_retest_check_result
    )
    assert (
        first_retest_check_result.matching_wcag_retest_check_results.last()
        == third_retest_check_result
    )


def test_statement_check_result_display_value():
    """Test StatementCheckResult.display_value"""
    statement_check_result: StatementCheckResult = StatementCheckResult()

    assert statement_check_result.display_value == "Not tested"

    statement_check_result.check_result_state = StatementCheckResult.Result.NO
    statement_check_result.report_comment = REPORT_COMMENT

    assert (
        statement_check_result.display_value
        == f"No<br><br>Auditor's comment: {REPORT_COMMENT}"
    )


@pytest.mark.django_db
def test_check_result_issue_identifier():
    """Test check result gets unique identifier"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case_1: SimplifiedCase = SimplifiedCase.objects.create()
    audit_1: Audit = Audit.objects.create(simplified_case=simplified_case_1)
    page_1: Page = Page.objects.create(audit=audit_1, page_type=Page.Type.HOME)
    check_result_1a: CheckResult = CheckResult.objects.create(
        audit=audit_1,
        page=page_1,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert check_result_1a.issue_identifier == "1-A-1"

    check_result_1b: CheckResult = CheckResult.objects.create(
        audit=audit_1,
        page=page_1,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert check_result_1b.issue_identifier == "1-A-2"

    simplified_case_2: SimplifiedCase = SimplifiedCase.objects.create()
    audit_2: Audit = Audit.objects.create(simplified_case=simplified_case_2)
    page_2: Page = Page.objects.create(audit=audit_2, page_type=Page.Type.HOME)
    check_result_2a: CheckResult = CheckResult.objects.create(
        audit=audit_2,
        page=page_2,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert check_result_2a.issue_identifier == "2-A-1"


@pytest.mark.django_db
def test_issue_identifier():
    """
    Test issue_identifier property is populated on CheckResult, StatementCheckResult,
    RetestCheckResult and RetestStatementCheckResult creation.
    """

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )

    first_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert first_check_result.issue_identifier == "1-A-1"

    second_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert second_check_result.issue_identifier == "1-A-2"

    statement_check: StatementCheck = StatementCheck.objects.all().first()
    first_statement_check_result: StatementCheckResult = (
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )
    )

    assert first_statement_check_result.issue_identifier == "1-S-1"

    second_statement_check_result: StatementCheckResult = (
        StatementCheckResult.objects.create(
            audit=audit,
            report_comment="Custom statement issue",
        )
    )

    assert second_statement_check_result.issue_identifier == "1-SC-2"

    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    create_checkresults_for_retest(retest=retest)

    first_retest_check_result: RetestCheckResult = (
        retest.retestcheckresult_set.all().first()
    )
    second_retest_check_result: RetestCheckResult = (
        retest.retestcheckresult_set.all().last()
    )

    assert first_retest_check_result.issue_identifier == "1-A-1"
    assert second_retest_check_result.issue_identifier == "1-A-2"

    assert retest.reteststatementcheckresult_set.count() > 2

    first_retest_statement_check_result: RetestStatementCheckResult = (
        retest.reteststatementcheckresult_set.all().first()
    )
    second_retest_statement_check_result: RetestStatementCheckResult = (
        retest.reteststatementcheckresult_set.all().last()
    )

    assert first_retest_statement_check_result.issue_identifier == "1-S-1"
    assert second_retest_statement_check_result.issue_identifier == "1-S-42"

    new_custom_retest_statement_check_result: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.create(
            retest=retest,
        )
    )

    assert new_custom_retest_statement_check_result.issue_identifier == "1-SC-43"


@pytest.mark.django_db
def test_build_issue_identifier():
    """Test building issue identifiers"""

    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert (
        build_issue_identifier(simplified_case=simplified_case, issue=check_result)
        == "1-A-1"
    )

    statement_check: StatementCheck = StatementCheck.objects.all().first()
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
    )

    assert (
        build_issue_identifier(
            simplified_case=simplified_case, issue=statement_check_result
        )
        == "1-S-1"
    )

    custom_statement_check_result: StatementCheck = StatementCheckResult.objects.create(
        audit=audit,
        report_comment="Custom statement issue",
    )

    assert (
        build_issue_identifier(
            simplified_case=simplified_case,
            issue=custom_statement_check_result,
            custom_issue=True,
        )
        == "1-SC-2"
    )

    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )
    retest_check_result: RetestCheckResult = RetestCheckResult.objects.create(
        retest=retest,
        id_within_case=check_result.id_within_case,
        retest_page=retest_page,
        check_result=check_result,
    )

    assert (
        build_issue_identifier(
            simplified_case=simplified_case, issue=retest_check_result
        )
        == "1-A-1"
    )

    retest_statement_check_result: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.create(
            retest=retest,
            type=statement_check.type,
            statement_check=statement_check,
        )
    )

    assert (
        build_issue_identifier(
            simplified_case=simplified_case, issue=retest_statement_check_result
        )
        == "1-S-1"
    )

    custom_retest_statement_check_result: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.create(
            retest=retest,
            comment="Custom statement issue",
        )
    )

    assert (
        build_issue_identifier(
            simplified_case=simplified_case,
            issue=custom_retest_statement_check_result,
            custom_issue=True,
        )
        == "1-SC-2"
    )


@pytest.mark.django_db
def test_audit_new_12_week_custom_statement_check_results():
    """Test statement custom check result found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    new_12_week_custom_check_result: StatementCheckResult = (
        StatementCheckResult.objects.create(
            audit=audit,
            type=StatementCheck.Type.TWELVE_WEEK,
            report_comment="12-week custom statement issue",
        )
    )

    assert audit.new_12_week_custom_statement_check_results.count() == 1
    assert (
        audit.new_12_week_custom_statement_check_results.first()
        == new_12_week_custom_check_result
    )
