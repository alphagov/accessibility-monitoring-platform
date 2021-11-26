"""
Tests for audits views
"""
import pytest

from typing import Dict, List

from pytest_django.asserts import assertContains

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import Case
from ..models import PAGE_TYPE_EXTRA, Audit, Page
from ..utils import create_pages_and_checks_for_new_audit

EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"


def create_audit() -> Audit:
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    return audit


def create_audit_and_pages() -> Audit:
    audit: Audit = create_audit()
    user: User = User.objects.create()
    create_pages_and_checks_for_new_audit(audit=audit, user=user)
    return audit


def get_path_kwargs(audit: Audit, path_name: str) -> Dict[str, int]:
    if "-manual" in path_name or "-axe" in path_name:
        return {
            "case_id": audit.case.id,  # type: ignore
            "audit_id": audit.id,  # type: ignore
            "page_id": audit.next_page.id,
        }
    return {
        "case_id": audit.case.id,  # type: ignore
        "pk": audit.id,  # type: ignore
    }


def test_delete_audit_view(admin_client):
    """Test that delete audit view deletes audit"""
    audit: Audit = create_audit()

    response: HttpResponse = admin_client.post(
        reverse("audits:delete-audit", kwargs={"pk": audit.id, "case_id": audit.case.id}),  # type: ignore
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
        reverse("audits:restore-audit", kwargs={"pk": audit.id, "case_id": audit.case.id}),  # type: ignore
        {
            "version": audit.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:audit-detail", kwargs={"pk": audit.id, "case_id": audit.case.id})  # type: ignore

    audit_from_db: Audit = Audit.objects.get(pk=audit.id)  # type: ignore

    assert audit_from_db.is_deleted is False


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:audit-detail", "View test"),
        ("audits:edit-audit-metadata", "Edit test | Test metadata"),
        ("audits:edit-audit-pages", "Edit test | Pages"),
        ("audits:edit-audit-pdf", "Edit test | PDF tests"),
        ("audits:edit-audit-statement-1", "Edit test | Accessibility statement Pt. 1"),
        ("audits:edit-audit-statement-2", "Edit test | Accessibility statement Pt. 2"),
        ("audits:edit-audit-summary", "Edit test | Test summary"),
        ("audits:edit-audit-report-options", "Edit test | Report options"),
        ("audits:edit-audit-report-text", "Edit test | Report text"),
    ],
)
def test_audit_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-specific view page loads"""
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"case_id": audit.case.id, "pk": audit.id})  # type: ignore
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:edit-audit-manual", "Edit test | Manual tests"),
        ("audits:edit-audit-axe", "Edit test | Axe and colour contrast tests"),
    ],
)
def test_audit_page_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-page-specific view page loads"""
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"case_id": audit.case.id, "audit_id": audit.id, "page_id": audit.next_page.id})  # type: ignore
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name, expected_view_page_anchor",
    [
        ("audits:edit-audit-metadata", "save_continue", "audits:edit-audit-pages", ""),
        ("audits:edit-audit-metadata", "save_exit", "audits:audit-detail", "#audit-metadata"),
        ("audits:edit-audit-pages", "save_continue", "audits:edit-audit-manual", ""),
        ("audits:edit-audit-pages", "save_exit", "audits:audit-detail", "#audit-pages"),
        ("audits:edit-audit-manual", "save_continue", "audits:edit-audit-axe", ""),
        ("audits:edit-audit-manual", "save_exit", "audits:audit-detail", "#audit-manual"),
        ("audits:edit-audit-axe", "save_continue", "audits:edit-audit-pdf", ""),
        ("audits:edit-audit-axe", "save_exit", "audits:audit-detail", "#audit-axe"),
        ("audits:edit-audit-pdf", "save_continue", "audits:edit-audit-statement-1", ""),
        ("audits:edit-audit-pdf", "save_exit", "audits:audit-detail", "#audit-pdf"),
        ("audits:edit-audit-statement-1", "save_continue", "audits:edit-audit-statement-2", ""),
        ("audits:edit-audit-statement-1", "save_exit", "audits:audit-detail", "#audit-statement"),
        ("audits:edit-audit-statement-2", "save_continue", "audits:edit-audit-summary", ""),
        ("audits:edit-audit-statement-2", "save_exit", "audits:audit-detail", "#audit-statement"),
        ("audits:edit-audit-summary", "save_continue", "audits:edit-audit-report-options", ""),
        ("audits:edit-audit-summary", "save_exit", "audits:audit-detail", ""),
        ("audits:edit-audit-report-options", "save_continue", "audits:edit-audit-report-text", ""),
        ("audits:edit-audit-report-options", "save_exit", "audits:audit-detail", "#audit-report-options"),
        ("audits:edit-audit-report-text", "save_exit", "audits:audit-detail", "#audit-report-text"),
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
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=get_path_kwargs(audit=audit, path_name=path_name)),  # type: ignore
        {
            "version": audit.version,
            "next_page": audit.next_page.id,
            button_name: "Button value",
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse(expected_redirect_path_name, kwargs=get_path_kwargs(audit=audit, path_name=expected_redirect_path_name))}{expected_view_page_anchor}'  # type: ignore
    )


def test_add_extra_page_form_appears(admin_client):
    """
    Test that pressing the save and create additional page button adds an extra page form
    """
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"case_id": audit.case.id, "pk": audit.id}),  # type: ignore
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
        reverse("audits:edit-audit-pages", kwargs={"case_id": audit.case.id, "pk": audit.id}),  # type: ignore
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

    extra_pages: List[Page] = list(Page.objects.filter(audit=audit, type=PAGE_TYPE_EXTRA))  # type: ignore

    assert len(extra_pages) == 1
    assert extra_pages[0].name == EXTRA_PAGE_NAME
    assert extra_pages[0].url == EXTRA_PAGE_URL
