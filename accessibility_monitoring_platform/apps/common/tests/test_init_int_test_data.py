"""
Test for init_int_test_data command which resets the contents of the database
for integration tests. Also used to reset data for development.
"""
import pytest
from django.core.management import call_command

from ...cases.models import Case


@pytest.mark.django_db
def test_init_int_test_data_can_be_called():
    """Test init_int_test_data can be called"""
    Case.objects.create()
    Case.objects.create()
    call_command("init_int_test_data")
    assert Case.objects.count() == 1
