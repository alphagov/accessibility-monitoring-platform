"""
Test - common utility functions
"""

from datetime import date, timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest
from django.urls import reverse

from ...common.form_extract_utils import FieldLabelAndValue
from ...common.sitemap import PlatformPage
from ...simplified.models import SimplifiedCase
from ..forms import CheckResultFormset
from ..models import (
    Audit,
    CheckResult,
    CheckResultNotesHistory,
    CheckResultRetestNotesHistory,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)
from ..utils import (
    add_to_check_result_notes_history,
    add_to_check_result_restest_notes_history,
    create_checkresults_for_retest,
    create_mandatory_pages_for_new_audit,
    create_or_update_check_results_for_page,
    create_statement_checks_for_new_audit,
    get_audit_summary_context,
    get_next_platform_page_equality_body,
    get_next_platform_page_initial,
    get_next_platform_page_twelve_week,
    get_other_pages_with_retest_notes,
    get_page_check_results_formset_initial,
    index_or_404,
    other_page_failed_check_results,
    report_data_updated,
)

TODAY: date = date.today()
HOME_PAGE_URL: str = "https://example.com/home"
USER_FIRST_NAME = "John"
USER_LAST_NAME = "Smith"
TYPES_OF_OF_PAGES_CREATED_WITH_NEW_AUDIT: list[str] = [
    Page.Type.HOME,
    Page.Type.CONTACT,
    Page.Type.STATEMENT,
    Page.Type.PDF,
    Page.Type.FORM,
]
NUMBER_OF_PAGES_CREATED_WITH_NEW_AUDIT: int = len(
    TYPES_OF_OF_PAGES_CREATED_WITH_NEW_AUDIT
)
WCAG_TYPE_PDF_NAME: str = "PDF WCAG"
WCAG_TYPE_AXE_NAME: str = "Axe WCAG"
WCAG_TYPE_MANUAL_NAME: str = "Manual WCAG"
NUMBER_OF_WCAG_PER_TYPE_OF_PAGE: int = 1
NUMBER_OF_HTML_PAGES: int = 4
UPDATED_NOTE: str = "Updated note"
NEW_CHECK_NOTE: str = "New note"
OLD_CHECK_RESULT_NOTES: str = "Old check result notes"
NEW_CHECK_RESULT_NOTES: str = "New check result notes"
OLD_RETEST_NOTES: str = "Old retest notes"
NEW_RETEST_NOTES: str = "New retest notes"
EXPECTED_AUDIT_REPORT_OPTIONS_ROWS: list[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="An accessibility statement for the website was not found.",
        label="Accessibility statement",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it was not in the correct format",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it was not specific enough",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="accessibility issues were found during the test that were not included in the statement",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="mandatory wording is missing",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="we require more information covering the disproportionate burden claim",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it required more information detailing the accessibility issues",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it includes a deadline of XXX for fixing XXX issues and this has not been completed",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it includes a deadline of XXX for fixing XXX issues and this is not sufficient",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it is out of date and needs to be reviewed",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it must link directly to the Equality Advisory and Support Service (EASS) website",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="it is a requirement that accessibility statements are accessible. Some users may experience"
        " difficulties using PDF documents. It may be beneficial for users if there was a HTML version of your"
        " full accessibility statement.",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="in 2020 the GOV.UK sample template was updated to include an extra mandatory piece of information"
        " to outline the scope of your accessibility statement. This needs to be added to your statement.",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="your statement should be prominently placed on the homepage of the website or made available"
        " on every web page, for example in a static header or footer, as per the legislative requirement.",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="Extra wording for report",
        type="notes",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Errors were found",
        label="What to do next",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="They have an acceptable statement but need to change it because of the errors we found",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="They don’t have a statement, or it is in the wrong format",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="They have a statement but it is not quite right",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="Their statement matches",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="Disproportionate burden",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="Notes",
        type="notes",
        extra_label="",
        external_url=True,
    ),
]


def create_audit_and_wcag() -> Audit:
    """Create an audit and WcagDefinitions"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    WcagDefinition.objects.all().delete()
    WcagDefinition.objects.create(
        id=1, type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )
    WcagDefinition.objects.create(
        id=2, type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    return audit


def create_audit_and_user() -> tuple[Audit, User]:
    """Create an audit and pages"""
    audit: Audit = create_audit_and_wcag()
    user: User = User.objects.create(
        first_name=USER_FIRST_NAME, last_name=USER_LAST_NAME
    )
    audit.simplified_case.auditor = user
    audit.simplified_case.save()
    return audit, user


def create_audit_and_check_results() -> Audit:
    """Create an audit and check results"""
    audit, _ = create_audit_and_user()

    page_home: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.MANUAL
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_home,
        wcag_definition=wcag_definition_manual,
        type=wcag_definition_manual.type,
    )

    page_pdf: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.PDF, url="https://example.com/pdf"
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_pdf,
        wcag_definition=wcag_definition_pdf,
        type=wcag_definition_pdf.type,
    )

    return audit


@pytest.mark.django_db
def test_create_mandatory_pages_for_new_audit():
    """Test that the mandatory pages are created for a new audit"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL
    )
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    create_mandatory_pages_for_new_audit(audit=audit)

    assert audit.page_audit.count() == len(Page.MANDATORY_PAGE_TYPES)

    home_page: Page = audit.page_audit.filter(page_type=Page.Type.HOME).first()

    assert home_page.url == HOME_PAGE_URL


@pytest.mark.django_db
def test_update_check_results_for_page():
    """Test update of check results for a page"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)

    check_results: QuerySet[CheckResult] = CheckResult.objects.filter(page=page_home)

    number_of_forms: int = len(check_results) + 1
    formset_data: dict[str, int | str] = {
        "form-TOTAL_FORMS": number_of_forms,
        "form-INITIAL_FORMS": number_of_forms,
        "form-MIN_NUM_FORMS": 0,
        "form-MAX_NUM_FORMS": 1000,
    }
    for count, check_result in enumerate(check_results):
        formset_data[f"form-{count}-wcag_definition"] = check_result.wcag_definition.id
        formset_data[f"form-{count}-check_result_state"] = CheckResult.Result.ERROR
        formset_data[f"form-{count}-notes"] = UPDATED_NOTE

    new_form_index: int = len(check_results)
    new_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    formset_data[f"form-{new_form_index}-wcag_definition"] = new_wcag_definition.id
    formset_data[f"form-{new_form_index}-check_result_state"] = CheckResult.Result.ERROR
    formset_data[f"form-{new_form_index}-notes"] = NEW_CHECK_NOTE

    check_results_formset: CheckResultFormset = CheckResultFormset(formset_data)
    check_results_formset.is_valid()

    assert audit.published_report_data_updated_time is None

    create_or_update_check_results_for_page(
        user=audit.simplified_case.auditor,
        page=page_home,
        check_result_forms=check_results_formset.forms,
    )

    updated_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=WcagDefinition.Type.MANUAL
    )

    assert updated_check_result.check_result_state == CheckResult.Result.ERROR
    assert updated_check_result.notes == UPDATED_NOTE

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_create_check_results_for_page():
    """Test create of check results for a page"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)

    check_results: QuerySet[CheckResult] = CheckResult.objects.filter(page=page_home)

    number_of_forms: int = len(check_results) + 1
    formset_data: dict[str, int | str] = {
        "form-TOTAL_FORMS": number_of_forms,
        "form-INITIAL_FORMS": number_of_forms,
        "form-MIN_NUM_FORMS": 0,
        "form-MAX_NUM_FORMS": 1000,
    }
    for count, check_result in enumerate(check_results):
        formset_data[f"form-{count}-wcag_definition"] = check_result.wcag_definition.id
        formset_data[f"form-{count}-check_result_state"] = (
            check_result.check_result_state
        )
        formset_data[f"form-{count}-notes"] = check_result.notes

    new_form_index: int = len(check_results)
    new_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    formset_data[f"form-{new_form_index}-wcag_definition"] = new_wcag_definition.id
    formset_data[f"form-{new_form_index}-check_result_state"] = CheckResult.Result.ERROR
    formset_data[f"form-{new_form_index}-notes"] = NEW_CHECK_NOTE

    check_results_formset: CheckResultFormset = CheckResultFormset(formset_data)
    check_results_formset.is_valid()

    assert audit.published_report_data_updated_time is None

    create_or_update_check_results_for_page(
        user=audit.simplified_case.auditor,
        page=page_home,
        check_result_forms=check_results_formset.forms,
    )

    new_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=WcagDefinition.Type.AXE
    )

    assert new_check_result.check_result_state == CheckResult.Result.ERROR
    assert new_check_result.notes == NEW_CHECK_NOTE

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_get_all_possible_check_results_for_page():
    """Test building list of all possible test results"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    WcagDefinition.objects.create(type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME)
    wcag_definitions: list[WcagDefinition] = list(WcagDefinition.objects.all())

    all_check_results: list[dict[str, str | WcagDefinition]] = (
        get_page_check_results_formset_initial(
            page=page_home, wcag_definitions=wcag_definitions
        )
    )

    assert len(all_check_results) == 3

    assert all_check_results == [
        {
            "wcag_definition": WcagDefinition.objects.get(type=WcagDefinition.Type.PDF),
            "check_result_state": "not-tested",
            "notes": "",
            "issue_identifier": "",
            "check_result": None,
        },
        {
            "wcag_definition": WcagDefinition.objects.get(
                type=WcagDefinition.Type.MANUAL
            ),
            "check_result_state": "not-tested",
            "notes": "",
            "issue_identifier": "1-A-1",
            "check_result": CheckResult.objects.get(
                page=page_home, type=WcagDefinition.Type.MANUAL
            ),
        },
        {
            "wcag_definition": WcagDefinition.objects.get(type=WcagDefinition.Type.AXE),
            "check_result_state": "not-tested",
            "notes": "",
            "issue_identifier": "",
            "check_result": None,
        },
    ]


@pytest.mark.django_db
def test_get_next_platform_page_audit_with_no_pages():
    """
    Test get_next_platform_page returns website decision page
    when audit has no testable pages.
    """
    audit: Audit = create_audit_and_wcag()

    platform_page: PlatformPage = get_next_platform_page_initial(audit=audit)

    assert platform_page.url_name == "audits:edit-website-decision"


@pytest.mark.django_db
def test_get_next_platform_page_audit_with_pages():
    """
    Test get_next_platform_page returns each testable page in audit in in turn.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    next_page: Page = audit.testable_pages[0]
    next_page_pk: dict[str, int] = {"pk": next_page.id}
    platform_page: PlatformPage = get_next_platform_page_initial(audit=audit)

    assert platform_page.url == reverse(
        "audits:edit-audit-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: dict[str, int] = {"pk": next_page.id}
    platform_page: PlatformPage = get_next_platform_page_initial(
        audit=audit, current_page=current_page
    )

    assert platform_page.url == reverse(
        "audits:edit-audit-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[1]
    platform_page: PlatformPage = get_next_platform_page_initial(
        audit=audit, current_page=current_page
    )

    assert platform_page.url == reverse("audits:edit-website-decision", kwargs=audit_pk)


@pytest.mark.django_db
def test_get_next_platform_page_twelve_week_audit_with_pages():
    """
    Test get_next_platform_page_twelve_week returns platform page
    for each testable page (with errors) in audit in in turn.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}
    for page in audit.testable_pages:
        for check_result in page.all_check_results:
            check_result.check_result_state = CheckResult.Result.ERROR
            check_result.save()

    next_page: Page = audit.testable_pages[0]
    next_page_pk: dict[str, int] = {"pk": next_page.id}
    platform_page: PlatformPage = get_next_platform_page_twelve_week(audit=audit)

    assert platform_page.url == reverse(
        "audits:edit-audit-retest-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: dict[str, int] = {"pk": next_page.id}
    platform_page: PlatformPage = get_next_platform_page_twelve_week(
        audit=audit, current_page=current_page
    )

    assert platform_page.url == reverse(
        "audits:edit-audit-retest-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[1]
    platform_page: PlatformPage = get_next_platform_page_twelve_week(
        audit=audit, current_page=current_page
    )

    assert platform_page.url == reverse(
        "audits:edit-audit-retest-website-decision", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_platform_page_twelve_week_audit_with_no_errors():
    """
    Test get_next_platform_page_twelve_week returns expected platform page
    for website compliance decision when audit has no pages with errors.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}
    assert get_next_platform_page_twelve_week(audit=audit).url == reverse(
        "audits:edit-audit-retest-website-decision", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_other_page_failed_check_results():
    """
    Test other_page_failed_check_results returns a dictionary of all the failed
    check results entered for other pages
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    extra_page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.EXTRA, url="https://example.com/extra"
    )
    Page.objects.create(
        audit=audit, page_type=Page.Type.EXTRA, url="https://example.com/extra2"
    )
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.MANUAL
    )
    for page in audit.html_pages:
        CheckResult.objects.create(
            audit=audit,
            page=page,
            wcag_definition=wcag_definition_manual,
            type=wcag_definition_manual.type,
        )
        CheckResult.objects.create(
            audit=audit,
            page=page,
            wcag_definition=wcag_definition_manual,
            type=wcag_definition_manual.type,
            check_result_state=CheckResult.Result.ERROR,
        )
    failed_check_results: dict[WcagDefinition, list[CheckResult]] = (
        other_page_failed_check_results(page=extra_page)
    )

    assert len(home_page.failed_check_results) == 1
    assert wcag_definition_manual in failed_check_results
    assert len(failed_check_results[wcag_definition_manual]) == 2

    assert (
        failed_check_results[wcag_definition_manual][0]
        == home_page.failed_check_results[0]
    )


@pytest.mark.django_db
def test_report_data_updated():
    """Test report data updated fields are populated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert audit.published_report_data_updated_time is None

    report_data_updated(audit=audit)

    assert audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_create_statement_checks_for_new_audit():
    """Test creation of statement check results for audit"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert StatementCheckResult.objects.filter(audit=audit).count() == 0

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.on_date(TODAY).count()

    assert (
        StatementCheckResult.objects.filter(audit=audit).count()
        == number_of_statement_checks
    )


@pytest.mark.django_db
def test_create_skips_future_statement_checks():
    """
    Test creation of statement check results for audit skips future
    statement checks.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    future_statement_check: StatementCheck = StatementCheck.objects.all().first()
    future_statement_check.date_start = date.today() + timedelta(days=10)
    future_statement_check.save()

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.on_date(TODAY).count()

    assert (
        StatementCheckResult.objects.filter(audit=audit).count()
        == number_of_statement_checks
    )


@pytest.mark.django_db
def test_create_skips_past_statement_checks():
    """
    Test creation of statement check results for audit skips past
    statement checks.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    past_statement_check: StatementCheck = StatementCheck.objects.all().first()
    past_statement_check.date_end = date.today() - timedelta(days=10)
    past_statement_check.save()

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.on_date(TODAY).count()

    assert (
        StatementCheckResult.objects.filter(audit=audit).count()
        == number_of_statement_checks
    )


@pytest.mark.django_db
def test_create_checkresults_for_retest():
    """
    Copy unfixed checks from 12-week retest to create a hidden retest with
    id-in-case set to zero.

    All subsequent retests are created by copying unfixed retests and
    incrementing id-in-case.
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    unfixed_page_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.NO_ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert Retest.objects.all().count() == 0

    retest_1: Retest = Retest.objects.create(simplified_case=simplified_case)

    create_checkresults_for_retest(retest=retest_1)

    assert Retest.objects.all().count() == 2

    retest_0: Retest = Retest.objects.get(id_within_case=0)
    retest_page_0: RetestPage = RetestPage.objects.get(retest=retest_0)

    assert retest_page_0.page == page
    assert RetestCheckResult.objects.filter(retest=retest_0).count() == 1

    retest_checkresult_0: RetestCheckResult = RetestCheckResult.objects.get(
        retest=retest_0
    )

    assert retest_checkresult_0.check_result == unfixed_page_check_result

    retest_page_1: RetestPage = RetestPage.objects.get(retest=retest_1)

    assert retest_page_1.page == page
    assert RetestCheckResult.objects.filter(retest=retest_1).count() == 1

    retest_checkresult_1: RetestCheckResult = RetestCheckResult.objects.get(
        retest=retest_1
    )

    assert retest_checkresult_1.check_result == unfixed_page_check_result

    retest_2: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=2
    )

    create_checkresults_for_retest(retest=retest_2)

    assert Retest.objects.all().count() == 3

    retest_2: Retest = Retest.objects.get(id_within_case=2)
    retest_page_2: RetestPage = RetestPage.objects.get(retest=retest_2)

    assert retest_page_2.page == page
    assert RetestCheckResult.objects.filter(retest=retest_2).count() == 1

    retest_checkresult_2: RetestCheckResult = RetestCheckResult.objects.get(
        retest=retest_2
    )

    assert retest_checkresult_2.check_result == unfixed_page_check_result


@pytest.mark.django_db
def test_create_checkresults_for_retest_creates_statement_checks():
    """
    RetestStatementCheckResults are created for each new retest.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    assert RetestStatementCheckResult.objects.all().count() == 0

    create_checkresults_for_retest(retest=retest)

    assert RetestStatementCheckResult.objects.all().count() > 0


@pytest.mark.django_db
def test_get_next_platform_page_equality_body_with_no_pages():
    """
    Test get_next_platform_page_equality_body returns platform page for retest
    comparison update when retest has no retest pages.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    platform_page: PlatformPage = get_next_platform_page_equality_body(retest=retest)
    assert platform_page.url == reverse(
        "audits:retest-comparison-update", kwargs={"pk": retest.id}
    )


@pytest.mark.django_db
def test_get_next_platform_page_equality_body_with_pages():
    """
    Test get_next_platform_page_equality_bodyreturns patform pages
    for each retest page in retest in in turn.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    first_retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )
    last_retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )

    assert get_next_platform_page_equality_body(retest).url == reverse(
        "audits:edit-retest-page-checks", kwargs={"pk": first_retest_page.id}
    )
    assert get_next_platform_page_equality_body(
        retest, current_page=first_retest_page
    ).url == reverse(
        "audits:edit-retest-page-checks", kwargs={"pk": last_retest_page.id}
    )
    assert get_next_platform_page_equality_body(
        retest, current_page=last_retest_page
    ).url == reverse("audits:retest-comparison-update", kwargs={"pk": retest.id})


@pytest.mark.django_db
def test_get_other_pages_with_retest_notes():
    """Test get_other_pages_with_retest_notes returns only other pages with retest notes"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit,
        page_type=Page.Type.HOME,
        url="https://example.com",
        retest_notes="Primary",
    )
    other_page_with_retest_notes: Page = Page.objects.create(
        audit=audit,
        page_type=Page.Type.HOME,
        url="https://example.com",
        retest_notes="Other",
    )
    Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )

    other_pages_with_retest_notes: list[Page] = get_other_pages_with_retest_notes(
        page=page
    )

    assert len(other_pages_with_retest_notes) == 1

    assert other_pages_with_retest_notes[0] == other_page_with_retest_notes


@pytest.mark.django_db
def test_get_audit_summary_context(rf):
    """Test get_audit_summary_context returned"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "enable_12_week_ui" in context
    assert "show_failures_by_page" in context
    assert "show_all" in context
    assert "audit_failures_by_page" in context
    assert "pages_with_retest_notes" in context
    assert "audit_failures_by_wcag" in context
    assert "number_of_wcag_issues" in context
    assert "number_of_statement_issues" in context
    assert "statement_check_results_by_type" in context


@pytest.mark.django_db
def test_get_audit_summary_enable_12_week_ui(rf):
    """Test enable_12_week_ui set as expected"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "enable_12_week_ui" in context
    assert context["enable_12_week_ui"] is False

    audit.retest_date = TODAY

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "enable_12_week_ui" in context
    assert context["enable_12_week_ui"] is True


@pytest.mark.django_db
def test_get_audit_summary_show_failures_by_page(rf):
    """Test show_failures_by_page set as expected"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "show_failures_by_page" in context
    assert context["show_failures_by_page"] is False

    request.GET = {"page-view": "true"}

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "show_failures_by_page" in context
    assert context["show_failures_by_page"] is True


@pytest.mark.django_db
def test_get_audit_summary_audit_failures_by_page(rf):
    """Test audit_failures_by_page set as expected"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_page" in context
    assert context["audit_failures_by_page"] == {}

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

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_page" in context

    audit_failures_by_page: dict[Page, Any] = context["audit_failures_by_page"]

    assert page in audit_failures_by_page
    assert len(audit_failures_by_page[page]) == 1
    assert audit_failures_by_page[page][0] == check_result


@pytest.mark.django_db
def test_get_audit_summary_pages_with_retest_notes(rf):
    """Test pages_with_retest_notes set as expected"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "pages_with_retest_notes" in context
    assert context["pages_with_retest_notes"].exists() is False

    page.retest_notes = "Note"
    page.save()

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "pages_with_retest_notes" in context
    assert context["pages_with_retest_notes"].exists() is True
    assert context["pages_with_retest_notes"].first() == page


@pytest.mark.django_db
def test_get_audit_summary_audit_failures_by_wcag(rf):
    """Test audit_failures_by_wcag set as expected"""
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_wcag" in context
    assert context["audit_failures_by_wcag"] == {}

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

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_wcag" in context

    audit_failures_by_wcag: dict[Page, Any] = context["audit_failures_by_wcag"]

    assert wcag_definition in audit_failures_by_wcag
    assert len(audit_failures_by_wcag[wcag_definition]) == 1
    assert audit_failures_by_wcag[wcag_definition][0] == check_result


@pytest.mark.django_db
def test_get_audit_summary_unfixed_audit_failures(rf):
    """
    Test fixed results are not returned when show_all URL paremeter
    not set.
    """
    request: HttpRequest = rf.get("/")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
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

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_wcag" in context

    audit_failures_by_wcag: dict[Page, Any] = context["audit_failures_by_wcag"]

    assert len(audit_failures_by_wcag[wcag_definition]) == 1
    assert audit_failures_by_wcag[wcag_definition][0] == check_result

    assert "audit_failures_by_page" in context

    audit_failures_by_page: dict[Page, Any] = context["audit_failures_by_page"]

    assert page in audit_failures_by_page
    assert len(audit_failures_by_page[page]) == 1
    assert audit_failures_by_page[page][0] == check_result

    assert "number_of_wcag_issues" in context
    assert context["number_of_wcag_issues"] == 1

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "audit_failures_by_wcag" in context
    assert context["audit_failures_by_wcag"] == {}
    assert "audit_failures_by_page" in context
    assert context["audit_failures_by_page"] == {}
    assert "number_of_wcag_issues" in context
    assert context["number_of_wcag_issues"] == 0


@pytest.mark.django_db
def test_get_audit_summary_issue_counts(rf):
    """Test counting of issues for Test summary page"""
    request: HttpRequest = rf.get("/")
    request.GET = {"show-all": "true"}
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    create_statement_checks_for_new_audit(audit=audit)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "number_of_wcag_issues" in context
    assert context["number_of_wcag_issues"] == 1
    assert "number_of_statement_issues" in context
    assert context["number_of_statement_issues"] == 1

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "number_of_statement_issues" in context
    assert context["number_of_statement_issues"] == 42


@pytest.mark.django_db
def test_get_audit_summary_statement_check_results_by_type(rf):
    """Test statement check results grouped by type"""
    request: HttpRequest = rf.get("/")
    request.GET = {"show-all": "true"}
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    create_statement_checks_for_new_audit(audit=audit)

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "statement_check_results_by_type" in context

    statement_check_results_by_type: dict[str, QuerySet[StatementCheckResult]] = (
        context["statement_check_results_by_type"]
    )

    assert "overview" in statement_check_results_by_type
    assert len(statement_check_results_by_type["overview"]) == 1

    statement_check_result = statement_check_results_by_type["overview"][0]
    request.GET = {}

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "statement_check_results_by_type" in context
    assert context["statement_check_results_by_type"] == {}

    statement_check_result.check_result_state = StatementCheckResult.Result.NO
    statement_check_result.save()

    context: dict[str, Any] = get_audit_summary_context(request=request, audit=audit)

    assert "statement_check_results_by_type" in context

    statement_check_results_by_type: dict[str, QuerySet[StatementCheckResult]] = (
        context["statement_check_results_by_type"]
    )

    assert "overview" in statement_check_results_by_type
    assert len(statement_check_results_by_type["overview"]) == 1


def test_index_or_404():
    """Text index or 404 returns index or raises 404"""
    items: str = ["a", "b", "c"]

    assert index_or_404(items=items, item="b") == 1

    with pytest.raises(Http404):
        index_or_404(items=items, item="d")


@pytest.mark.django_db
def test_add_check_result_notes_history():
    """
    Test add_to_check_result_notes_history creates an entry with the correct
    notes and logged in user.
    """
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    WcagDefinition.objects.all().delete()
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        type=wcag_definition.type,
        notes=OLD_CHECK_RESULT_NOTES,
    )

    check_result.notes = NEW_CHECK_RESULT_NOTES

    add_to_check_result_notes_history(check_result=check_result, user=user)

    check_result_notes_history: CheckResultNotesHistory = (
        CheckResultNotesHistory.objects.get(check_result=check_result)
    )

    assert check_result_notes_history.notes == NEW_CHECK_RESULT_NOTES
    assert check_result_notes_history.created_by == user


@pytest.mark.django_db
def test_check_result_notes_history_changed():
    """
    Test add_to_check_result_notes_history creates an entry only if the
    notes have changed.
    """
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    WcagDefinition.objects.all().delete()
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        type=wcag_definition.type,
        notes=OLD_CHECK_RESULT_NOTES,
    )

    add_to_check_result_notes_history(check_result=check_result, user=user)

    assert CheckResultNotesHistory.objects.all().count() == 0

    check_result.notes = NEW_CHECK_RESULT_NOTES

    add_to_check_result_notes_history(check_result=check_result, user=user)

    assert CheckResultNotesHistory.objects.all().count() == 1


@pytest.mark.django_db
def test_add_check_result_restest_notes_history():
    """
    Test add_to_check_result_restest_notes_history creates an entry with the correct
    retest notes, retest state and logged in user.
    """
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    WcagDefinition.objects.all().delete()
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        type=wcag_definition.type,
        retest_notes=OLD_RETEST_NOTES,
        retest_state=CheckResult.RetestResult.FIXED,
    )

    check_result.retest_notes = NEW_RETEST_NOTES

    add_to_check_result_restest_notes_history(check_result=check_result, user=user)

    check_result_retest_notes_history: CheckResultRetestNotesHistory = (
        CheckResultRetestNotesHistory.objects.get(check_result=check_result)
    )

    assert check_result_retest_notes_history.retest_notes == NEW_RETEST_NOTES
    assert (
        check_result_retest_notes_history.retest_state == CheckResult.RetestResult.FIXED
    )
    assert check_result_retest_notes_history.created_by == user


@pytest.mark.django_db
def test_check_result_restest_notes_history_changed():
    """
    Test add_to_check_result_restest_notes_history creates an entry only if the
    retest notes have changed.
    """
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    WcagDefinition.objects.all().delete()
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url="https://example.com"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        type=wcag_definition.type,
        retest_notes=OLD_RETEST_NOTES,
    )

    add_to_check_result_restest_notes_history(check_result=check_result, user=user)

    assert CheckResultRetestNotesHistory.objects.all().count() == 0

    check_result.retest_notes = NEW_RETEST_NOTES

    add_to_check_result_restest_notes_history(check_result=check_result, user=user)

    assert CheckResultRetestNotesHistory.objects.all().count() == 1
