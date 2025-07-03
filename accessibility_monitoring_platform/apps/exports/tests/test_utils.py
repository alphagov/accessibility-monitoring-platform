import pytest

from ...simplified.models import SimplifiedCase
from ..utils import get_exportable_cases
from .test_forms import CUTOFF_DATE, create_exportable_case


@pytest.mark.django_db
def test_get_exportable_case():
    """Tests get_exportable_cases gets exportable cases for enforcement body"""
    simplified_case: SimplifiedCase = create_exportable_case()

    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.EHRC,
        ).first()
        == simplified_case
    )
    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.ECNI,
        ).first()
        is None
    )

    simplified_case.enforcement_body = SimplifiedCase.EnforcementBody.ECNI
    simplified_case.save()

    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.EHRC,
        ).first()
        is None
    )
    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.ECNI,
        ).first()
        == simplified_case
    )
