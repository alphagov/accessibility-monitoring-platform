"""
Test - function to derive page title from url path
"""
import pytest

from django.urls import reverse

from ...audits.models import Audit, Page
from ...cases.models import Case
from ...reminders.models import Reminder

from ..page_title_utils import get_page_title

ORGANISATION_NAME: str = "Organisation name"


@pytest.mark.parametrize(
    "path, page_title",
    [
        (reverse("cases:case-list"), "Search"),
        (reverse("cases:case-create"), "Create case"),
        (reverse("common:contact-admin"), "Contact admin"),
        (reverse("common:issue-report"), "Report an issue"),
    ],
)
def test_page_title_returned(path, page_title):
    """Check page title found"""
    assert get_page_title(path) == page_title


@pytest.mark.django_db
def test_page_title_for_case_page_returned():
    """Page title for case-specific page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    path: str = reverse("cases:case-detail", kwargs={"pk": case.id})

    assert get_page_title(path) == f"{ORGANISATION_NAME} | View case"


@pytest.mark.django_db
def test_page_title_for_non_existant_case_returned():
    """Page title for non-existant case"""
    path: str = reverse("cases:case-detail", kwargs={"pk": 0})

    assert get_page_title(path) == f"Case does not exist: {path}"


@pytest.mark.django_db
def test_page_title_for_audit_page_returned():
    """Page title for audit-specific page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    audit: Audit = Audit.objects.create(case=case)
    path: str = reverse("audits:audit-detail", kwargs={"pk": audit.id})

    assert get_page_title(path) == f"{ORGANISATION_NAME} | View test"


@pytest.mark.django_db
def test_page_title_for_non_existant_audit_returned():
    """Page title for non-existant audit"""
    path: str = reverse("audits:audit-detail", kwargs={"pk": 0})

    assert get_page_title(path) == f"Audit does not exist: {path}"


@pytest.mark.django_db
def test_page_title_for_page_returned():
    """Page title for page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, name="Test page")
    path: str = reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id})

    assert get_page_title(path) == f"{ORGANISATION_NAME} | Testing {page}"


@pytest.mark.django_db
def test_page_title_for_non_existant_page_returned():
    """Page title for non-existant page"""
    path: str = reverse("audits:edit-audit-page-checks", kwargs={"pk": 0})

    assert get_page_title(path) == f"Page does not exist: {path}"


@pytest.mark.django_db
def test_page_title_for_reminder_page_returned():
    """Page title for page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    path: str = reverse("reminders:reminder-create", kwargs={"case_id": case.id})

    assert get_page_title(path) == f"{ORGANISATION_NAME} | Reminder"


@pytest.mark.django_db
def test_page_title_for_reminder_of_non_existant_case_returned():
    """Page title for non-existant case"""
    path: str = reverse("reminders:reminder-create", kwargs={"case_id": 0})

    assert get_page_title(path) == f"Case does not exist: {path}"


@pytest.mark.django_db
def test_page_title_for_audit_create_page_returned():
    """Page title for page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    path: str = reverse("audits:audit-create", kwargs={"case_id": case.id})

    assert get_page_title(path) == f"{ORGANISATION_NAME} | Create test"


@pytest.mark.django_db
def test_page_title_for_audit_create_of_non_existant_case_returned():
    """Page title for non-existant case"""
    path: str = reverse("audits:audit-create", kwargs={"case_id": 0})

    assert get_page_title(path) == f"Case does not exist: {path}"
