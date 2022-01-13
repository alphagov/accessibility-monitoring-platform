"""
Tests for audits views
"""
import pytest

from typing import Dict

from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import Case
from ..models import (
    Audit,
    CheckResult,
    Page,
    WcagDefinition,
    CHECK_RESULT_ERROR,
    CHECK_RESULT_NOT_TESTED,
    PAGE_TYPE_EXTRA,
    TEST_TYPE_AXE,
    TEST_TYPE_PDF,
)

WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
WCAG_TYPE_MANUAL_NAME: str = "WCAG Manual name"
WCAG_TYPE_PDF_NAME: str = "WCAG PDF name"
EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"
CHECK_RESULT_NOTES: str = "Check result notes"
NEW_PAGE_NAME = "New page name"
NEW_PAGE_URL = "https://example.com/extra"
UPDATED_PAGE_NAME = "Updated page name"
UPDATED_PAGE_URL = "https://example.com/updated"


def create_audit() -> Audit:
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    return audit


def create_audit_and_wcag() -> Audit:
    audit: Audit = create_audit()
    WcagDefinition.objects.all().delete()
    WcagDefinition.objects.create(id=1, type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME)
    WcagDefinition.objects.create(id=2, type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME)
    return audit


def test_delete_audit_view(admin_client):
    """Test that delete audit view deletes audit"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:delete-audit", kwargs=audit_pk),
        {
            "version": audit.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "cases:edit-test-results", kwargs={"pk": audit.case.id}
    )

    audit_from_db: Audit = Audit.objects.get(**audit_pk)

    assert audit_from_db.is_deleted


def test_restore_audit_view(admin_client):
    """Test that restore audit view restores audit"""
    audit: Audit = create_audit()
    audit.is_deleted = True
    audit.save()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:restore-audit", kwargs=audit_pk),
        {
            "version": audit.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:audit-detail", kwargs=audit_pk)

    audit_from_db: Audit = Audit.objects.get(**audit_pk)

    assert audit_from_db.is_deleted is False


def test_delete_page_view(admin_client):
    """Test that delete page view deletes page"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:delete-page",
            kwargs=page_pk,
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-website",
        kwargs=audit_pk,
    )

    page_from_db: Page = Page.objects.get(**page_pk)

    assert page_from_db.is_deleted


def test_restore_page_view(admin_client):
    """Test that restore page view restores audit"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
    page: Page = Page.objects.create(audit=audit, is_deleted=True)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:restore-page",
            kwargs=page_pk,
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-website",
        kwargs=audit_pk,
    )

    page_from_db: Page = Page.objects.get(**page_pk)

    assert page_from_db.is_deleted is False


def test_create_audit_redirects(admin_client):
    """Test that audit create redirects to audit metadata"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse("audits:edit-audit-metadata", kwargs={"pk": 1})


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:audit-detail", "View test"),
        ("audits:edit-audit-metadata", "Test metadata"),
        ("audits:edit-audit-website", "Website test"),
        ("audits:edit-audit-statement-1", "Accessibility statement Pt. 1"),
        ("audits:edit-audit-statement-2", "Accessibility statement Pt. 2"),
        ("audits:edit-audit-summary", "Test summary"),
        ("audits:edit-audit-report-options", "Report options"),
        ("audits:edit-audit-report-text", "Report text"),
    ],
)
def test_audit_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-specific view page loads"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=audit_pk))

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-audit-metadata", "save", "audits:edit-audit-metadata"),
        ("audits:edit-audit-website", "save", "audits:edit-audit-website"),
        ("audits:edit-audit-statement-1", "save", "audits:edit-audit-statement-1"),
        ("audits:edit-audit-statement-2", "save", "audits:edit-audit-statement-2"),
        ("audits:edit-audit-summary", "save", "audits:edit-audit-summary"),
        ("audits:edit-audit-summary", "save", "audits:edit-audit-summary"),
        (
            "audits:edit-audit-report-options",
            "save",
            "audits:edit-audit-report-options",
        ),
        ("audits:edit-audit-report-text", "save", "audits:edit-audit-report-text"),
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
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_add_page_page_loads(admin_client):
    """Test page edit view page loads"""
    audit: Audit = create_audit()
    audit_id: Dict[str, int] = {"audit_id": audit.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-create-page", kwargs=audit_id)
    )

    assert response.status_code == 200

    assertContains(response, "Add page")


def test_add_page_create_page(admin_client):
    """
    Test adding an extra page creates the page and redirects to the website UI page
    """
    audit: Audit = create_audit_and_wcag()
    audit_id: Dict[str, int] = {"audit_id": audit.id}  # type: ignore
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-create-page", kwargs=audit_id),
        {
            "save_return": "Asave and return",
            "name": NEW_PAGE_NAME,
            "url": NEW_PAGE_URL,
            "page_type": PAGE_TYPE_EXTRA,
        },
    )
    assert response.status_code == 302

    expected_path: str = reverse("audits:edit-audit-website", kwargs=audit_pk)
    assert response.url == expected_path

    new_page: Page = Page.objects.get(audit=audit, page_type=PAGE_TYPE_EXTRA)

    assert new_page.name == NEW_PAGE_NAME
    assert new_page.url == NEW_PAGE_URL


def test_page_edit_page_loads(admin_client):
    """Test page edit view page loads"""
    audit: Audit = create_audit()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Edit page details")


def test_page_edit_view_redirects_to_website_page(admin_client):
    """Test editing a page redirects to website page"""
    audit: Audit = create_audit()
    audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page", kwargs=page_pk),
        {
            "save_return": "Save and return",
            "name": UPDATED_PAGE_NAME,
            "url": UPDATED_PAGE_URL,
            "page_type": PAGE_TYPE_EXTRA,
        },
    )
    assert response.status_code == 302

    expected_path: str = reverse("audits:edit-audit-website", kwargs=audit_pk)
    assert response.url == expected_path

    updated_page: Page = Page.objects.get(**page_pk)

    assert updated_page.name == UPDATED_PAGE_NAME
    assert updated_page.url == UPDATED_PAGE_URL


def test_page_checks_edit_page_loads(admin_client):
    """Test page checks edit view page loads and contains all wcag definitions"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Testing Additional page")
    assertContains(response, "Showing 2 errors")
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)


def test_page_checks_edit_saves_results(admin_client):
    """Test page checks edit view saves the entered results"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore
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
            "form-0-wcag_definition": wcag_definition_axe.id,  # type: ignore
            "form-0-check_result_state": CHECK_RESULT_ERROR,
            "form-0-notes": CHECK_RESULT_NOTES,
            "form-1-wcag_definition": wcag_definition_pdf.id,  # type: ignore
            "form-1-check_result_state": CHECK_RESULT_ERROR,
            "form-1-notes": CHECK_RESULT_NOTES,
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


def test_page_checks_edit_stays_on_page(admin_client):
    """Test that a successful page checks edit stays on the page"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: Dict[str, int] = {"pk": page.id}  # type: ignore
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
