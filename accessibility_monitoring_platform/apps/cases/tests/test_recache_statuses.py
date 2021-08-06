"""
Test for recache_statuses command
"""
import pytest
from django.core.management import call_command
from ..models import Case

@pytest.mark.django_db
def test_load_test_cases_csv_command():
    """Test load_test_cases_csv populates the database"""
    call_command("recache_statuses")

    assert Case.objects.count() == 0
