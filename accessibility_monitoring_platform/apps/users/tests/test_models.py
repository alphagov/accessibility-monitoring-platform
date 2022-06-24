"""
Tests for users models
"""
import pytest

from ..models import EmailInclusionList

EMAIL_ADDRESS: str = "admin@email.com"


@pytest.mark.django_db
def test_email_inclusion_list_returns_str():
    """Tests if EmailInclusionList returns an email address"""
    EmailInclusionList.objects.create(inclusion_email=EMAIL_ADDRESS)
    email_list: EmailInclusionList = EmailInclusionList.objects.get(
        inclusion_email=EMAIL_ADDRESS
    )
    assert str(email_list) == EMAIL_ADDRESS
