"""
Tests for cases models
"""
import pytest
from typing import List

from ...cases.models import Case
from ...common.models import BOOLEAN_TRUE
from ..models import (
    Audit,
    Page,
    PAGE_TYPE_EXTRA,
    PAGE_TYPE_HOME,
    PAGE_TYPE_CONTACT,
    PAGE_TYPE_STATEMENT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_FORM,
    PAGE_TYPE_ALL,
)

PAGE_NAME = "Page name"


def create_audit_and_pages() -> Audit:
    """Create an audit with all types of page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for page_type in [
        PAGE_TYPE_EXTRA,
        PAGE_TYPE_HOME,
        PAGE_TYPE_CONTACT,
        PAGE_TYPE_STATEMENT,
        PAGE_TYPE_PDF,
        PAGE_TYPE_FORM,
        PAGE_TYPE_ALL,
    ]:
        Page.objects.create(audit=audit, type=page_type)
    Page.objects.create(audit=audit, type=PAGE_TYPE_EXTRA, is_deleted=True)
    Page.objects.create(audit=audit, type=PAGE_TYPE_EXTRA, not_found=BOOLEAN_TRUE)
    return audit


@pytest.mark.django_db
def test_audit_all_pages_returns_all_pages_except_pdf():
    """
    Test all_pages attribute of audit does not include pages of type pdf.
    Deleted and pages which were not found are also excluded.
    """
    audit: Audit = create_audit_and_pages()

    assert len(audit.all_pages) == 6
    assert PAGE_TYPE_PDF not in [page.type for page in audit.all_pages]


@pytest.mark.django_db
def test_audit_html_pages_returns_all_pages_except_all_pages():
    """
    Test html_pages attribute of audit does not include pages of types PDF or all.
    """
    audit: Audit = create_audit_and_pages()
    page_types: List[str] = [page.type for page in audit.html_pages]

    assert len(audit.html_pages) == 5
    assert PAGE_TYPE_PDF not in page_types
    assert PAGE_TYPE_ALL not in page_types


@pytest.mark.django_db
def test_audit_standard_pages_returns_no_extra_or_all_pages():
    """
    Test standard_pages attribute of audit does not include pages of type PDF,
    all pages or extra.
    """
    audit: Audit = create_audit_and_pages()
    page_types: List[str] = [page.type for page in audit.standard_pages]

    assert len(audit.standard_pages) == 5
    assert PAGE_TYPE_ALL not in page_types
    assert PAGE_TYPE_EXTRA not in page_types


@pytest.mark.django_db
def test_audit_extra_pages_returns_only_extra_pages():
    """
    Test extra_pages attribute of audit returns only pages of type extra.
    """
    audit: Audit = create_audit_and_pages()

    assert len(audit.extra_pages) == 1
    assert list(audit.extra_pages)[0].type == PAGE_TYPE_EXTRA


@pytest.mark.django_db
def test_page_string():
    """
    Test Page string is name if present otherwise type
    """
    audit: Audit = create_audit_and_pages()
    page: Page = audit.all_pages[0]

    assert str(page) == "Page"

    page.name = PAGE_NAME

    assert str(page) == PAGE_NAME
