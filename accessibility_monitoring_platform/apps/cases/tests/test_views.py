"""
Tests for cases views
"""
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from ..models import Case, Contact


class CaseDetailViewTestCase(TestCase):
    """
    Tests for CaseDetailView

    Methods
    -------
    setUp()
        Sets up the test environment with a case with archived and unarchived contacts

    test_archived_contact_not_included_in_context()
        Tests that case detail includes only unarchived contact
    """

    def setUp(self):
        """ Create case with archived and unarchived contacts """
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        self.case = Case.objects.create()
        Contact.objects.create(case=self.case)
        Contact.objects.create(case=self.case, is_archived=True)

    def test_archived_contact_not_included_in_context(self):
        """ Tests that case detail includes only unarchived contact """
        self.client.login(username="testuser", password="12345")
        response = self.client.get(
            reverse("cases:case-detail", kwargs={"pk": self.case.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["contacts"],
            Contact.objects.filter(case=self.case, is_archived=False),
        )
