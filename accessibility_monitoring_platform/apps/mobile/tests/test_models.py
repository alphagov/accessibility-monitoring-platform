"""Tests for mobile models"""

from datetime import date

import pytest
from django.contrib.auth.models import User

from ...common.models import Boolean
from ...simplified.models import SimplifiedCase
from ..models import MobileCase, MobileCaseHistory, MobileContact, MobileZendeskTicket

ORGANISATION_NAME: str = "Organisation Name"
WEBSITE_NAME: str = "Website Name"
EXPECTED_FORMATTED_CONTACTS: str = """Name 2
Job title 2
email2
Information 2

Name 1
Job title 1
email1
Information 1
"""


@pytest.mark.django_db
def test_mobile_case_str():
    """Test MobileCase.__str__()"""
    mobile_case: MobileCase = MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    assert str(mobile_case) == "Organisation Name | #M-1"


@pytest.mark.django_db
def test_mobile_case_title():
    """Test MobileCase.title"""
    mobile_case: MobileCase = MobileCase.objects.create(app_name="App name")

    assert mobile_case.title == "App name &nbsp;|&nbsp; #M-1"


@pytest.mark.django_db
def test_mobile_case_identifier():
    """Test MobileCase.case_identifier"""
    mobile_case: MobileCase = MobileCase.objects.create()

    assert mobile_case.case_identifier == "#M-1"


@pytest.mark.django_db
def test_mobile_case_status_history():
    """Test MobileCase.status_history returns only relevant events"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    mobile_case_history_status: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.STATUS,
        created_by=user,
    )
    mobile_case_history_note: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        created_by=user,
    )

    assert mobile_case_history_status in mobile_case.status_history()
    assert mobile_case_history_note not in mobile_case.status_history()


@pytest.mark.django_db
def test_mobile_case_notes_history():
    """Test MobileCase.notes_history returns only relevant events"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    mobile_case_history_status: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.STATUS,
        created_by=user,
    )
    mobile_case_history_note: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        created_by=user,
    )

    assert mobile_case_history_status not in mobile_case.notes_history()
    assert mobile_case_history_note in mobile_case.notes_history()


@pytest.mark.django_db
def test_mobile_case_most_recent_history():
    """Test MobileCase.most_recent_history returns the most recent event"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        created_by=user,
    )
    mobile_case_history_last: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        created_by=user,
    )

    assert mobile_case.most_recent_history == mobile_case_history_last


@pytest.mark.django_db
def test_mobile_case_contacts():
    """Test MobileCase.contacts returns the contacts"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    contact: MobileContact = MobileContact.objects.create(
        mobile_case=mobile_case, created_by=user
    )

    assert list(mobile_case.contacts) == [contact]


@pytest.mark.django_db
def test_mobile_case_preferred_contacts():
    """Test MobileCase.preferred_contacts returns the preferred contacts"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileContact.objects.create(mobile_case=mobile_case, created_by=user)
    preferred_contact: MobileContact = MobileContact.objects.create(
        mobile_case=mobile_case, created_by=user, preferred=MobileContact.Preferred.YES
    )

    assert list(mobile_case.preferred_contacts) == [preferred_contact]


@pytest.mark.django_db
def test_mobile_case_history_saves_mobile_case_status():
    """Test MobileCaseiHistory saves the current MobileCase status"""
    mobile_case: MobileCase = MobileCase.objects.create(
        status=MobileCase.Status.REVIEWING_CHANGES
    )
    user: User = User.objects.create()
    mobile_case_history: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        created_by=user,
    )

    assert mobile_case_history.mobile_case_status == MobileCase.Status.REVIEWING_CHANGES


def test_contact_str():
    """Test MobileContact.__str__()"""
    contact: MobileContact = MobileContact(
        name="MobileContact Name", contact_details="name@example.com"
    )

    assert str(contact) == "MobileContact Name name@example.com"


@pytest.mark.django_db
def test_zendesk_id_within_case():
    """
    Test that MobileZendeskTicket.id_within_case is set to number of Zendesk tickets in case
    or id from Zendesk URL
    """
    mobile_case: MobileCase = MobileCase.objects.create()
    zendesk_ticket: MobileZendeskTicket = MobileZendeskTicket.objects.create(
        mobile_case=mobile_case, url="https://non-zendesk-url"
    )

    assert zendesk_ticket.id_within_case == 1

    zendesk_ticket.url = "https://govuk.zendesk.com/agent/tickets/1234567"
    zendesk_ticket.save()

    assert zendesk_ticket.id_within_case == 1234567


@pytest.mark.parametrize(
    "previous_case_url, previous_case_identifier",
    [
        ("https://...gov.uk/simplified/1/view/", "#S-1"),
        ("https://...gov.uk/mobile/1/case-detail/", "#M-1"),
        ("", None),
        ("https://...gov.uk/audit/191/view/", None),
    ],
)
@pytest.mark.django_db
def test_previous_case_identifier(previous_case_url, previous_case_identifier):
    """Test previous case identifier derived from url"""
    if "mobile" in previous_case_url:
        MobileCase.objects.create()
    else:
        SimplifiedCase.objects.create()

    mobile_case: MobileCase = MobileCase.objects.create(
        previous_case_url=previous_case_url
    )

    assert mobile_case.previous_case_identifier == previous_case_identifier


@pytest.mark.django_db
def test_mobile_case_equality_body_export_contact_details():
    """Test that contacts fields values are contatenated"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileContact.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        name="Name 1",
        job_title="Job title 1",
        contact_details="email1",
        information="Information 1",
    ),
    MobileContact.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        name="Name 2",
        job_title="Job title 2",
        contact_details="email2",
        information="Information 2",
    ),

    assert (
        mobile_case.equality_body_export_contact_details == EXPECTED_FORMATTED_CONTACTS
    )


def test_mobile_case_report_acknowledged_yes_no():
    """Test the MobileCase.report_acknowledged_yes_no"""

    assert MobileCase().report_acknowledged_yes_no == "No"
    assert (
        MobileCase(report_acknowledged_date=date(2020, 1, 1)).report_acknowledged_yes_no
        == "Yes"
    )
    assert (
        MobileCase(
            report_acknowledged_date=date(2020, 1, 1),
            no_psb_contact=Boolean.YES,
        ).report_acknowledged_yes_no
        == "No"
    )


def test_mobile_case_number_of_issues_fixed():
    """Test the MobileCase.number_of_issues_fixed"""

    assert MobileCase().number_of_issues_fixed == 0
    assert (
        MobileCase(
            initial_ios_total_number_of_issues=40,
            initial_android_total_number_of_issues=10,
        ).number_of_issues_fixed
        == 50
    )
    assert (
        MobileCase(
            initial_ios_total_number_of_issues=40,
            initial_android_total_number_of_issues=10,
            retest_ios_total_number_of_issues=20,
            retest_android_total_number_of_issues=0,
        ).number_of_issues_fixed
        == 30
    )
    assert (
        MobileCase(
            initial_ios_total_number_of_issues=40,
            initial_android_total_number_of_issues=10,
            retest_ios_total_number_of_issues=20,
            retest_android_total_number_of_issues=40,
        ).number_of_issues_fixed
        == -10
    )


def test_mobile_case_percentage_of_issues_fixed():
    """Test the MobileCase.percentage_of_issues_fixed"""

    assert MobileCase().percentage_of_issues_fixed == 0
    assert (
        MobileCase(initial_ios_total_number_of_issues=50).percentage_of_issues_fixed
        == 100
    )
    assert (
        MobileCase(
            initial_ios_total_number_of_issues=50,
            retest_ios_total_number_of_issues=20,
            initial_android_total_number_of_issues=50,
            retest_android_total_number_of_issues=20,
        ).percentage_of_issues_fixed
        == 60
    )
    assert (
        MobileCase(
            initial_ios_total_number_of_issues=50,
            retest_ios_total_number_of_issues=60,
            initial_android_total_number_of_issues=50,
            retest_android_total_number_of_issues=60,
        ).percentage_of_issues_fixed
        == -20
    )


def test_mobile_case_equality_body_export_statement_found_at_retest():
    """Test the MobileCase.equality_body_export_statement_found_at_retest"""

    assert (
        MobileCase().equality_body_export_statement_found_at_retest
        == "iOS: No\n\nAndroid: No"
    )
    assert (
        MobileCase(
            retest_ios_statement_compliance_state=MobileCase.StatementCompliance.COMPLIANT,
            retest_android_statement_compliance_state=MobileCase.StatementCompliance.COMPLIANT,
        ).equality_body_export_statement_found_at_retest
        == "iOS: Yes\n\nAndroid: Yes"
    )
    assert (
        MobileCase(
            retest_ios_statement_compliance_state=MobileCase.StatementCompliance.NOT_COMPLIANT,
            retest_android_statement_compliance_state=MobileCase.StatementCompliance.NOT_COMPLIANT,
        ).equality_body_export_statement_found_at_retest
        == "iOS: Yes\n\nAndroid: Yes"
    )
    assert (
        MobileCase(
            retest_ios_statement_compliance_state=MobileCase.StatementCompliance.NO_STATEMENT,
            retest_android_statement_compliance_state=MobileCase.StatementCompliance.NO_STATEMENT,
        ).equality_body_export_statement_found_at_retest
        == "iOS: No\n\nAndroid: No"
    )
    assert (
        MobileCase(
            retest_ios_statement_compliance_state=MobileCase.StatementCompliance.UNKNOWN,
            retest_android_statement_compliance_state=MobileCase.StatementCompliance.UNKNOWN,
        ).equality_body_export_statement_found_at_retest
        == "iOS: No\n\nAndroid: No"
    )


@pytest.mark.parametrize(
    "equality_body_report_url_ios, equality_body_report_url_android, expected_equality_body_report_urls",
    [
        ("", "", "iOS: n/a\n\nAndroid: n/a"),
        ("https://domain.com/ios", "", "iOS: https://domain.com/ios\n\nAndroid: n/a"),
        (
            "",
            "https://domain.com/android",
            "iOS: n/a\n\nAndroid: https://domain.com/android",
        ),
        (
            "https://domain.com/ios",
            "https://domain.com/android",
            "iOS: https://domain.com/ios\n\nAndroid: https://domain.com/android",
        ),
    ],
)
@pytest.mark.django_db
def test_equality_body_report_urls(
    equality_body_report_url_ios,
    equality_body_report_url_android,
    expected_equality_body_report_urls,
):
    """Test equality_body_report_urls returned for use in equality body export"""
    mobile_case: MobileCase = MobileCase.objects.create(
        equality_body_report_url_ios=equality_body_report_url_ios,
        equality_body_report_url_android=equality_body_report_url_android,
    )

    assert mobile_case.equality_body_report_urls == expected_equality_body_report_urls
