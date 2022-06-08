"""
Test - function to derive page title from url path
"""
import pytest

from django.urls import reverse

from ...cases.models import Case

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
    path: str = reverse("cases:case-detail", kwargs={"pk": case.id})  # type: ignore

    assert get_page_title(path) == f"{ORGANISATION_NAME} | View case"
