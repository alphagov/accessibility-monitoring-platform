"""
Test for init_int_test_data command which resets the contents of the database
for integration tests. Also used to reset data for development.
"""

import pytest
from django.core.management import call_command

from ...detailed.models import DetailedCase
from ...mobile.models import MobileCase
from ...simplified.models import SimplifiedCase


@pytest.mark.django_db
def test_init_int_test_data_can_be_called():
    """Test init_int_test_data can be called"""
    DetailedCase.objects.create()
    MobileCase.objects.create()
    SimplifiedCase.objects.create()
    SimplifiedCase.objects.create()

    call_command("init_int_test_data")

    assert DetailedCase.objects.count() == 0
    assert MobileCase.objects.count() == 0
    assert SimplifiedCase.objects.count() == 1
