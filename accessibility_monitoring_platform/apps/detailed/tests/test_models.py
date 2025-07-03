"""
Tests for detailed models
"""

import pytest

from ..models import Contact, DetailedCase


@pytest.mark.django_db
def test_detailed_case_identifier():
    """Test DetailedCase.case_identifier"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    assert detailed_case.case_identifier == "#D-1"


def test_contact_str():
    """Test Contact.__str__()"""
    contact: Contact = Contact(name="Contact Name", contact_point="name@example.com")

    assert str(contact) == "Contact Name name@example.com"
