"""
Tests for mobile models
"""

import pytest

from ..models import MobileCase


@pytest.mark.django_db
def test_mobile_case_str():
    """Test MobileCase.__str__()"""
    mobile_case: MobileCase = MobileCase.objects.create(app_name="App name")

    assert str(mobile_case) == "App name | #M-1"


@pytest.mark.django_db
def test_mobile_case_title():
    """Test MobileCase.title"""
    mobile_case: MobileCase = MobileCase.objects.create(app_name="App name")

    assert mobile_case.title == "App name &nbsp;|&nbsp; #M-1"


@pytest.mark.django_db
def test_mobile_case_identifier():
    """Test MobileCase.case_identifier"""
    mobile_case: MobileCase = MobileCase.objects.create()

    assert mobile_case.case_identifier == "#M-1"
