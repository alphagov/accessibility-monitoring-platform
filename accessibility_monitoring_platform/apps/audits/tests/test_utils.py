"""
Test - common utility functions
"""
import pytest
from typing import Dict, List, Tuple, Union

from django.contrib.auth.models import User
from django.db.models.query import QuerySet

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
    PAGE_TYPE_ALL,
    TEST_TYPE_PDF,
    TEST_TYPE_AXE,
    TEST_TYPE_MANUAL,
)
from ..utils import (
    copy_all_pages_check_results,
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    get_audit_metadata_rows,
    get_audit_statement_rows,
    get_audit_report_options_rows,
)

USER_FIRST_NAME = "John"
USER_LAST_NAME = "Smith"
TYPES_OF_OF_PAGES_CREATED_WITH_NEW_AUDIT: List[str] = [
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
    PAGE_TYPE_ALL,
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
        value=None, label="Date of test", type="text", extra_label="", external_url=True
    ),
    FieldLabelAndValue(
        value="",
        label="Name",
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
]
EXPECTED_AUDIT_PDF_ROWS: List[FieldLabelAndValue] = [
    FieldLabelAndValue(
        value="", label="PDF WCAG", type="notes", extra_label="", external_url=True
    )
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
    FieldLabelAndValue(
        value="Not Compliant",
        label="Overall Decision on Compliance of Accessibility Statement",
        type="text",
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
        label="It was not in the correct format",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It was not specific enough",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="Accessibility issues were found during the test that were not included in the statement",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="Mandatory wording is missing",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="We require more information covering the disproportionate burden claim",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It required more information detailing the accessibility issues",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It includes a deadline of XXX for fixing XXX issues and this has not been completed",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It includes a deadline of XXX for fixing XXX issues and this is not sufficient",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It is out of date and needs to be reviewed",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="It is a requirement that accessibility statements are accessible. Some users may experience"
        " difficulties using PDF documents. It may be beneficial for users if there was a HTML version of your"
        " full accessibility statement.",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="In 2020 the GOV.UK sample template was updated to include an extra mandatory piece of information"
        " to outline the scope of your accessibility statement. This needs to be added to your statement.",
        type="text",
        extra_label="",
        external_url=True,
    ),
    FieldLabelAndValue(
        value="No",
        label="Your statement should be prominently placed on the homepage of the website or made available"
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

    page_home: Page = Page.objects.create(audit=audit, page_type=PAGE_TYPE_HOME)
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=TEST_TYPE_MANUAL
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_home,
        wcag_definition=wcag_definition_manual,
        type=wcag_definition_manual.type,
    )

    page_pdf: Page = Page.objects.create(audit=audit, page_type=PAGE_TYPE_PDF)
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
    CheckResult.objects.create(
        audit=audit,
        page=page_pdf,
        wcag_definition=wcag_definition_pdf,
        type=wcag_definition_pdf.type,
    )

    return audit


@pytest.mark.django_db
def test_copy_all_pages_check_results():
    """Test copy of check results to all html pages"""
    audit: Audit = create_audit_and_check_results()
    page_all: Page = Page.objects.create(audit=audit, page_type=PAGE_TYPE_ALL)
    wcag_definition_manual: WcagDefinition = WcagDefinition.objects.get(
        type=TEST_TYPE_MANUAL
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_all,
        wcag_definition=wcag_definition_manual,
        notes=UPDATED_NOTE,
    )

    copy_all_pages_check_results(user=audit.case.auditor, page=page_all)

    for page in audit.html_pages:
        check_results: QuerySet[CheckResult] = page.checkresult_page.all()
        assert len(check_results) == NUMBER_OF_WCAG_PER_TYPE_OF_PAGE
        for check_result in check_results:
            assert check_result.notes == UPDATED_NOTE

    page_pdf: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_PDF)
    check_results: QuerySet[CheckResult] = page_pdf.checkresult_page.all()  # type: ignore
    assert len(check_results) == NUMBER_OF_WCAG_PER_TYPE_OF_PAGE
    for check_result in check_results:
        assert check_result.notes != UPDATED_NOTE


@pytest.mark.django_db
def test_get_audit_metadata_rows():
    """Test audit metadata rows returned for display on View test page"""
    audit, _ = create_audit_and_user()

    assert get_audit_metadata_rows(audit=audit) == EXPECTED_AUDIT_METADATA_ROWS


@pytest.mark.django_db
def test_get_audit_statement_rows():
    """Test audit statement rows returned for display on View test page"""
    audit: Audit = create_audit_and_wcag()

    assert get_audit_statement_rows(audit=audit) == EXPECTED_AUDIT_STATEMENT_ROWS


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
