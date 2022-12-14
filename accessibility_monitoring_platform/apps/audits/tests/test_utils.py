"""
Test - common utility functions
"""
from datetime import date
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
    CHECK_RESULT_ERROR,
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
)
from ..utils import (
    create_mandatory_pages_for_new_audit,
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    get_audit_metadata_rows,
    get_website_decision_rows,
    get_audit_statement_rows,
    get_statement_decision_rows,
    get_audit_report_options_rows,
    get_next_page_url,
    get_next_retest_page_url,
    other_page_failed_check_results,
    report_data_updated,
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
        value="Not selected",
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
EXPECTED_AUDIT_STATEMENT_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="",
        label="Link to saved accessibility statement",
        type="url",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not included",
        label="Scope",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Feedback",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Contact Information",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not included",
        label="Enforcement Procedure",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not included",
        label="Declaration",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Compliance Status",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Non-accessible Content - non compliance with regulations",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No claim",
        label="Non-accessible Content - disproportionate burden",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Non-accessible Content - the content is not within the scope of the applicable legislation",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not included",
        label="Preparation Date",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not included",
        label="Review",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Not present",
        label="Method",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="Does not meet requirements",
        label="Access Requirements",
        type="text",
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
        label="They don???t have a statement, or it is in the wrong format",
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

    assert audit.page_audit.count() == len(MANDATORY_PAGE_TYPES)  # type: ignore

    home_page: Page = audit.page_audit.filter(page_type=PAGE_TYPE_HOME).first()  # type: ignore

    assert home_page.url == HOME_PAGE_URL


@pytest.mark.django_db
def test_get_audit_metadata_rows():
    """Test audit metadata rows returned for display on View test page"""
    audit, _ = create_audit_and_user()

    assert [field.value for field in get_audit_metadata_rows(audit=audit)] == [
        field.value for field in EXPECTED_AUDIT_METADATA_ROWS
    ]
    assert [field.label for field in get_audit_metadata_rows(audit=audit)] == [
        field.label for field in EXPECTED_AUDIT_METADATA_ROWS
    ]


@pytest.mark.django_db
def test_get_website_decision_rows():
    """Test website decision rows returned for display on View test page"""
    audit, _ = create_audit_and_user()

    assert get_website_decision_rows(audit=audit) == EXPECTED_WEBSITE_DECISION_ROWS


@pytest.mark.django_db
def test_get_audit_statement_rows():
    """Test audit statement rows returned for display on View test page"""
    audit: Audit = create_audit_and_wcag()

    assert get_audit_statement_rows(audit=audit) == EXPECTED_AUDIT_STATEMENT_ROWS


@pytest.mark.django_db
def test_get_statement_decision_rows():
    """Test statement decision rows returned for display on View test page"""
    audit, _ = create_audit_and_user()

    assert get_statement_decision_rows(audit=audit) == EXPECTED_STATEMENT_DECISION_ROWS


@pytest.mark.django_db
def test_get_audit_report_options_rows():
    """Test audit report options rows returned for display on View test page"""
    audit: Audit = create_audit_and_wcag()

    assert (
        get_audit_report_options_rows(audit=audit) == EXPECTED_AUDIT_REPORT_OPTIONS_ROWS
    )


@pytest.mark.django_db
def test_create_or_update_check_results_for_page():
    """Test create and update of check results for a page"""
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
        formset_data[f"form-{count}-wcag_definition"] = check_result.wcag_definition.id  # type: ignore
        formset_data[f"form-{count}-check_result_state"] = CHECK_RESULT_ERROR
        formset_data[f"form-{count}-notes"] = UPDATED_NOTE

    new_form_index: int = len(check_results)
    new_wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME
    )
    formset_data[f"form-{new_form_index}-wcag_definition"] = new_wcag_definition.id  # type: ignore
    formset_data[f"form-{new_form_index}-check_result_state"] = CHECK_RESULT_ERROR
    formset_data[f"form-{new_form_index}-notes"] = NEW_CHECK_NOTE

    check_results_formset: CheckResultFormset = CheckResultFormset(formset_data)
    check_results_formset.is_valid()

    create_or_update_check_results_for_page(
        user=audit.case.auditor,
        page=page_home,
        check_result_forms=check_results_formset.forms,
    )

    updated_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=TEST_TYPE_MANUAL
    )
    new_check_result: CheckResult = CheckResult.objects.get(
        page=page_home, type=TEST_TYPE_AXE
    )

    assert updated_check_result.check_result_state == CHECK_RESULT_ERROR
    assert updated_check_result.notes == UPDATED_NOTE
    assert new_check_result.check_result_state == CHECK_RESULT_ERROR
    assert new_check_result.notes == NEW_CHECK_NOTE


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
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
    assert get_next_page_url(audit=audit) == reverse(
        "audits:edit-website-decision", kwargs=audit_pk
    )


@pytest.mark.django_db
def test_get_next_page_url_audit_with_pages():
    """
    Test get_next_page_url returns urls for each testable page in audit in in turn.
    """
    audit: Audit = create_audit_and_check_results()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    next_page: Page = audit.testable_pages[0]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}  # type: ignore
    assert get_next_page_url(audit=audit) == reverse(
        "audits:edit-audit-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}  # type: ignore
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
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
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
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
    for page in audit.testable_pages:
        for check_result in page.all_check_results:
            check_result.check_result_state = CHECK_RESULT_ERROR
            check_result.save()

    next_page: Page = audit.testable_pages[0]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}  # type: ignore
    assert get_next_retest_page_url(audit=audit) == reverse(
        "audits:edit-audit-retest-page-checks", kwargs=next_page_pk
    )

    current_page: Page = audit.testable_pages[0]
    next_page: Page = audit.testable_pages[1]
    next_page_pk: Dict[str, int] = {"pk": next_page.id}  # type: ignore
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
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
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
    assert len(failed_check_results[wcag_definition_manual]) == 1

    assert (
        failed_check_results[wcag_definition_manual][0]
        == home_page.failed_check_results[0]
    )


@pytest.mark.django_db
def test_report_data_updated():
    """Test report data updated fields are populated"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert audit.unpublished_report_data_updated_time is None
    assert audit.published_report_data_updated_time is None

    report_data_updated(audit=audit)

    assert audit.unpublished_report_data_updated_time is not None
    assert audit.published_report_data_updated_time is not None
