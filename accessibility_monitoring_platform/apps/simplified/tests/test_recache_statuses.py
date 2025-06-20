"""
Test for recache_statuses command
"""

import pytest
from django.core.management import call_command

from ..models import SimplifiedCase


@pytest.mark.django_db
def test_recache_statuses_can_be_called():
    """Test recache_statuses can be called"""
    SimplifiedCase.objects.create()
    call_command("recache_statuses")
    assert SimplifiedCase.objects.count() == 1
