"""
Test for init_int_test_data command which resets the contents of the database
for integration tests. Also used to reset data for development.
"""
import pytest
from django.core.management import call_command

from ...cases.models import Case


@pytest.mark.django_db
def test_recache_statuses_can_be_called():
    """Test recache_statuses can be called"""
    Case.objects.create()
    Case.objects.create()
    call_command("init_int_test_data")
    assert Case.objects.count() == 1
