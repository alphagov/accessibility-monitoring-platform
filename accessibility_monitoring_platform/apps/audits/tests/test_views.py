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
    Page,
    WcagDefinition,
    TEST_TYPE_AXE,
    TEST_TYPE_PDF,
)

WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
WCAG_TYPE_MANUAL_NAME: str = "WCAG Manual name"
WCAG_TYPE_PDF_NAME: str = "WCAG PDF name"
EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"
CHECK_RESULT_NOTES: str = "Check result notes"


def create_audit() -> Audit:
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    return audit


def create_audit_and_wcag() -> Audit:
    audit: Audit = create_audit()
    WcagDefinition.objects.create(type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME)
    WcagDefinition.objects.create(type=TEST_TYPE_PDF, name=WCAG_TYPE_PDF_NAME)
    return audit


def test_delete_audit_view(admin_client):
    """Test that delete audit view deletes audit"""
    audit: Audit = create_audit()

    response: HttpResponse = admin_client.post(
        reverse("audits:delete-audit", kwargs={"pk": audit.id}),  # type: ignore
        {
            "version": audit.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "cases:edit-test-results", kwargs={"pk": audit.case.id}
    )

    audit_from_db: Audit = Audit.objects.get(pk=audit.id)  # type: ignore

    assert audit_from_db.is_deleted


def test_restore_audit_view(admin_client):
    """Test that restore audit view restores audit"""
    audit: Audit = create_audit()
    audit.is_deleted = True
    audit.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:restore-audit", kwargs={"pk": audit.id}),  # type: ignore
        {
            "version": audit.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:audit-detail", kwargs={"pk": audit.id})  # type: ignore

    audit_from_db: Audit = Audit.objects.get(pk=audit.id)  # type: ignore

    assert audit_from_db.is_deleted is False


def test_delete_page_view(admin_client):
    """Test that delete page view deletes page"""
    audit: Audit = create_audit()
    page: Page = Page.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:delete-page",
            kwargs={"pk": page.id},  # type: ignore
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-website",
        kwargs={"pk": audit.id},  # type: ignore
    )

    page_from_db: Page = Page.objects.get(pk=page.id)  # type: ignore

    assert page_from_db.is_deleted


def test_restore_page_view(admin_client):
    """Test that restore page view restores audit"""
    audit: Audit = create_audit()
    page: Page = Page.objects.create(audit=audit, is_deleted=True)

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:restore-page",
            kwargs={"pk": page.id},  # type: ignore
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-website",
        kwargs={"pk": audit.id},  # type: ignore
    )

    page_from_db: Page = Page.objects.get(pk=page.id)  # type: ignore

    assert page_from_db.is_deleted is False


@pytest.mark.parametrize(
    "button_name, expected_redirect_url",
    [
        (
            "save_continue",
            reverse("audits:edit-audit-metadata", kwargs={"pk": 1}),
        ),
        ("save_exit", reverse("cases:edit-test-results", kwargs={"pk": 1})),
    ],
)
def test_create_audit_redirects_based_on_button_pressed(
    button_name, expected_redirect_url, admin_client
):
    """Test that audit create redirects based on the button pressed"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}  # type: ignore

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            button_name: "Button value",
        },
    )

    assert response.status_code == 302

    assert response.url == expected_redirect_url


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:audit-detail", "View test"),
        ("audits:edit-audit-metadata", "Edit test | Test metadata"),
        ("audits:edit-audit-website", "Edit test | Website test"),
        ("audits:edit-audit-statement-1", "Edit test | Accessibility statement Pt. 1"),
        ("audits:edit-audit-statement-2", "Edit test | Accessibility statement Pt. 2"),
        ("audits:edit-audit-summary", "Edit test | Test summary"),
        ("audits:edit-audit-report-options", "Edit test | Report options"),
        ("audits:edit-audit-report-text", "Edit test | Report text"),
    ],
)
def test_audit_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-specific view page loads"""
    audit: Audit = create_audit_and_wcag()

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs={"pk": audit.id}))  # type: ignore

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name, expected_view_page_anchor",
    [
        (
            "audits:edit-audit-metadata",
            "save_continue",
            "audits:edit-audit-website",
            "",
        ),
        (
            "audits:edit-audit-metadata",
            "save_exit",
            "audits:audit-detail",
            "#audit-metadata",
        ),
        (
            "audits:edit-audit-website",
            "continue",
            "audits:edit-audit-statement-1",
            "",
        ),
        (
            "audits:edit-audit-statement-1",
            "save_continue",
            "audits:edit-audit-statement-2",
            "",
        ),
        (
            "audits:edit-audit-statement-1",
            "save_exit",
            "audits:audit-detail",
            "#audit-statement",
        ),
        (
            "audits:edit-audit-statement-2",
            "save_continue",
            "audits:edit-audit-summary",
            "",
        ),
        (
            "audits:edit-audit-statement-2",
            "save_exit",
            "audits:audit-detail",
            "#audit-statement",
        ),
        (
            "audits:edit-audit-summary",
            "save_continue",
            "audits:edit-audit-report-options",
            "",
        ),
        ("audits:edit-audit-summary", "save_exit", "audits:audit-detail", ""),
        (
            "audits:edit-audit-report-options",
            "save_continue",
            "audits:edit-audit-report-text",
            "",
        ),
        (
            "audits:edit-audit-report-options",
            "save_exit",
            "audits:audit-detail",
            "#audit-report-options",
        ),
        (
            "audits:edit-audit-report-text",
            "save_exit",
            "audits:audit-detail",
            "#audit-report-text",
        ),
    ],
)
def test_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    expected_view_page_anchor,
    admin_client,
):
    """Test that a successful audit update redirects based on the button pressed"""
    audit: Audit = create_audit_and_wcag()

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs={"pk": audit.id}),  # type: ignore
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

    expected_path: str = reverse(
        expected_redirect_path_name,
        kwargs={"pk": audit.id},  # type: ignore
    )
    assert response.url == f"{expected_path}{expected_view_page_anchor}"  # type: ignore
