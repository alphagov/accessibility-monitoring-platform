"""
Tests for users models
"""
import pytest

from ..models import AllowedEmail

EMAIL_ADDRESS: str = "admin@email.com"


@pytest.mark.django_db
def test_email_inclusion_list_returns_str():
    """Tests if AllowedEmail returns an email address"""
    AllowedEmail.objects.create(inclusion_email=EMAIL_ADDRESS)
    email_list: AllowedEmail = AllowedEmail.objects.get(inclusion_email=EMAIL_ADDRESS)
    assert str(email_list) == EMAIL_ADDRESS
