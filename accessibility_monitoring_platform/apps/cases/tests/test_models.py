"""
Tests for cases models
"""

from datetime import datetime

import pytest

from ..models import BaseCase, Case


@pytest.mark.django_db
def test_case_identifier():
    """Test the Case.case_identifier"""
    case: Case = Case.objects.create()

    assert case.case_identifier == "#S-1"


@pytest.mark.django_db
def test_base_case_save_increments_version():
    """Test that saving a BaseCase increments its version"""
    base_case: BaseCase = BaseCase.objects.create()
    old_version: int = base_case.version
    base_case.save()

    assert base_case.version == old_version + 1


@pytest.mark.django_db
def test_new_base_case_defaults():
    """Test the default values of new BaseCase"""
    BaseCase.objects.create()
    base_case: BaseCase = BaseCase.objects.create(
        organisation_name="Org Name",
    )

    assert base_case.created is not None
    assert isinstance(base_case.created, datetime)
    assert base_case.created == base_case.updated
    assert base_case.case_number == 2
    assert base_case.case_identifier == "#S-2"
    assert base_case.get_absolute_url() == "/simplified/2/view/"
    assert str(base_case) == "Org Name | #S-2"
