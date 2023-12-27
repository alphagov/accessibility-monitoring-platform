"""
Test - common utility functions
"""
from datetime import date, timedelta
import pytest
from typing import Dict, List, Tuple, Union

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.urls import reverse

from ...cases.models import Case
from ...common.form_extract_utils import FieldLabelAndValue

from ..forms import CheckResultFormset
from ..models import (
    Audit,
    CheckResult,
    Page,
    WcagDefinition,
    StatementCheck,
    StatementCheckResult,
    CHECK_RESULT_ERROR,
    CHECK_RESULT_NO_ERROR,
    RETEST_CHECK_RESULT_NOT_FIXED,
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
    PAGE_TYPE_EXTRA,
    TEST_TYPE_PDF,
    TEST_TYPE_AXE,
    TEST_TYPE_MANUAL,
    MANDATORY_PAGE_TYPES,
    Retest,
    RetestPage,
    RetestCheckResult,
)
from ..utils import (
    create_mandatory_pages_for_new_audit,
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    get_audit_report_options_rows,
    get_next_page_url,
    get_next_retest_page_url,
    other_page_failed_check_results,
    report_data_updated,
    get_test_view_tables_context,
    get_retest_view_tables_context,
    create_statement_checks_for_new_audit,
    create_checkresults_for_retest,
    get_next_equality_body_retest_page_url,
)

HOME_PAGE_URL: str = "https://example.com/home"
USER_FIRST_NAME = "John"
USER_LAST_NAME = "Smith"
TYPES_OF_OF_PAGES_CREATED_WITH_NEW_AUDIT: List[str] = [
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
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
EXPECTED_AUDIT_METADATA_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value=date.today(),
        label="Date of test",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="15 inch",
        label="Screen size",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Unknown",
        label="Exemptions?",
        type="text",
        extra_label="",
        external_url=True,
    ),
]
EXPECTED_AUDIT_PDF_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="", label="PDF WCAG", type="notes", extra_label="", external_url=True
    )
]
EXPECTED_WEBSITE_DECISION_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="Not known",
        label="Initial website compliance decision",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="Initial website compliance notes",
        type="notes",
        extra_label="",
        external_url=True,
    ),
]
EXPECTED_STATEMENT_DECISION_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="Not selected",
        label="Initial accessibility statement compliance decision",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="Initial accessibility statement compliance notes",
        type="notes",
        extra_label="",
        external_url=True,
    ),
]
EXPECTED_AUDIT_REPORT_OPTIONS_ROWS: List[FieldLabelAndValue] = [
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
EXPECTED_RETEST_WEBSITE_DECISION_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="Not known",
        label="12-week website compliance decision",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="12-week website compliance decision notes",
        type="notes",
        extra_label="",
        external_url=True,
    ),
]
EXPECTED_RETEST_STATEMENT_DECISION_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="Not selected",
        label="12-week accessibility statement compliance decision",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="",
        label="12-week accessibility statement compliance notes",
        type="notes",
        extra_label="",
        external_url=True,
    ),
]


def create_audit_and_wcag() -> Audit:
    """Create an audit and WcagDefinitions"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    WcagDefinition.objects.all().delete()
    WcagDefinition.objects.create(id=1, type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME)
    WcagDefinition.objects.create(
        id=2, type=TEST_TYPE_MANUAL, name=WCAG_TYPE_MANUAL_NAME
    )
    return audit


def create_audit_and_user() -> Tuple[Audit, User]:
    """Create an audit and pages"""
    audit: Audit = create_audit_and_wcag()
    user: User = User.objects.create(
        first_name=USER_FIRST_NAME, last_name=USER_LAST_NAME
    )
    audit.case.auditor = user
    audit.case.save()
    return audit, user


def create_audit_and_check_results() -> Audit:
    """Create an audit and check results"""
    audit, _ = create_audit_and_user()

    page_home: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_HOME, url="https://example.com"
    )
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=TEST_TYPE_MANUAL
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_home,
        wcag_definition=wcag_definition_manual,
        type=wcag_definition_manual.type,
    )

    page_pdf: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_PDF, url="https://example.com/pdf"
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
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
    case: Case = Case.objects.create(home_page_url=HOME_PAGE_URL)
    audit: Audit = Audit.objects.create(case=case)
    create_mandatory_pages_for_new_audit(audit=audit)

    assert audit.page_audit.count() == len(MANDATORY_PAGE_TYPES)

    home_page: Page = audit.page_audit.filter(page_type=PAGE_TYPE_HOME).first()

    assert home_page.url == HOME_PAGE_URL


@pytest.mark.django_db
def test_get_audit_metadata_rows():
    """Test audit metadata rows returned for display on View test page"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_test_view_tables_context(
        audit=audit
    )

    assert [field.value for field in context["audit_metadata_rows"]] == [
        field.value for field in EXPECTED_AUDIT_METADATA_ROWS
    ]
    assert [field.label for field in context["audit_metadata_rows"]] == [
        field.label for field in EXPECTED_AUDIT_METADATA_ROWS
    ]


@pytest.mark.django_db
def test_get_website_decision_rows():
    """Test website decision rows returned for display on View test page"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_test_view_tables_context(
        audit=audit
    )

    assert context["website_decision_rows"] == EXPECTED_WEBSITE_DECISION_ROWS


@pytest.mark.django_db
def test_get_statement_decision_rows():
    """Test statement decision rows returned for display on View test page"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_test_view_tables_context(
        audit=audit
    )

    assert context["statement_decision_rows"] == EXPECTED_STATEMENT_DECISION_ROWS


@pytest.mark.django_db
def test_get_audit_report_options_rows():
    """Test audit report options rows returned for display on View test page"""
    audit: Audit = create_audit_and_wcag()
    context: Dict[str, List[FieldLabelAndValue]] = get_test_view_tables_context(
        audit=audit
    )
    assert (
        get_audit_report_options_rows(audit=audit) == EXPECTED_AUDIT_REPORT_OPTIONS_ROWS
    )
    assert context["audit_report_options_rows"] == EXPECTED_AUDIT_REPORT_OPTIONS_ROWS


@pytest.mark.django_db
def test_update_check_results_for_page():
    """Test update of check results for a page"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)

    check_results: QuerySet[CheckResult] = CheckResult.objects.filter(page=page_home)

    number_of_forms: int = len(check_results) + 1
    formset_data: Dict[str, Union[int, str]] = {
        "form-TOTAL_FORMS": number_of_forms,
        "form-INITIAL_FORMS": number_of_forms,
        "form-MIN_NUM_FORMS": 0,
        "form-MAX_NUM_FORMS": 1000,
    }
    for count, check_result in enumerate(check_results):
        formset_data[f"form-{count}-wcag_definition"] = check_result.wcag_definition.id
        formset_data[f"form-{count}-check_result_state"] = CHECK_RESULT_ERROR
        formset_data[f"form-{count}-notes"] = UPDATED_NOTE

    new_form_index: int = len(check_results)
    new_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME
    )
    formset_data[f"form-{new_form_index}-wcag_definition"] = new_wcag_definition.id
    formset_data[f"form-{new_form_index}-check_result_state"] = CHECK_RESULT_ERROR
    formset_data[f"form-{new_form_index}-notes"] = NEW_CHECK_NOTE

    check_results_formset: CheckResultFormset = CheckResultFormset(formset_data)
    check_results_formset.is_valid()

    assert audit.published_report_data_updated_time is None

    create_or_update_check_results_for_page(
        user=audit.case.auditor,
        page=page_home,
        check_result_forms=check_results_formset.forms,
    )

    updated_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=TEST_TYPE_MANUAL
    )

    assert updated_check_result.check_result_state == CHECK_RESULT_ERROR
    assert updated_check_result.notes == UPDATED_NOTE

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_create_check_results_for_page():
    """Test create of check results for a page"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)

    check_results: QuerySet[CheckResult] = CheckResult.objects.filter(page=page_home)

    number_of_forms: int = len(check_results) + 1
    formset_data: Dict[str, Union[int, str]] = {
        "form-TOTAL_FORMS": number_of_forms,
        "form-INITIAL_FORMS": number_of_forms,
        "form-MIN_NUM_FORMS": 0,
        "form-MAX_NUM_FORMS": 1000,
    }
    for count, check_result in enumerate(check_results):
        formset_data[f"form-{count}-wcag_definition"] = check_result.wcag_definition.id
        formset_data[
            f"form-{count}-check_result_state"
        ] = check_result.check_result_state
        formset_data[f"form-{count}-notes"] = check_result.notes

    new_form_index: int = len(check_results)
    new_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME
    )
    formset_data[f"form-{new_form_index}-wcag_definition"] = new_wcag_definition.id
    formset_data[f"form-{new_form_index}-check_result_state"] = CHECK_RESULT_ERROR
    formset_data[f"form-{new_form_index}-notes"] = NEW_CHECK_NOTE

    check_results_formset: CheckResultFormset = CheckResultFormset(formset_data)
    check_results_formset.is_valid()

    assert audit.published_report_data_updated_time is None

    create_or_update_check_results_for_page(
        user=audit.case.auditor,
        page=page_home,
        check_result_forms=check_results_formset.forms,
    )

    new_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=TEST_TYPE_AXE
    )

    assert new_check_result.check_result_state == CHECK_RESULT_ERROR
    assert new_check_result.notes == NEW_CHECK_NOTE

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    assert updated_audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_get_all_possible_check_results_for_page():
    """Test building list of all possible test results"""
    audit: Audit = create_audit_and_check_results()
    page_home: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)
    WcagDefinition.objects.create(type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME)
    wcag_definitions: List[WcagDefinition] = list(WcagDefinition.objects.all())

    all_check_results: List[
        Dict[str, Union[str, WcagDefinition]]
    ] = get_all_possible_check_results_for_page(
        page=page_home, wcag_definitions=wcag_definitions
    )

    assert len(all_check_results) == 3

    assert all_check_results == [
        {
            "wcag_definition": WcagDefinition.objects.get(type=TEST_TYPE_PDF),
            "check_result_state": "not-tested",
            "notes": "",
        },
        {
            "wcag_definition": WcagDefinition.objects.get(type=TEST_TYPE_MANUAL),
            "check_result_state": "not-tested",
            "notes": "",
        },
        {
            "wcag_definition": WcagDefinition.objects.get(type=TEST_TYPE_AXE),
            "check_result_state": "not-tested",
            "notes": "",
        },
    ]


@pytest.mark.django_db
def test_get_next_page_url_audit_with_no_pages():
    """
    Test get_next_page_url returns url for accessibility statement part 1
    when audit has no testable pages.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    assert get_next_page_url(audit=audit) == reverse(
        "audits:edit-website-decision", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_page_url_audit_with_pages():
    """
    Test get_next_page_url returns urls for each testable page in audit in in turn.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    next_page: Page = audit.testable_pages[0]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}
    assert get_next_page_url(audit=audit) == reverse(
        "audits:edit-audit-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}
    assert get_next_page_url(audit=audit, current_page=current_page) == reverse(
        "audits:edit-audit-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[1]
    assert get_next_page_url(audit=audit, current_page=current_page) == reverse(
        "audits:edit-website-decision", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_retest_page_url_audit_with_no_pages():
    """
    Test get_next_retest_page_url returns url for retest pages
    when audit has no testable pages.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    assert get_next_retest_page_url(audit=audit) == reverse(
        "audits:edit-audit-retest-pages", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_retest_page_url_audit_with_pages():
    """
    Test get_next_retest_page_url returns urls for each testable page (with
    errors) in audit in in turn.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    for page in audit.testable_pages:
        for check_result in page.all_check_results:
            check_result.check_result_state = CHECK_RESULT_ERROR
            check_result.save()

    next_page: Page = audit.testable_pages[0]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}
    assert get_next_retest_page_url(audit=audit) == reverse(
        "audits:edit-audit-retest-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}
    assert get_next_retest_page_url(audit=audit, current_page=current_page) == reverse(
        "audits:edit-audit-retest-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[1]
    assert get_next_retest_page_url(audit=audit, current_page=current_page) == reverse(
        "audits:edit-audit-retest-pages", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_retest_page_url_audit_with_no_errors():
    """
    Test get_next_retest_page_url returns url for website compliance decision
    when audit has no pages with errors.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    assert get_next_retest_page_url(audit=audit) == reverse(
        "audits:edit-audit-retest-pages", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_other_page_failed_check_results():
    """
    Test other_page_failed_check_results returns a dictionary of all the failed
    check results entered for other pages
    """
    audit: Audit = create_audit_and_check_results()
    home_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_HOME)
    extra_page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_EXTRA, url="https://example.com/extra"
    )
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_EXTRA, url="https://example.com/extra2"
    )
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=TEST_TYPE_MANUAL
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
            check_result_state=CHECK_RESULT_ERROR,
        )
    failed_check_results: Dict[
        WcagDefinition, List[CheckResult]
    ] = other_page_failed_check_results(page=extra_page)

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
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert audit.published_report_data_updated_time is None

    report_data_updated(audit=audit)

    assert audit.published_report_data_updated_time is not None


@pytest.mark.django_db
def test_get_test_view_tables_context():
    """Test view test tables context returned"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_test_view_tables_context(
        audit=audit
    )

    assert "audit_metadata_rows" in context
    assert "website_decision_rows" in context
    assert "audit_statement_1_rows" in context
    assert "audit_statement_2_rows" in context
    assert "statement_decision_rows" in context
    assert "audit_report_options_rows" in context


@pytest.mark.django_db
def test_get_retest_view_tables_context():
    """Test view 12-week retest tables context returned"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_retest_view_tables_context(
        case=audit.case
    )

    assert "audit_retest_website_decision_rows" in context
    assert "audit_retest_statement_decision_rows" in context


@pytest.mark.django_db
def test_audit_retest_website_decision_rows():
    """Test view 12-week retest website decision rows correct"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_retest_view_tables_context(
        case=audit.case
    )

    assert (
        context["audit_retest_website_decision_rows"]
        == EXPECTED_RETEST_WEBSITE_DECISION_ROWS
    )


@pytest.mark.django_db
def test_audit_retest_statement_decision_rows():
    """Test view 12-week retest website decision rows correct"""
    audit, _ = create_audit_and_user()
    context: Dict[str, List[FieldLabelAndValue]] = get_retest_view_tables_context(
        case=audit.case
    )

    assert (
        context["audit_retest_statement_decision_rows"]
        == EXPECTED_RETEST_STATEMENT_DECISION_ROWS
    )


@pytest.mark.django_db
def test_create_statement_checks_for_new_audit():
    """Test creation of statement check results for audit"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert StatementCheckResult.objects.filter(audit=audit).count() == 0

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.all().count()

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
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    future_statement_check: StatementCheck = StatementCheck.objects.all().first()
    future_statement_check.date_start = date.today() + timedelta(days=10)
    future_statement_check.save()

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.all().count() - 1

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
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    past_statement_check: StatementCheck = StatementCheck.objects.all().first()
    past_statement_check.date_end = date.today() - timedelta(days=10)
    past_statement_check.save()

    create_statement_checks_for_new_audit(audit=audit)

    number_of_statement_checks: int = StatementCheck.objects.all().count() - 1

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
        type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME
    )
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_HOME, url="https://example.com"
    )
    unfixed_page_check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CHECK_RESULT_ERROR,
        retest_state=RETEST_CHECK_RESULT_NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CHECK_RESULT_NO_ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert Retest.objects.all().count() == 0

    retest_1: Retest = Retest.objects.create(case=case)

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

    retest_2: Retest = Retest.objects.create(case=case, id_within_case=2)

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
def test_get_next_equality_body_retest_page_url_with_no_pages():
    """
    Test get_next_equality_body_retest_page_url returns url for retest comparison
    update when retest has no retest pages.
    """
    case: Case = Case.objects.create()
    retest: Retest = Retest.objects.create(case=case)
    assert get_next_equality_body_retest_page_url(retest) == reverse(
        "audits:retest-comparison-update", kwargs={"pk": retest.id}
    )


@pytest.mark.django_db
def test_get_next_equality_body_retest_page_url_with_pages():
    """
    Test get_next_equality_body_retest_page_url returns urls for each retest page
    in retest in in turn.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_HOME, url="https://example.com"
    )
    retest: Retest = Retest.objects.create(case=case)

    first_retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )
    last_retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )

    assert get_next_equality_body_retest_page_url(retest) == reverse(
        "audits:edit-retest-page-checks", kwargs={"pk": first_retest_page.id}
    )
    assert get_next_equality_body_retest_page_url(
        retest, current_page=first_retest_page
    ) == reverse("audits:edit-retest-page-checks", kwargs={"pk": last_retest_page.id})
    assert get_next_equality_body_retest_page_url(
        retest, current_page=last_retest_page
    ) == reverse("audits:retest-comparison-update", kwargs={"pk": retest.id})
