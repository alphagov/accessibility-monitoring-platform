from datetime import datetime

from django.test import TestCase

from ..models import Case, Contact

DOMAIN = "example.com"
HOME_PAGE_URL = f"https://{DOMAIN}/index.html"

class CaseTestCase(TestCase):
    """
    Tests for Case model

    Methods
    -------
    setUp()
        Sets up the test environment with a case

    test_case_created_timestamp_is_populated()
        Test the created field is populated the first time the Case is saved

    test_case_created_timestamp_is_not_updated()
        Test the created field is not updated on subsequent saves
    """
    def setUp(self):
        self.case = Case.objects.create(home_page_url=HOME_PAGE_URL)
        self.case_from_db = Case.objects.get(pk=self.case.id)


    def test_case_created_timestamp_is_populated(self):
        """ Test the Case created field is populated the first time the Case is saved """
        self.assertTrue(self.case_from_db.created is not None)
        self.assertTrue(isinstance(self.case_from_db.created, datetime))


    def test_case_created_timestamp_is_not_updated(self):
        """ Test the Case created field is not updated on subsequent saves """
        original_created_timestamp = self.case.created
        updated_organisation_name = "updated organisation name"
        self.case_from_db.organisation_name = updated_organisation_name
        self.case_from_db.save()
        updated_case = Case.objects.get(pk=self.case.id)
        self.assertTrue(updated_case.organisation_name == updated_organisation_name)
        self.assertTrue(updated_case.created == original_created_timestamp)

    def test_case_domain_is_populated_from_home_page_url(self):
        """ Test the Case domain field is populated from the home_page_url """
        self.assertTrue(self.case_from_db.domain == DOMAIN)

    def test_case_completed_timestamp_is_updated_on_completion(self):
        """ Test the Case completed field is updated when is_case_completed flag is set """
        self.assertTrue(self.case_from_db.completed is None)
        self.case_from_db.is_case_completed = True
        self.case_from_db.save()
        updated_case = Case.objects.get(pk=self.case.id)
        self.assertTrue(updated_case.completed is not None)
        self.assertTrue(isinstance(updated_case.completed, datetime))


class ContactTestCase(TestCase):
    """
    Tests for Contact model

    Methods
    -------
    setUp()
        Sets up the test environment with a contact

    test_contact_name_is_as_expected()
        Test that name is a combination of first_name and last_name

    test_contact_created_timestamp_is_populated()
        Test the created field is populated the first time the Contact is saved

    test_contact_created_timestamp_is_not_updated()
        Test the created field is not updated on subsequent save
    """
    def setUp(self):
        case = Case.objects.create()
        self.contact = Contact.objects.create(
            case=case,
            first_name="Joe",
            last_name="Bloggs",
        )
        self.contact_from_db = Contact.objects.get(pk=self.contact.id)

    def test_contact_name_is_as_expected(self):
        """ Test that name is a combination of first_name and last_name """
        self.assertTrue(self.contact.name == "Joe Bloggs")

    def test_contact_created_timestamp_is_populated(self):
        """ Test the created field is populated the first time the Contact is saved """
        self.assertTrue(self.contact_from_db.created != None)
        self.assertTrue(isinstance(self.contact_from_db.created, datetime))


    def test_contact_created_timestamp_is_not_updated(self):
        """ Test the created field is not updated on subsequent save """
        original_created_timestamp = self.contact_from_db.created
        updated_first_name = "updated first name"
        self.contact_from_db.first_name = updated_first_name
        self.contact_from_db.save()
        updated_contact = Contact.objects.get(pk=self.contact.id)
        self.assertTrue(updated_contact.first_name == updated_first_name)
        self.assertTrue(updated_contact.created == original_created_timestamp)
