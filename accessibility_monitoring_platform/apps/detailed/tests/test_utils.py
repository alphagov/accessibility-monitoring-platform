"""
Test utility functions of cases app
"""

import pytest
from django.http import HttpRequest
from django.urls import reverse

from ...cases.utils import CaseDetailSection
from ...common.sitemap import Sitemap
from ..models import DetailedCase
from ..utils import get_detailed_case_detail_sections

ORGANISATION_NAME: str = "Organisation name one"


@pytest.mark.django_db
def test_get_detailed_case_detail_sections(rf):
    """Test get_detailed_case_detail_sections builds list of detail sections"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    request: HttpRequest = rf.get(
        reverse("detailed:case-view-and-search", kwargs={"pk": detailed_case.id}),
    )
    sitemap: Sitemap = Sitemap(request=request)

    sections: list[CaseDetailSection] = get_detailed_case_detail_sections(
        detailed_case=detailed_case, sitemap=sitemap
    )

    assert sections[0].pages[0].display_fields[1].value == ORGANISATION_NAME
