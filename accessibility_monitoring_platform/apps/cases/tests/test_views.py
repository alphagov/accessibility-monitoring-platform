"""
Tests for cases views
"""
from datetime import date, datetime, timedelta
import pytest
import pytz
from typing import List

from pytest_django.asserts import assertContains, assertNotContains

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify

from ..models import Case, Contact
from ..views import (
    ONE_WEEK_IN_DAYS,
    FOUR_WEEKS_IN_DAYS,
    TWELVE_WEEKS_IN_DAYS,
    find_duplicate_cases,
)
from ...common.utils import format_date, get_field_names_for_export

CONTACT_DETAIL = "test@email.com"
DOMAIN = "domain.com"
HOME_PAGE_URL = f"https://{DOMAIN}"
ORGANISATION_NAME = "Organisation name"
REPORT_SENT_DATE: date = date(2021, 2, 28)
OTHER_DATE: date = date(2020, 12, 31)
ONE_WEEK_FOLLOWUP_DUE_DATE = REPORT_SENT_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
FOUR_WEEK_FOLLOWUP_DUE_DATE = REPORT_SENT_DATE + timedelta(days=FOUR_WEEKS_IN_DAYS)
TWELVE_WEEK_FOLLOWUP_DUE_DATE = REPORT_SENT_DATE + timedelta(days=TWELVE_WEEKS_IN_DAYS)
TODAY = date.today()
case_fields_to_export_str = ",".join(get_field_names_for_export(Case))


def test_case_detail_view_leaves_out_archived_contact(admin_client):
    """Test that archived Contacts are not included in context"""
    case: Case = Case.objects.create()
    unarchived_contact: Contact = Contact.objects.create(
        case=case,
        first_name="Unarchived",
        last_name="Contact",
    )
    Contact.objects.create(
        case=case,
        first_name="Archived",
        last_name="Contact",
        is_archived=True,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assert set(response.context["contacts"]) == set([unarchived_contact])
    assertContains(response, "Unarchived Contact")
    assertNotContains(response, "Archived Contact")


def test_case_list_view_leaves_out_archived_case(admin_client):
    """Test that the case list view page does not include archived cases"""
    Case.objects.create(organisation_name="Not Archived")
    Case.objects.create(organisation_name="Is Archived", is_archived=True)

    response: HttpResponse = admin_client.get(reverse("cases:case-list"))

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Not Archived")
    assertNotContains(response, "Is Archived")


def test_case_list_view_filters_by_case_number(admin_client):
    """Test that the case list view page can be filtered by case number"""
    included_case: Case = Case.objects.create(organisation_name="Included")
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?search={included_case.id}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,value,url_parameter_name",
    [
        ("home_page_url", "included.com", "search"),
        ("organisation_name", "IncludedOrg", "search"),
    ],
)
def test_case_list_view_string_filters(
    field_name, value, url_parameter_name, admin_client
):
    """Test that the case list view page can be filtered by string"""
    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(included_case, field_name, value)
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}={value}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,url_parameter_name",
    [
        ("auditor", "auditor"),
        ("reviewer", "reviewer"),
    ],
)
def test_case_list_view_user_filters(field_name, url_parameter_name, admin_client):
    """Test that the case list view page can be filtered by user"""
    user = User.objects.create()
    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(included_case, field_name, user)
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}={user.id}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,url_parameter_name",
    [
        ("auditor", "auditor"),
        ("reviewer", "reviewer"),
    ],
)
def test_case_list_view_user_unassigned_filters(
    field_name, url_parameter_name, admin_client
):
    """Test that the case list view page can be filtered by unassigned user values"""
    Case.objects.create(organisation_name="Included")

    user = User.objects.create()
    excluded_case: Case = Case.objects.create(organisation_name="Excluded")
    setattr(excluded_case, field_name, user)
    excluded_case.save()

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}=none"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_date_range_filters(admin_client):
    """Test that the case list view page can be filtered by date range"""
    included_created_date: datetime = datetime(
        year=2021, month=6, day=5, tzinfo=pytz.UTC
    )
    excluded_created_date: datetime = datetime(
        year=2021, month=5, day=5, tzinfo=pytz.UTC
    )
    Case.objects.create(organisation_name="Included", created=included_created_date)
    Case.objects.create(organisation_name="Excluded", created=excluded_created_date)

    url_parameters = "start_date_0=1&start_date_1=6&start_date_2=2021&end_date_0=10&end_date_1=6&end_date_2=2021"
    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameters}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_export_list_view(admin_client):
    """Test that the case export list view returns csv data"""
    response: HttpResponse = admin_client.get(reverse("cases:case-export-list"))

    assert response.status_code == 200
    assertContains(response, case_fields_to_export_str)


def test_case_export_single_view(admin_client):
    """Test that the case export single view returns csv data"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-export-single", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, case_fields_to_export_str)


def test_archive_case_view(admin_client):
    """Test that archive case view archives case"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:archive-case", kwargs={"pk": case.id})
    )

    assert response.status_code == 302
    assert response.url == reverse("cases:case-list")

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.is_archived


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("cases:case-list", '<h1 class="govuk-heading-xl">Cases and reports</h1>'),
        ("cases:case-export-list", case_fields_to_export_str),
        ("cases:case-create", '<h1 class="govuk-heading-xl">Create case</h1>'),
    ],
)
def test_non_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the non-case-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("cases:case-export-single", case_fields_to_export_str),
        (
            "cases:case-detail",
            '<h1 class="govuk-heading-xl" style="margin-bottom:15px">View case</h1>',
        ),
        ("cases:edit-case-details", "<li>Case details</li>"),
        ("cases:edit-contact-details", "<li>Contact details</li>"),
        ("cases:edit-test-results", "<li>Testing details</li>"),
        ("cases:edit-report-details", "<li>Report details</li>"),
        ("cases:edit-report-correspondence", "<li>Report correspondence</li>"),
    ],
)
def test_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the case-specific view page loads"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "button_name, expected_redirect_url",
    [
        ("save_continue_case", reverse("cases:edit-case-details", kwargs={"pk": 1})),
        ("save_new_case", reverse("cases:case-create")),
        ("save_exit", reverse("cases:case-list")),
    ],
)
def test_create_case_redirects_based_on_button_pressed(
    button_name, expected_redirect_url, admin_client
):
    """Test that a successful case create redirects based on the button pressed"""
    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


@pytest.mark.django_db
def test_create_case_shows_duplicate_cases(admin_client):
    """Test that create case shows duplicates found"""
    domain_case: Case = Case.objects.create(home_page_url=HOME_PAGE_URL)
    organisation_name_case: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "organisation_name": ORGANISATION_NAME,
        },
    )

    assert response.status_code == 200
    assertContains(response, f" | #{domain_case.id}")
    assertContains(response, f" | #{organisation_name_case.id}")


@pytest.mark.parametrize(
    "button_name, expected_redirect_url",
    [
        ("save_continue_case", reverse("cases:edit-case-details", kwargs={"pk": 3})),
        ("save_new_case", reverse("cases:case-create")),
        ("save_exit", reverse("cases:case-list")),
    ],
)
@pytest.mark.django_db
def test_create_case_can_create_duplicate_cases(
    button_name, expected_redirect_url, admin_client
):
    """Test that create case can create duplicate cases"""
    Case.objects.create(home_page_url=HOME_PAGE_URL)
    Case.objects.create(organisation_name=ORGANISATION_NAME)

    response: HttpResponse = admin_client.post(
        f"{reverse('cases:case-create')}?allow_duplicate_cases=True",
        {
            "home_page_url": HOME_PAGE_URL,
            "organisation_name": ORGANISATION_NAME,
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        ("cases:edit-case-details", "save_continue", "cases:edit-contact-details"),
        ("cases:edit-case-details", "save_exit", "cases:case-detail"),
        ("cases:edit-contact-details", "save_continue", "cases:edit-test-results"),
        ("cases:edit-contact-details", "save_exit", "cases:case-detail"),
        ("cases:edit-test-results", "save_continue", "cases:edit-report-details"),
        ("cases:edit-test-results", "save_exit", "cases:case-detail"),
        (
            "cases:edit-report-details",
            "save_continue",
            "cases:edit-report-correspondence",
        ),
        ("cases:edit-report-details", "save_exit", "cases:case-detail"),
        ("cases:edit-report-correspondence", "save_exit", "cases:case-detail"),
        (
            "cases:edit-report-correspondence",
            "save_continue",
            "cases:edit-12-week-correspondence",
        ),
        (
            "cases:edit-report-followup-due-dates",
            "save_return",
            "cases:edit-report-correspondence",
        ),
        ("cases:edit-12-week-correspondence", "save_exit", "cases:case-detail"),
        (
            "cases:edit-12-week-correspondence",
            "save_continue",
            "cases:edit-final-decision",
        ),
        (
            "cases:edit-12-week-correspondence-due-dates",
            "save_return",
            "cases:edit-12-week-correspondence",
        ),
        ("cases:edit-no-psb-response", "save_exit", "cases:case-detail"),
        (
            "cases:edit-no-psb-response",
            "save_continue",
            "cases:edit-enforcement-body-correspondence",
        ),
        ("cases:edit-final-decision", "save_exit", "cases:case-detail"),
        (
            "cases:edit-final-decision",
            "save_continue",
            "cases:edit-enforcement-body-correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "save_exit",
            "cases:case-detail",
        ),
    ],
)
def test_case_edit_redirects_based_on_button_pressed(
    case_edit_path, button_name, expected_redirect_path, admin_client
):
    """Test that a successful case update redirects based on the button pressed"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "home_page_url": HOME_PAGE_URL,
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse(expected_redirect_path, kwargs={"pk": case.id})


def test_add_contact_form_appears(admin_client):
    """Test that pressing the add contact button adds a new contact form"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "add_contact": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Contact 1")


def test_add_contact(admin_client):
    """Test adding a contact"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "",
            "form-0-first_name": "",
            "form-0-last_name": "",
            "form-0-job_title": "",
            "form-0-detail": CONTACT_DETAIL,
            "form-0-notes": "",
            "save_continue": "Save and continue",
        },
        follow=True,
    )
    assert response.status_code == 200

    contacts: QuerySet[Contact] = Contact.objects.filter(case=case)
    assert contacts.count() == 1
    assert list(contacts)[0].detail == CONTACT_DETAIL


def test_archive_contact(admin_client):
    """Test that pressing the remove contact button archives the contact"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            f"remove_contact_{contact.id}": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "No contacts have been entered")

    contact_on_database = Contact.objects.get(pk=contact.id)
    assert contact_on_database.is_archived is True


def test_preferred_contact_not_displayed_on_form(admin_client):
    """
    Test that the preferred contact field is not displayed when there is only one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertNotContains(response, "Preferred contact?")


def test_preferred_contact_displayed_on_form(admin_client):
    """
    Test that the preferred contact field is displayed when there is more than one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "Preferred contact?")


def test_updating_report_sent_date(admin_client):
    """Test that populating the report sent date populates the report followup due dates"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-details", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date == ONE_WEEK_FOLLOWUP_DUE_DATE
    assert case_from_db.report_followup_week_4_due_date == FOUR_WEEK_FOLLOWUP_DUE_DATE
    assert (
        case_from_db.report_followup_week_12_due_date == TWELVE_WEEK_FOLLOWUP_DUE_DATE
    )


def test_report_followup_due_dates_not_changed(admin_client):
    """
    Test that populating the report sent date does not update existing report followup due dates
    """
    case: Case = Case.objects.create(
        report_followup_week_1_due_date=OTHER_DATE,
        report_followup_week_4_due_date=OTHER_DATE,
        report_followup_week_12_due_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-details", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date == OTHER_DATE
    assert case_from_db.report_followup_week_4_due_date == OTHER_DATE
    assert case_from_db.report_followup_week_12_due_date == OTHER_DATE


def test_report_followup_due_dates_not_changed_if_repot_sent_date_already_set(
    admin_client,
):
    """
    Test that updating the report sent date does not populate report followup due dates
    """
    case: Case = Case.objects.create(report_sent_date=OTHER_DATE)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-details", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date is None
    assert case_from_db.report_followup_week_4_due_date is None
    assert case_from_db.report_followup_week_12_due_date is None


def test_case_report_correspondence_view_contains_followup_due_dates(admin_client):
    """Test that the case report correspondence view contains the followup due dates"""
    case: Case = Case.objects.create(
        report_followup_week_1_due_date=ONE_WEEK_FOLLOWUP_DUE_DATE,
        report_followup_week_4_due_date=FOUR_WEEK_FOLLOWUP_DUE_DATE,
        report_followup_week_12_due_date=TWELVE_WEEK_FOLLOWUP_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        f'<div id="event-name-hint" class="govuk-hint">{format_date(ONE_WEEK_FOLLOWUP_DUE_DATE)}</div>',
    )
    assertContains(
        response,
        f'<div id="event-name-hint" class="govuk-hint">{format_date(FOUR_WEEK_FOLLOWUP_DUE_DATE)}</div>',
    )
    assertContains(
        response,
        f'<div id="event-name-hint" class="govuk-hint">{format_date(TWELVE_WEEK_FOLLOWUP_DUE_DATE)}</div>',
    )


def test_setting_report_followup_populates_sent_dates(admin_client):
    """Test that ticking the report followup checkboxes populates the report followup sent dates"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_followup_week_1_sent_date": "on",
            "report_followup_week_4_sent_date": "on",
            "report_followup_week_12_sent_date": "on",
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date == TODAY
    assert case_from_db.report_followup_week_4_sent_date == TODAY
    assert case_from_db.report_followup_week_12_sent_date == TODAY


def test_setting_report_followup_doesn_not_update_sent_dates(admin_client):
    """Test that ticking the report followup checkboxes does not update the report followup sent dates"""
    case: Case = Case.objects.create(
        report_followup_week_1_sent_date=OTHER_DATE,
        report_followup_week_4_sent_date=OTHER_DATE,
        report_followup_week_12_sent_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_followup_week_1_sent_date": "on",
            "report_followup_week_4_sent_date": "on",
            "report_followup_week_12_sent_date": "on",
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date == OTHER_DATE
    assert case_from_db.report_followup_week_4_sent_date == OTHER_DATE
    assert case_from_db.report_followup_week_12_sent_date == OTHER_DATE


def test_unsetting_report_followup_sent_dates(admin_client):
    """Test that not ticking the report followup checkboxes clears the report followup sent dates"""
    case: Case = Case.objects.create(
        report_followup_week_1_sent_date=OTHER_DATE,
        report_followup_week_4_sent_date=OTHER_DATE,
        report_followup_week_12_sent_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date is None
    assert case_from_db.report_followup_week_4_sent_date is None
    assert case_from_db.report_followup_week_12_sent_date is None


@pytest.mark.parametrize(
    "url, domain, expected_number_of_duplicates",
    [
        (HOME_PAGE_URL, ORGANISATION_NAME, 2),
        (HOME_PAGE_URL, "", 1),
        ("https://domain2.com", "Org name", 0),
        ("https://domain2.com", "", 0),
    ],
)
@pytest.mark.django_db
def test_find_duplicate_cases(url, domain, expected_number_of_duplicates):
    """Test find_duplicate_cases returns matching cases"""
    domain_case: Case = Case.objects.create(home_page_url=HOME_PAGE_URL)
    organisation_name_case: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    duplicate_cases: List[Case] = list(find_duplicate_cases(url, domain))

    assert len(duplicate_cases) == expected_number_of_duplicates

    if expected_number_of_duplicates > 0:
        assert duplicate_cases[0] == domain_case

    if expected_number_of_duplicates > 1:
        assert duplicate_cases[1] == organisation_name_case


def test_preferred_contact_not_displayed(admin_client):
    """
    Test that the preferred contact is not displayed when there is only one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertNotContains(response, "Preferred contact")


def test_preferred_contact_displayed(admin_client):
    """
    Test that the preferred contact is displayed when there is more than one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "Preferred contact")


@pytest.mark.parametrize(
    "flag_name, section_name",
    [
        ("is_case_details_complete", "Case details"),
        ("is_contact_details_complete", "Contact details"),
        ("is_testing_details_complete", "Testing details"),
        ("is_reporting_details_complete", "Report details"),
        ("is_report_correspondence_complete", "Report correspondence"),
        ("is_12_week_correspondence_complete", "12 week correspondence"),
        ("is_final_decision_complete", "Final decision"),
        ("is_enforcement_correspondence_complete", "Equality bodies correspondence"),
    ],
)
def test_section_complete_check_displayed_in_contents(flag_name, section_name, admin_client):
    """
    Test that the section complete tick is displayed in contents
    """
    case: Case = Case.objects.create()
    setattr(case, flag_name, True)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, f'<a href="#{slugify(section_name)}" class="govuk-link govuk-link--no-visited-state">{section_name}</a> &check;', html=True)


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        ("cases:edit-case-details", "is_case_details_complete", "Case details"),
        ("cases:edit-contact-details", "is_contact_details_complete", "Contact details"),
        ("cases:edit-test-results", "is_testing_details_complete", "Testing details"),
        ("cases:edit-report-details", "is_reporting_details_complete", "Report details"),
        ("cases:edit-report-correspondence", "is_report_correspondence_complete", "Report correspondence"),
        ("cases:edit-12-week-correspondence", "is_12_week_correspondence_complete", "12 week correspondence"),
        ("cases:edit-final-decision", "is_final_decision_complete", "Final decision"),
        ("cases:edit-enforcement-body-correspondence", "is_enforcement_correspondence_complete", "Equality body correspondence"),
    ],
)
def test_section_complete_check_displayed_in_steps(step_url, flag_name, step_name, admin_client):
    """
    Test that the section complete tick is displayed in list of steps
    """
    case: Case = Case.objects.create()
    setattr(case, flag_name, True)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, f"{step_name} &check;", html=True)
