import pytest

from ...cases.models import Case
from ..utils import get_exportable_cases
from .test_forms import CUTOFF_DATE, create_exportable_case


@pytest.mark.django_db
def test_get_exportable_case():
    """Tests get_exportable_cases gets exportable cases for enforcement body"""
    case: Case = create_exportable_case()

    assert get_exportable_cases(
        cutoff_date=CUTOFF_DATE, enforcement_body=Case.EnforcementBody.EHRC
    ) == [case]
    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE, enforcement_body=Case.EnforcementBody.ECNI
        )
        == []
    )

    case.enforcement_body = Case.EnforcementBody.ECNI
    case.save()

    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE, enforcement_body=Case.EnforcementBody.EHRC
        )
        == []
    )
    assert get_exportable_cases(
        cutoff_date=CUTOFF_DATE, enforcement_body=Case.EnforcementBody.ECNI
    ) == [case]
