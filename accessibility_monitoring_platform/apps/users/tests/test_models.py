"""
Tests for model - users
"""

from django.test import TestCase
from ..models import EmailInclusionList


class EmailInclusionListTestCase(TestCase):
    """
    View tests for users

    Methods
    -------
    test_email_inclusion_list_returns_str()
        Returns a string
    """

    def test_email_inclusion_list_returns_str(self):
        """ Tests if EmailInclusionList returns a string """
        EmailInclusionList.objects.create(inclusion_email="admin@email.com")
        email_list: EmailInclusionList = EmailInclusionList.objects.get(
            inclusion_email="admin@email.com"
        )
        self.assertEqual(str(email_list), "admin@email.com")
