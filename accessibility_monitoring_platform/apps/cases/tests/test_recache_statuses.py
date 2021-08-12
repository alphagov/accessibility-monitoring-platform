"""
Test for recache_statuses command
"""
import pytest
from django.core.management import call_command
from ..models import Case

@pytest.mark.django_db
def test_recache_statuses_can_be_called():
    """Test load_test_cases_csv populates the database"""
    call_command("recache_statuses")

    assert Case.objects.count() == 0
