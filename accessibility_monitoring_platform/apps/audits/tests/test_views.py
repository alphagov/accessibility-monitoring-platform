"""
Tests for audits views
"""
import pytest
from datetime import date
from typing import Dict, List, Optional, Union

from pytest_django.asserts import assertContains, assertNotContains

from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from accessibility_monitoring_platform.apps.common.models import BOOLEAN_TRUE

from ...cases.models import (
    Case,
    CaseEvent,
    Contact,
    REPORT_METHODOLOGY_ODT,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_START_RETEST,
)
from ..models import (
    PAGE_TYPE_PDF,
    PAGE_TYPE_STATEMENT,
    Audit,
    CheckResult,
    Page,
    WcagDefinition,
    CHECK_RESULT_ERROR,
    CHECK_RESULT_NOT_TESTED,
    RETEST_CHECK_RESULT_FIXED,
    PAGE_TYPE_EXTRA,
    TEST_TYPE_AXE,
    TEST_TYPE_PDF,
    ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
    REPORT_OPTIONS_NEXT_DEFAULT,
)
from ..utils import create_mandatory_pages_for_new_audit

WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
WCAG_TYPE_MANUAL_NAME: str = "WCAG Manual name"
WCAG_TYPE_PDF_NAME: str = "WCAG PDF name"
EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"
CHECK_RESULT_NOTES: str = "Check result notes"
NEW_PAGE_NAME: str = "New page name"
NEW_PAGE_URL: str = "https://example.com/extra"
UPDATED_PAGE_NAME: str = "Updated page name"
UPDATED_PAGE_URL: str = "https://example.com/updated"
WEBSITE_COMPLIANCE_STATE_INITIAL: str = "partially-compliant"
COMPLIANCE_DECISION_NOTES: str = "Website decision notes"
ACCESSIBILITY_STATEMENT_STATE: str = "not-compliant"
ACCESSIBILITY_STATEMENT_NOTES: str = "Accessibility statement notes"
FIXED_ERROR_NOTES: str = "Fixed error notes"
WCAG_DEFINITION_TYPE: str = "axe"
WCAG_DEFINITION_NAME: str = "WCAG definiton name"
WCAG_DEFINITION_URL: str = "https://example.com"
PAGE_RETEST_NOTES: str = "Retest notes"
ACCESSIBILITY_STATEMENT_URL: str = "https://example.com/accessibility-statement"
NO_ACCESSIBILITY_STATEMENT_WARNING: str = """<strong class="govuk-warning-text__text">
    <span class="govuk-warning-text__assistive">Warning</span>
    The statement assessment is not visible as no statement has been found
    for this organisation website. To make the form visible, add an
    accessibility statement to
    <a href="/audits/1/edit-audit-pages/" class="govuk-link govuk-link--no-visited-state">
        Test > Pages</a>
    and uncheck 'Not found?'
</strong>"""
NO_ACCESSIBILITY_STATEMENT_ON_RETEST: str = """<p class="govuk-body-m">
    The statement assessment is not visible, as no statement was found during the initial test.
    <a href="/audits/1/edit-audit-12-week-statement/" class="govuk-link govuk-link--no-visited-state">
        Append a statement to the 12-week test</a>
    if the organisation has added a statement to their website.
</p>"""
NO_12_WEEK_STATEMENT_ON_RETEST_TEXT: str = "The statement assessment is not visible, as no statement was found during the initial test."
ACCESSIBILITY_STATEMENT_12_WEEK_URL: str = (
    "https://example.com/12-week-accessibility-statement"
)
TWELVE_WEEK_STATEMENT_ON_RETEST_TEXT: str = (
    "The statement was appended during the 12-week retest."
)
MISSING_PAGE_ON_RETEST: str = "This page has been removed by the organisation."
ORGANISATION_NAME: str = "Organisation name"


def create_audit() -> Audit:
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    audit: Audit = Audit.objects.create(case=case)
    return audit


def create_audit_and_pages() -> Audit:
    audit: Audit = create_audit()
    create_mandatory_pages_for_new_audit(audit=audit)
    return audit


def create_audit_and_wcag() -> Audit:
    audit: Audit = create_audit()
    WcagDefinition.objects.all().delete()
    WcagDefinition.objects.create(id=1, type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME)
    WcagDefinition.objects.create(id=2, type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME)
    return audit


def test_delete_page_view(admin_client):
    """Test that delete page view deletes page"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:delete-page",
            kwargs=page_pk,
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-pages",
        kwargs=audit_pk,
    )

    page_from_db: Page = Page.objects.get(**page_pk)

    assert page_from_db.is_deleted


def test_audit_detail_shows_number_of_errors(admin_client):
    """Test that audit detail view shows the number of errors"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_PDF, url="https://example.com"
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:audit-detail", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, "PDF (2)")


def test_audit_detail_shows_12_week_statement(admin_client):
    """Test that audit detail view shows the 12-week statement"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    audit.twelve_week_accessibility_statement_url = ACCESSIBILITY_STATEMENT_12_WEEK_URL
    audit.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:audit-retest-detail", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, ACCESSIBILITY_STATEMENT_12_WEEK_URL)


def test_restore_page_view(admin_client):
    """Test that restore page view restores audit"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, is_deleted=True)
    page_pk: Dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:restore-page",
            kwargs=page_pk,
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-pages",
        kwargs=audit_pk,
    )

    page_from_db: Page = Page.objects.get(**page_pk)

    assert page_from_db.is_deleted is False


def test_create_audit_redirects(admin_client):
    """Test that audit create redirects to audit metadata"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse("audits:edit-audit-metadata", kwargs={"pk": 1})


def test_create_audit_does_not_create_a_duplicate(admin_client):
    """Test that audit create does not create a duplicate audit"""
    audit: Audit = create_audit()
    path_kwargs: Dict[str, int] = {"case_id": audit.case.id}

    assert Audit.objects.filter(case=audit.case).count() == 1

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302
    assert Audit.objects.filter(case=audit.case).count() == 1


def test_create_audit_creates_case_event(admin_client):
    """Test that audit create creates a case event"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302
    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_CREATE_AUDIT
    assert case_event.message == "Started test"


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:audit-detail", "View test"),
        ("audits:edit-audit-metadata", "Test metadata"),
        ("audits:edit-audit-pages", "Pages"),
        ("audits:edit-website-decision", "Website compliance decision"),
        ("audits:edit-audit-statement-1", "Accessibility statement Pt. 1"),
        ("audits:edit-audit-statement-2", "Accessibility statement Pt. 2"),
        (
            "audits:edit-statement-decision",
            "Accessibility statement compliance decision",
        ),
        ("audits:edit-audit-report-options", "Report options"),
        ("audits:edit-audit-summary", "Test summary"),
        ("audits:edit-audit-report-text", "Report text"),
        ("audits:audit-retest-detail", "View 12-week test"),
        ("audits:edit-audit-retest-metadata", "12-week test metadata"),
        ("audits:edit-audit-retest-pages", "12-week pages comparison"),
        (
            "audits:edit-audit-retest-website-decision",
            "12-week website compliance decision",
        ),
        (
            "audits:edit-audit-retest-statement-1",
            "12-week accessibility statement Pt. 1",
        ),
        ("audits:edit-audit-12-week-statement", "Append accessibility statement"),
        (
            "audits:edit-audit-retest-statement-2",
            "12-week accessibility statement Pt. 2",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "12-week accessibility statement compliance decision",
        ),
    ],
)
def test_audit_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-specific view page loads"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=audit_pk))

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-audit-metadata", "save", "audits:edit-audit-metadata"),
        ("audits:edit-audit-metadata", "save_continue", "audits:edit-audit-pages"),
        ("audits:edit-website-decision", "save", "audits:edit-website-decision"),
        (
            "audits:edit-website-decision",
            "save_continue",
            "audits:edit-audit-statement-1",
        ),
        ("audits:edit-audit-statement-1", "save", "audits:edit-audit-statement-1"),
        (
            "audits:edit-audit-statement-1",
            "save_continue",
            "audits:edit-audit-statement-2",
        ),
        ("audits:edit-audit-statement-2", "save", "audits:edit-audit-statement-2"),
        (
            "audits:edit-audit-statement-2",
            "save_continue",
            "audits:edit-statement-decision",
        ),
        ("audits:edit-statement-decision", "save", "audits:edit-statement-decision"),
        (
            "audits:edit-statement-decision",
            "save_continue",
            "audits:edit-audit-report-options",
        ),
        (
            "audits:edit-audit-report-options",
            "save",
            "audits:edit-audit-report-options",
        ),
        (
            "audits:edit-audit-report-options",
            "save_continue",
            "audits:edit-audit-summary",
        ),
        ("audits:edit-audit-summary", "save", "audits:edit-audit-summary"),
        (
            "audits:edit-audit-summary",
            "save_continue",
            "audits:edit-audit-report-text",
        ),
        ("audits:edit-audit-report-text", "save", "audits:edit-audit-report-text"),
        (
            "audits:edit-audit-retest-metadata",
            "save",
            "audits:edit-audit-retest-metadata",
        ),
        (
            "audits:edit-audit-retest-metadata",
            "save_continue",
            "audits:edit-audit-retest-pages",
        ),
        ("audits:edit-audit-retest-pages", "save", "audits:edit-audit-retest-pages"),
        (
            "audits:edit-audit-retest-pages",
            "save_continue",
            "audits:edit-audit-retest-website-decision",
        ),
        (
            "audits:edit-audit-retest-website-decision",
            "save",
            "audits:edit-audit-retest-website-decision",
        ),
        (
            "audits:edit-audit-retest-website-decision",
            "save_continue",
            "audits:edit-audit-retest-statement-1",
        ),
        (
            "audits:edit-audit-retest-statement-1",
            "save",
            "audits:edit-audit-retest-statement-1",
        ),
        (
            "audits:edit-audit-retest-statement-1",
            "save_continue",
            "audits:edit-audit-retest-statement-2",
        ),
        (
            "audits:edit-audit-12-week-statement",
            "save",
            "audits:edit-audit-12-week-statement",
        ),
        (
            "audits:edit-audit-12-week-statement",
            "save_return",
            "audits:edit-audit-retest-statement-1",
        ),
        (
            "audits:edit-audit-retest-statement-2",
            "save",
            "audits:edit-audit-retest-statement-2",
        ),
        (
            "audits:edit-audit-retest-statement-2",
            "save_continue",
            "audits:edit-audit-retest-statement-comparison",
        ),
        (
            "audits:edit-audit-retest-statement-comparison",
            "save",
            "audits:edit-audit-retest-statement-comparison",
        ),
        (
            "audits:edit-audit-retest-statement-comparison",
            "save_continue",
            "audits:edit-audit-retest-statement-decision",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "save",
            "audits:edit-audit-retest-statement-decision",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "save_exit",
            "audits:audit-retest-detail",
        ),
    ],
)
def test_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """Test that a successful audit update redirects based on the button pressed"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "case-version": audit.case.version,
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_retest_date_change_creates_case_event(admin_client):
    """Test that changing the retest date creates a case event"""
    audit: Audit = create_audit()
    path_kwargs: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-metadata", kwargs=path_kwargs),
        {
            "retest_date_0": 30,
            "retest_date_1": 11,
            "retest_date_2": 2022,
            "save": "Save",
            "version": audit.version,
        },
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=audit.case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_START_RETEST
    assert case_event.message == "Started retest (date set to 30 November 2022)"


@pytest.mark.parametrize(
    "path_name",
    ["audits:edit-audit-summary", "audits:edit-audit-report-text"],
)
def test_audit_edit_redirects_to_case(
    path_name,
    admin_client,
):
    """Test that a successful audit save and exit redirects to the case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    case_pk: Dict[str, int] = {"pk": audit.case.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            "save_exit": "Button value",
            "case-version": audit.case.version,
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("cases:edit-test-results", kwargs=case_pk)
    assert response.url == expected_path


def test_retest_metadata_skips_to_statement_when_no_psb_response(admin_client):
    """
    Test save and continue button causes user to skip to statement 1 page
    when no response was received from public sector body.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    case: Case = audit.case
    case.no_psb_contact = BOOLEAN_TRUE
    case.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-metadata", kwargs=audit_pk),
        {
            "version": audit.version,
            "save_continue": "Button value",
            "case-version": audit.case.version,
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-audit-retest-statement-1", kwargs=audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "button_name, expected_redirect_path_name",
    [
        ("save", "audits:edit-audit-pages"),
        ("save_continue", "audits:edit-website-decision"),
    ],
)
def test_pages_redirects_based_on_button_pressed(
    button_name, expected_redirect_path_name, admin_client
):
    """Test that a successful audit update redirects based on the button pressed"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_standard_pages_appear_on_pages_page(admin_client):
    """
    Test that all the standard pages appear on the pages page.
    Also that the 'Form is on contact page' field appears.
    """
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
    )
    assert response.status_code == 200
    assertContains(response, """<h2 class="govuk-heading-m">Home</h2>""", html=True)
    assertContains(response, """<h2 class="govuk-heading-m">Contact</h2>""", html=True)
    assertContains(response, "Form is on contact page")
    assertContains(
        response,
        """<h2 class="govuk-heading-m">Accessibility Statement</h2>""",
        html=True,
    )
    assertContains(response, """<h2 class="govuk-heading-m">PDF</h2>""", html=True)
    assertContains(response, """<h2 class="govuk-heading-m">A Form</h2>""", html=True)


def test_two_extra_pages_appear_on_pages_page(admin_client):
    """
    Test that two extra pages appear on the pages page when no extra pages
    have yet been created.
    """
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        """<h2 id="extra-page-1" class="govuk-heading-m">Page 1</h2>""",
        html=True,
    )
    assertContains(
        response,
        """<h2 id="extra-page-2" class="govuk-heading-m">Page 2</h2>""",
        html=True,
    )

    Page.objects.create(audit=audit, page_type=PAGE_TYPE_EXTRA)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        """<h2 id="extra-page-2" class="govuk-heading-m">Page 2</h2>""",
        html=True,
    )


def test_add_extra_page_form_appears(admin_client):
    """
    Test that pressing the save and create additional page button adds an extra page form
    """
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            "add_extra": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Page 1")


def test_add_extra_page(admin_client):
    """Test adding an extra page"""
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "1",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "extra-0-id": "",
            "extra-0-name": EXTRA_PAGE_NAME,
            "extra-0-url": EXTRA_PAGE_URL,
            "version": audit.version,
            "save_continue": "Save and continue",
        },
        follow=True,
    )
    assert response.status_code == 200

    extra_pages: List[Page] = list(
        Page.objects.filter(audit=audit, page_type=PAGE_TYPE_EXTRA)
    )

    assert len(extra_pages) == 1
    assert extra_pages[0].name == EXTRA_PAGE_NAME
    assert extra_pages[0].url == EXTRA_PAGE_URL


def test_delete_extra_page(admin_client):
    """Test deleting an extra page"""
    audit: Audit = create_audit_and_pages()
    extra_page: Page = Page.objects.create(
        audit=audit,
        page_type=PAGE_TYPE_EXTRA,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            f"remove_extra_page_{extra_page.id}": "Remove page",
        },
        follow=True,
    )
    assert response.status_code == 200

    updated_extra_page: Page = Page.objects.get(id=extra_page.id)

    assert updated_extra_page.is_deleted


def test_page_checks_edit_page_loads(admin_client):
    """Test page checks edit view page loads and contains all WCAG definitions"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Testing Additional")
    assertContains(response, "Showing 2 errors")
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)


def test_page_checks_edit_saves_results(admin_client):
    """Test page checks edit view saves the entered results"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_AXE)
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-wcag_definition": wcag_definition_axe.id,
            "form-0-check_result_state": CHECK_RESULT_ERROR,
            "form-0-notes": CHECK_RESULT_NOTES,
            "form-1-wcag_definition": wcag_definition_pdf.id,
            "form-1-check_result_state": CHECK_RESULT_ERROR,
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "no_errors_date": "on",
        },
        follow=True,
    )

    assert response.status_code == 200

    check_result_axe: CheckResult = CheckResult.objects.get(
        page=page, wcag_definition=wcag_definition_axe
    )
    assert check_result_axe.check_result_state == CHECK_RESULT_ERROR
    assert check_result_axe.notes == CHECK_RESULT_NOTES

    check_result_pdf: CheckResult = CheckResult.objects.get(
        page=page, wcag_definition=wcag_definition_pdf
    )
    assert check_result_pdf.check_result_state == CHECK_RESULT_ERROR
    assert check_result_pdf.notes == CHECK_RESULT_NOTES

    updated_page: Page = Page.objects.get(id=page.id)

    assert updated_page.complete_date
    assert updated_page.no_errors_date


def test_page_checks_edit_stays_on_page(admin_client):
    """Test that a successful page checks edit stays on the page"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}
    url: str = reverse("audits:edit-audit-page-checks", kwargs=page_pk)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-wcag_definition": 1,
            "form-0-check_result_state": CHECK_RESULT_NOT_TESTED,
            "form-0-notes": "",
            "form-1-wcag_definition": 2,
            "form-1-check_result_state": CHECK_RESULT_NOT_TESTED,
            "form-1-notes": "",
        },
    )

    assert response.status_code == 302

    assert response.url == url


def test_website_decision_saved_on_case(admin_client):
    """Test that a website decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-website-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-version": audit.case.version,
            "case-website_compliance_state_initial": WEBSITE_COMPLIANCE_STATE_INITIAL,
            "case-compliance_decision_notes": COMPLIANCE_DECISION_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: Case = Case.objects.get(id=audit.case.id)

    assert (
        updated_case.website_compliance_state_initial
        == WEBSITE_COMPLIANCE_STATE_INITIAL
    )
    assert updated_case.compliance_decision_notes == COMPLIANCE_DECISION_NOTES


@pytest.mark.parametrize(
    "field_name, new_value, report_content_update",
    [
        ("case-website_compliance_state_initial", "partially-compliant", True),
        ("case-compliance_decision_notes", "blah", False),
        ("audit_website_decision_complete_date", timezone.now(), False),
    ],
)
def test_website_decision_field_updates_report_content(
    field_name, new_value, report_content_update, admin_client
):
    """
    Test that a report data updated time changes only when website compliance
    changes
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    assert audit.published_report_data_updated_time is None
    context: Dict[str, Union[str, int]] = {
        "version": audit.version,
        "case-version": audit.case.version,
        "case-website_compliance_state_initial": audit.case.website_compliance_state_initial,
        "save": "Button value",
    }
    context[field_name] = new_value

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-website-decision", kwargs=audit_pk), context
    )

    assert response.status_code == 302

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    if report_content_update:
        assert updated_audit.published_report_data_updated_time is not None
    else:
        assert updated_audit.published_report_data_updated_time is None


def test_statement_update_one_shows_statement_link(admin_client):
    """Test that an accessibility statement links shown if present"""
    audit: Audit = create_audit_and_pages()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-statement-1", kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, ACCESSIBILITY_STATEMENT_URL)

    page: Page = audit.accessibility_statement_page
    page.url = ACCESSIBILITY_STATEMENT_URL
    page.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-statement-1", kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, ACCESSIBILITY_STATEMENT_URL)

    page.not_found = BOOLEAN_TRUE
    page.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-statement-1", kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, ACCESSIBILITY_STATEMENT_URL)


@pytest.mark.parametrize(
    "url_name, field_label",
    [
        (
            "audits:audit-detail",
            "Non-accessible Content - non compliance with regulations",
        ),
        (
            "audits:edit-audit-statement-1",
            "Non-accessible Content - non compliance with regulations",
        ),
        (
            "audits:edit-audit-statement-2",
            "Non-accessible Content - disproportionate burden",
        ),
    ],
)
def test_statement_details_hidden_when_no_statement_page(
    url_name, field_label, admin_client
):
    """
    Test that accessibility statement details and form fields shown only if
    such a page is present.
    """
    audit: Audit = create_audit_and_pages()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, NO_ACCESSIBILITY_STATEMENT_WARNING, html=True)
    assertNotContains(response, field_label)

    page: Page = audit.accessibility_statement_page
    page.url = ACCESSIBILITY_STATEMENT_URL
    page.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, NO_ACCESSIBILITY_STATEMENT_WARNING, html=True)
    assertContains(response, field_label)

    page.not_found = BOOLEAN_TRUE
    page.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, NO_ACCESSIBILITY_STATEMENT_WARNING, html=True)
    assertNotContains(response, field_label)


@pytest.mark.parametrize(
    "url_name, field_label",
    [
        (
            "audits:audit-retest-detail",
            "Non-accessible content - non compliance with regulations",
        ),
        (
            "audits:edit-audit-retest-statement-1",
            "Non-accessible Content - non compliance with regulations",
        ),
        (
            "audits:edit-audit-retest-statement-2",
            "Non-accessible Content - disproportionate burden",
        ),
    ],
)
def test_statement_details_hidden_when_no_statement_page_on_retest(
    url_name, field_label, admin_client
):
    """
    Test that accessibility statement details and form fields shown only if
    such a page is present.
    """
    audit: Audit = create_audit_and_pages()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, NO_ACCESSIBILITY_STATEMENT_ON_RETEST, html=True)
    assertNotContains(response, field_label)

    page: Page = audit.accessibility_statement_page
    page.url = ACCESSIBILITY_STATEMENT_URL
    page.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, NO_ACCESSIBILITY_STATEMENT_ON_RETEST, html=True)
    assertContains(response, field_label)

    page.not_found = BOOLEAN_TRUE
    page.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, NO_ACCESSIBILITY_STATEMENT_ON_RETEST, html=True)
    assertNotContains(response, field_label)


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-retest-statement-1",
        "audits:edit-audit-retest-statement-2",
    ],
)
def test_12_week_statement_page_shown_on_retest(url_name, admin_client):
    """
    Test that option to add 12-week accessibility statement shown.
    """
    audit: Audit = create_audit_and_pages()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(response, NO_12_WEEK_STATEMENT_ON_RETEST_TEXT)
    assertNotContains(response, TWELVE_WEEK_STATEMENT_ON_RETEST_TEXT)
    assertNotContains(response, ACCESSIBILITY_STATEMENT_12_WEEK_URL)

    audit.twelve_week_accessibility_statement_url = ACCESSIBILITY_STATEMENT_12_WEEK_URL
    audit.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, NO_12_WEEK_STATEMENT_ON_RETEST_TEXT)
    assertContains(response, TWELVE_WEEK_STATEMENT_ON_RETEST_TEXT)
    assertContains(response, ACCESSIBILITY_STATEMENT_12_WEEK_URL)


@pytest.mark.parametrize(
    "email, new_contact_expected",
    [
        ("", False),
        ("email", True),
    ],
)
def test_statement_update_one_adds_contact(email, new_contact_expected, admin_client):
    """Test that a contact can be added from the statement update one view"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-statement-1", kwargs=audit_pk),
        {
            "version": audit.version,
            "add_contact_email": email,
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    contacts: QuerySet[Contact] = Contact.objects.filter(case=audit.case)

    if new_contact_expected:
        assert len(contacts) == 1
        contact: Contact = contacts[0]
        assert contact.email == email
    else:
        assert len(contacts) == 0


def test_statement_decision_saved_on_case(admin_client):
    """Test that a website decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-version": audit.case.version,
            "case-accessibility_statement_state": ACCESSIBILITY_STATEMENT_STATE,
            "case-accessibility_statement_notes": ACCESSIBILITY_STATEMENT_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: Case = Case.objects.get(id=audit.case.id)

    assert updated_case.accessibility_statement_state == ACCESSIBILITY_STATEMENT_STATE
    assert updated_case.accessibility_statement_notes == ACCESSIBILITY_STATEMENT_NOTES


@pytest.mark.parametrize(
    "field_name, new_value, report_content_update",
    [
        ("accessibility_statement_state", "found", True),
        ("report_options_next", "no-errors", True),
        ("audit_report_options_complete_date", timezone.now(), False),
    ],
)
def test_report_options_field_updates_report_content(
    field_name, new_value, report_content_update, admin_client
):
    """Test that a report data updated time changes when expected"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-report-options", kwargs=audit_pk),
        {
            "version": audit.version,
            "accessibility_statement_state": ACCESSIBILITY_STATEMENT_STATE_DEFAULT,
            "report_options_next": REPORT_OPTIONS_NEXT_DEFAULT,
            "save": "Button value",
            field_name: new_value,
            "accessibility_statement_deadline_not_complete_wording": "it includes a deadline of XXX for fixing XXX issues and this has not been completed",
            "accessibility_statement_deadline_not_sufficient_wording": "it includes a deadline of XXX for fixing XXX issues and this is not sufficient",
        },
    )

    assert response.status_code == 302

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    if report_content_update:
        assert updated_audit.published_report_data_updated_time is not None
    else:
        assert updated_audit.published_report_data_updated_time is None


def test_start_retest_redirects(admin_client):
    """Test that starting a retest redirects to audit retest metadata"""
    audit: Audit = create_audit()
    audit_pk: int = audit.id
    path_kwargs: Dict[str, int] = {"pk": audit_pk}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-retest-start", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-audit-retest-metadata", kwargs={"pk": audit_pk}
    )


def test_start_retest_creates_case_event(admin_client):
    """Test that starting a retest creates case event"""
    audit: Audit = create_audit()
    audit_pk: int = audit.id
    path_kwargs: Dict[str, int] = {"pk": audit_pk}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-retest-start", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=audit.case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_START_RETEST
    assert case_event.message == "Started retest"


def test_retest_details_renders_when_no_psb_response(admin_client):
    """
    Test save and continue button causes user to skip to statement 1 page
    when no response was received from public sector body.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    case: Case = audit.case
    case.no_psb_contact = BOOLEAN_TRUE
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:audit-retest-detail", kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertContains(
        response, "Only 12-week accessibility statement comparison is available"
    )


def test_retest_page_checks_edit_page_loads(admin_client):
    """Test retest page checks edit view page loads and contains errors"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit, retest_notes=PAGE_RETEST_NOTES)
    page_pk: Dict[str, int] = {"pk": page.id}
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_AXE)
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CHECK_RESULT_ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CHECK_RESULT_ERROR,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Retesting Additional")
    assertContains(response, PAGE_RETEST_NOTES)
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)


def test_retest_page_checks_edit_saves_results(admin_client):
    """Test retest page checks edit view saves the entered results"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_AXE)
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
    check_result_axe: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CHECK_RESULT_ERROR,
    )
    check_result_pdf: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CHECK_RESULT_ERROR,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": check_result_axe.id,
            "form-0-retest_state": "fixed",
            "form-0-retest_notes": CHECK_RESULT_NOTES,
            "form-1-id": check_result_pdf.id,
            "form-1-retest_state": "not-fixed",
            "form-1-retest_notes": CHECK_RESULT_NOTES,
            "retest_complete_date": "on",
            "retest_page_missing_date": "on",
            "retest_notes": PAGE_RETEST_NOTES,
        },
        follow=True,
    )

    assert response.status_code == 200

    updated_check_result_axe: CheckResult = CheckResult.objects.get(
        id=check_result_axe.id
    )
    assert updated_check_result_axe.retest_state == "fixed"
    assert updated_check_result_axe.retest_notes == CHECK_RESULT_NOTES

    updated_check_result_pdf: CheckResult = CheckResult.objects.get(
        id=check_result_pdf.id
    )
    assert updated_check_result_pdf.retest_state == "not-fixed"
    assert updated_check_result_pdf.retest_notes == CHECK_RESULT_NOTES

    updated_page: Page = Page.objects.get(id=page.id)

    assert updated_page.retest_complete_date
    assert updated_page.retest_page_missing_date
    assert updated_page.retest_notes == PAGE_RETEST_NOTES


def test_retest_page_shows_and_hides_fixed_errors(admin_client):
    """Test retest page conditionally shows and hides fixed errors"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_PDF)
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(type=TEST_TYPE_AXE)
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CHECK_RESULT_ERROR,
        retest_state=RETEST_CHECK_RESULT_FIXED,
        notes=FIXED_ERROR_NOTES,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CHECK_RESULT_ERROR,
    )

    url: str = reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, FIXED_ERROR_NOTES)

    response: HttpResponse = admin_client.get(f"{url}?hide-fixed=true")

    assert response.status_code == 200

    assertNotContains(response, FIXED_ERROR_NOTES)


def test_retest_pages_shows_missing_pages(admin_client):
    """Test that user is shown if page was marked as missing on retest"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")

    url: str = reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertNotContains(response, MISSING_PAGE_ON_RETEST)

    Page.objects.create(
        audit=audit,
        url="https://example.com",
        retest_page_missing_date=date(2022, 12, 16),
    )
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, MISSING_PAGE_ON_RETEST)


def test_retest_website_decision_saved_on_case(admin_client):
    """Test that a retest website decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-website-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-version": audit.case.version,
            "case-website_state_final": WEBSITE_COMPLIANCE_STATE_INITIAL,
            "case-website_state_notes_final": COMPLIANCE_DECISION_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: Case = Case.objects.get(id=audit.case.id)

    assert updated_case.website_state_final == WEBSITE_COMPLIANCE_STATE_INITIAL
    assert updated_case.website_state_notes_final == COMPLIANCE_DECISION_NOTES


def test_retest_statement_decision_saved_on_case(admin_client):
    """Test that a retest statement decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-version": audit.case.version,
            "case-accessibility_statement_state_final": ACCESSIBILITY_STATEMENT_STATE,
            "case-accessibility_statement_notes_final": ACCESSIBILITY_STATEMENT_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: Case = Case.objects.get(id=audit.case.id)

    assert (
        updated_case.accessibility_statement_state_final
        == ACCESSIBILITY_STATEMENT_STATE
    )
    assert (
        updated_case.accessibility_statement_notes_final
        == ACCESSIBILITY_STATEMENT_NOTES
    )


def test_retest_statement_decision_hides_initial_decision(admin_client):
    """
    Test that retest statement decision hides initial decision if none
    was entered.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, "View initial decision")

    audit.twelve_week_accessibility_statement_url = ACCESSIBILITY_STATEMENT_12_WEEK_URL
    audit.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, "Statement missing during initial test")


def test_report_text_shown_when_not_platform_report(admin_client):
    """
    Test that report text is shown when case is not using report methodology of platform
    """
    audit: Audit = create_audit_and_wcag()
    case: Case = audit.case
    case.report_methodology = REPORT_METHODOLOGY_ODT
    case.save()

    audit_pk: int = audit.id
    path_kwargs: Dict[str, int] = {"pk": audit_pk}
    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-report-text", kwargs=path_kwargs),
    )

    assert response.status_code == 200

    assertContains(response, "Copy report to clipboard")
    assertContains(
        response, """<h1 class="govuk-heading-l">Report text</h1>""", html=True
    )
    assertContains(response, "This is the end of the testing process.")
    assertNotContains(
        response,
        "Report text should not be used when the report methodology is set to Platform.",
    )


def test_all_initial_statement_one_notes_included_on_retest(admin_client):
    """
    Test that initial statement one notes all on retest page
    """
    audit: Audit = create_audit_and_wcag()
    audit.scope_notes = "Initial scope notes"
    audit.feedback_notes = "Initial feedback notes"
    audit.contact_information_notes = "Initial contact information notes"
    audit.enforcement_procedure_notes = "Initial enforcement procedure notes"
    audit.declaration_notes = "Initial declaration notes"
    audit.compliance_notes = "Initial compliance notes"
    audit.non_regulation_notes = "Initial non-regulation notes"
    audit.save()
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )

    audit_pk: int = audit.id
    path_kwargs: Dict[str, int] = {"pk": audit_pk}
    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-1", kwargs=path_kwargs),
    )

    assert response.status_code == 200

    assertContains(response, "Initial scope notes")
    assertContains(response, "Initial feedback notes")
    assertContains(response, "Initial contact information notes")
    assertContains(response, "Initial enforcement procedure notes")
    assertContains(response, "Initial declaration notes")
    assertContains(response, "Initial compliance notes")
    assertContains(response, "Initial non-regulation notes")


def test_all_initial_statement_two_notes_included_on_retest(admin_client):
    """
    Test that initial statement two notes all on retest page
    """
    audit: Audit = create_audit_and_wcag()
    audit.disproportionate_burden_notes = "Initial disproportional burden notes"
    audit.content_not_in_scope_notes = "Initial not in scope notes"
    audit.preparation_date_notes = "Initial preperation date notes"
    audit.review_notes = "Initial review notes"
    audit.method_notes = "Initial method notes"
    audit.access_requirements_notes = "Initial access requirements notes"
    audit.save()
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )

    audit_pk: int = audit.id
    path_kwargs: Dict[str, int] = {"pk": audit_pk}
    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-2", kwargs=path_kwargs),
    )

    assert response.status_code == 200

    assertContains(response, "Initial disproportional burden notes")
    assertContains(response, "Initial not in scope notes")
    assertContains(response, "Initial preperation date notes")
    assertContains(response, "Initial review notes")
    assertContains(response, "Initial method notes")
    assertContains(response, "Initial access requirements notes")


def test_wcag_definition_list_view_shows_all(admin_client):
    """Test WCAG definition list shows all rows"""
    response: HttpResponse = admin_client.get(reverse("audits:wcag-definition-list"))

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 76 WCAG errors.</p>', html=True
    )


@pytest.mark.parametrize(
    "fieldname",
    ["type", "name", "description", "url_on_w3", "report_boilerplate"],
)
def test_wcag_definition_list_view_filters(fieldname, admin_client):
    """Test WCAG definition list cab be filtered by each field"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    setattr(wcag_definition, fieldname, "helcaraxe")
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        f"{reverse('audits:wcag-definition-list')}?wcag_definition_search=Helcaraxe"
    )

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 1 WCAG error.</p>', html=True
    )


def test_create_wcag_definition_works(admin_client):
    """
    Test that a successful WCAG definiton create creates the new
    WCAG definition and redirects to list.
    """
    response: HttpResponse = admin_client.post(
        reverse("audits:wcag-definition-create"),
        {
            "type": WCAG_DEFINITION_TYPE,
            "name": WCAG_DEFINITION_NAME,
            "url_on_w3": WCAG_DEFINITION_URL,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:wcag-definition-list")

    wcag_definition_from_db: Optional[WcagDefinition] = WcagDefinition.objects.last()

    assert wcag_definition_from_db is not None
    assert wcag_definition_from_db.type == WCAG_DEFINITION_TYPE
    assert wcag_definition_from_db.name == WCAG_DEFINITION_NAME
    assert wcag_definition_from_db.url_on_w3 == WCAG_DEFINITION_URL


def test_update_wcag_definition_works(admin_client):
    """
    Test that a successful WCAG definiton update updates the
    WCAG definition and redirects to list.
    """
    wcag_definition: Optional[WcagDefinition] = WcagDefinition.objects.first()

    wcag_definition_pk: int = wcag_definition.id  # type: ignore
    path_kwargs: Dict[str, int] = {"pk": wcag_definition_pk}

    response: HttpResponse = admin_client.post(
        reverse("audits:wcag-definition-update", kwargs=path_kwargs),
        {
            "type": WCAG_DEFINITION_TYPE,
            "name": WCAG_DEFINITION_NAME,
            "url_on_w3": WCAG_DEFINITION_URL,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:wcag-definition-list")

    wcag_definition_from_db: Optional[WcagDefinition] = WcagDefinition.objects.first()

    assert wcag_definition_from_db is not None
    assert wcag_definition_from_db.type == WCAG_DEFINITION_TYPE
    assert wcag_definition_from_db.name == WCAG_DEFINITION_NAME
    assert wcag_definition_from_db.url_on_w3 == WCAG_DEFINITION_URL


def test_clear_published_report_data_updated_time_view(admin_client):
    """Test that clear report data updated time view empties that field"""
    audit: Audit = create_audit()
    audit.published_report_data_updated_time = timezone.now()
    audit.save()
    audit_pk: Dict[str, int] = {"pk": audit.id}

    admin_client.get(
        reverse("audits:clear-outdated-published-report-warning", kwargs=audit_pk)
    )

    audit_from_db: Audit = Audit.objects.get(**audit_pk)

    assert audit_from_db.published_report_data_updated_time is None


def test_update_audit_checks_version(admin_client):
    """Test that updating an audit shows an error if the version of the audit has changed"""
    audit: Audit = create_audit()
    case: Case = audit.case

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id}),
        {
            "version": audit.version - 1,
            "case-version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {str(audit)} has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-website-decision",
        "audits:edit-statement-decision",
        "audits:edit-audit-retest-website-decision",
        "audits:edit-audit-retest-statement-decision",
    ],
)
def test_update_audit_checks_case_version(url_name, admin_client):
    """Test that updating a case shows an error if the version of the case has changed"""
    audit: Audit = create_audit()
    case: Case = audit.case

    response: HttpResponse = admin_client.post(
        reverse(url_name, kwargs={"pk": audit.id}),
        {
            "version": audit.version,
            "case-version": case.version - 1,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {str(case)} has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:audit-detail",
        "audits:edit-audit-metadata",
        "audits:audit-retest-detail",
        "audits:edit-audit-retest-statement-2",
    ],
)
def test_frequently_used_links_displayed(url_name, admin_client):
    """
    Test that the frequently used links are displayed
    """
    audit: Audit = create_audit()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": audit.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Frequently used links")
    assertContains(response, "View outstanding issues")
    assertContains(response, "View email template")
    assertContains(response, "No published report")
    assertContains(response, "View website")
    assertContains(response, "Link to case view")
    assertContains(response, "Markdown cheatsheet")
