"""
Tests for cases views
"""
from datetime import date, datetime, timedelta
import pytest
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from pytest_django.asserts import assertContains, assertNotContains

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse

from ...notifications.models import Notification
from ...s3_read_write.models import S3Report
from ...audits.models import Audit, Page, PAGE_TYPE_STATEMENT, PAGE_TYPE_CONTACT
from ...audits.tests.test_models import create_audit_and_check_results
from ...comments.models import Comment
from ...common.models import (
    BOOLEAN_TRUE,
    Event,
    Sector,
    EVENT_TYPE_MODEL_CREATE,
    EVENT_TYPE_MODEL_UPDATE,
)
from ...common.utils import amp_format_date
from ...reports.models import Report

from ..models import (
    REPORT_METHODOLOGY_ODT,
    REPORT_METHODOLOGY_PLATFORM,
    TESTING_METHODOLOGY_SPREADSHEET,
    Case,
    CaseEvent,
    Contact,
    REPORT_APPROVED_STATUS_APPROVED,
    IS_WEBSITE_COMPLIANT_COMPLIANT,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    REPORT_READY_TO_REVIEW,
    CASE_COMPLETED_SEND,
    ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
    ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
    CASE_EVENT_TYPE_CREATE,
    CASE_EVENT_CASE_COMPLETED,
    CASE_COMPLETED_NO_SEND,
)
from ..utils import (
    FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    COLUMNS_FOR_EQUALITY_BODY,
    EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY,
    CASE_COLUMNS_FOR_EXPORT,
    CONTACT_COLUMNS_FOR_EXPORT,
)
from ..views import (
    ONE_WEEK_IN_DAYS,
    FOUR_WEEKS_IN_DAYS,
    TWELVE_WEEKS_IN_DAYS,
    find_duplicate_cases,
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
    format_due_date_help_text,
    CaseQAProcessUpdateView,
)

CONTACT_EMAIL: str = "test@email.com"
DOMAIN: str = "domain.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}"
ORGANISATION_NAME: str = "Organisation name"
REPORT_SENT_DATE: date = date(2021, 2, 28)
OTHER_DATE: date = date(2020, 12, 31)
ONE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
FOUR_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=FOUR_WEEKS_IN_DAYS
)
TWELVE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=TWELVE_WEEKS_IN_DAYS
)
DEACTIVATE_NOTES: str = """I am
a deactivate note,
I am"""
COMPLIANCE_DECISION_NOTES: str = "Compliant decision note"
ACCESSIBILITY_STATEMENT_NOTES: str = "Accessibility Statement note"
TODAY: date = date.today()
DRAFT_REPORT_URL: str = "https://draft-report-url.com"
case_feedback_survey_columns_to_export_str: str = ",".join(
    column.column_name
    for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
)
case_equality_body_columns_to_export_str: str = ",".join(
    column.column_name
    for column in COLUMNS_FOR_EQUALITY_BODY + EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY
)
case_columns_to_export_str: str = ",".join(
    column.column_name
    for column in CASE_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
)
ACCESSIBILITY_STATEMENT_URL: str = "https://example.com/accessibility-statement"
CONTACT_STATEMENT_URL: str = "https://example.com/contact"
TODAY: date = date.today()
QA_COMMENT_BODY: str = "QA comment body"


def add_user_to_auditor_groups(user: User) -> None:
    auditor_group: Group = Group.objects.create(name="Auditor")
    historic_auditor_group: Group = Group.objects.create(name="Historic auditor")
    qa_auditor_group: Group = Group.objects.create(name="QA auditor")
    auditor_group.user_set.add(user)
    historic_auditor_group.user_set.add(user)
    qa_auditor_group.user_set.add(user)


def test_case_detail_view_leaves_out_deleted_contact(admin_client):
    """Test that deleted Contacts are not included in context"""
    case: Case = Case.objects.create()
    undeleted_contact: Contact = Contact.objects.create(
        case=case,
        name="Undeleted Contact",
    )
    Contact.objects.create(
        case=case,
        name="Deleted Contact",
        is_deleted=True,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assert set(response.context["contacts"]) == set([undeleted_contact])
    assertContains(response, "Undeleted Contact")
    assertNotContains(response, "Deleted Contact")


def test_case_list_view_filters_by_unassigned_qa_case(admin_client):
    """Test that Cases where Report is ready to QA can be filtered by status"""
    Case.objects.create(organisation_name="Excluded")
    Case.objects.create(
        organisation_name="Included", report_review_status="ready-to-review"
    )

    response: HttpResponse = admin_client.get(
        f'{reverse("cases:case-list")}?status=unassigned-qa-case'
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_filters_by_case_number(admin_client):
    """Test that the case list view page can be filtered by case number"""
    included_case: Case = Case.objects.create(organisation_name="Included")
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?search={included_case.id}"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_filters_by_psb_location(admin_client):
    """Test that the case list view page can be filtered by case number"""
    Case.objects.create(organisation_name="Included", psb_location="scotland")
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?search=scot"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_filters_by_sector_name(admin_client):
    """Test that the case list view page can be filtered by sector name"""
    sector: Sector = Sector.objects.create(name="Defence")
    Case.objects.create(organisation_name="Included", sector=sector)
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?search=fence"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,value,url_parameter_name",
    [
        ("home_page_url", "included.com", "case_search"),
        ("organisation_name", "IncludedOrg", "case_search"),
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
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
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
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)

    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(included_case, field_name, user)
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}={user.id}"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
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
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_date_range_filters(admin_client):
    """Test that the case list view page can be filtered by date range"""
    included_sent_to_enforcement_body_sent_date: datetime = datetime(
        year=2021, month=6, day=5, tzinfo=ZoneInfo("UTC")
    )
    excluded_sent_to_enforcement_body_sent_date: datetime = datetime(
        year=2021, month=5, day=5, tzinfo=ZoneInfo("UTC")
    )
    Case.objects.create(
        organisation_name="Included",
        sent_to_enforcement_body_sent_date=included_sent_to_enforcement_body_sent_date,
    )
    Case.objects.create(
        organisation_name="Excluded",
        sent_to_enforcement_body_sent_date=excluded_sent_to_enforcement_body_sent_date,
    )

    url_parameters = "date_start_0=1&date_start_1=6&date_start_2=2021&date_end_0=10&date_end_1=6&date_end_2=2021"
    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameters}"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_sector_filter(admin_client):
    """Test that the case list view page can be filtered by sector"""
    sector: Sector = Sector.objects.create(name="test sector")

    included_case: Case = Case.objects.create(organisation_name="Included")
    included_case.sector = sector
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?sector={sector.id}"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_feedback_survey_export_list_view(admin_client):
    """Test that the case feedback survey export list view returns csv data"""
    response: HttpResponse = admin_client.get(
        reverse("cases:export-feedback-survey-cases")
    )

    assert response.status_code == 200
    assertContains(response, case_feedback_survey_columns_to_export_str)


def test_case_equality_body_export_list_view(admin_client):
    """Test that the case equality body export list view returns csv data"""
    response: HttpResponse = admin_client.get(
        reverse("cases:export-equality-body-cases")
    )

    assert response.status_code == 200
    assertContains(response, case_equality_body_columns_to_export_str)


def test_case_export_list_view(admin_client):
    """Test that the case export list view returns csv data"""
    response: HttpResponse = admin_client.get(reverse("cases:case-export-list"))

    assert response.status_code == 200
    assertContains(response, case_columns_to_export_str)


@pytest.mark.parametrize(
    "export_view_name",
    [
        "cases:export-equality-body-cases",
        "cases:case-export-list",
        "cases:export-feedback-survey-cases",
    ],
)
def test_case_export_view_filters_by_search(export_view_name, admin_client):
    """
    Test that the case exports can be filtered by search from top menu
    """
    included_case: Case = Case.objects.create(organisation_name="Included")
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse(export_view_name)}?search={included_case.id}"
    )

    assert response.status_code == 200
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_export_list_view_respects_filters(admin_client):
    """Test that the case export list view includes only filtered data"""
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)
    Case.objects.create(organisation_name="Included", auditor=user)
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-export-list')}?auditor={user.id}"
    )

    assert response.status_code == 200
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_export_single_view(admin_client):
    """Test that the case export single view returns csv data"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-export-single", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, case_columns_to_export_str)


def test_deactivate_case_view(admin_client):
    """Test that deactivate case view deactivates the case"""
    case: Case = Case.objects.create()
    case_pk: Dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.post(
        reverse("cases:deactivate-case", kwargs=case_pk),
        {
            "version": case.version,
            "deactivate_notes": DEACTIVATE_NOTES,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("cases:case-detail", kwargs=case_pk)

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.is_deactivated
    assert case_from_db.deactivate_date == TODAY
    assert case_from_db.deactivate_notes == DEACTIVATE_NOTES


def test_reactivate_case_view(admin_client):
    """Test that reactivate case view reactivates the case"""
    case: Case = Case.objects.create()
    case_pk: Dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.post(
        reverse("cases:reactivate-case", kwargs=case_pk),
        {
            "version": case.version,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("cases:case-detail", kwargs=case_pk)

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert not case_from_db.is_deactivated


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("cases:case-list", '<h1 class="govuk-heading-xl">Search</h1>'),
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
        (
            "cases:case-detail",
            '<h1 class="govuk-heading-xl amp-margin-bottom-15 amp-padding-right-20">View case</h1>',
        ),
        ("cases:edit-case-details", "<li>Case details</li>"),
        ("cases:edit-test-results", "<li>Testing details</li>"),
        ("cases:edit-report-details", "<li>Report details</li>"),
        ("cases:edit-qa-process", "<li>QA process</li>"),
        ("cases:edit-contact-details", "<li>Contact details</li>"),
        ("cases:edit-report-correspondence", "<li>Report correspondence</li>"),
        (
            "cases:outstanding-issues",
            '<h1 class="govuk-heading-xl amp-margin-bottom-15">Outstanding issues</h1>',
        ),
    ],
)
def test_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the case-specific view page loads"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, expected_content, html=True)


def test_create_case_shows_error_messages(admin_client):
    """
    Test that the create case page shows the expected error messages
    """
    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": "gov.uk",
            "save_exit": "Save and exit",
        },
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<p class="govuk-error-message">
            <span class="govuk-visually-hidden">Error:</span>
            URL must start with http:// or https://
        </p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-error-message">
            <span class="govuk-visually-hidden">Error:</span>
            Choose which equalities body will check the case
        </p>""",
        html=True,
    )


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
            "enforcement_body": "ehrc",
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


@pytest.mark.django_db
def test_create_case_shows_duplicate_cases(admin_client):
    """Test that create case shows duplicates found"""
    other_url: str = "other_url"
    other_organisation_name: str = "other organisation name"
    Case.objects.create(
        home_page_url=HOME_PAGE_URL,
        organisation_name=other_organisation_name,
    )
    Case.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=other_url,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
        },
    )

    assert response.status_code == 200
    assertContains(response, other_url)
    assertContains(response, other_organisation_name)


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
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_redirect_url


def test_create_case_creates_case_event(admin_client):
    """Test that a successful case create also creates a case event"""
    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "save_exit": "Button value",
        },
    )

    assert response.status_code == 302

    case: Case = Case.objects.get(home_page_url=HOME_PAGE_URL)
    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_TYPE_CREATE
    assert case_event.message == "Created case"


def test_updating_case_creates_case_event(admin_client):
    """
    Test that updating a case (changing case completed) creates a case event
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-close", kwargs={"pk": case.id}),
        {
            "case_completed": CASE_COMPLETED_NO_SEND,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_CASE_COMPLETED
    assert (
        case_event.message
        == "Case completed changed from 'Case still in progress' to 'Case should not be sent to the equality body'"
    )


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        ("cases:edit-case-details", "save", "cases:edit-case-details"),
        ("cases:edit-case-details", "save_continue", "cases:edit-test-results"),
        ("cases:edit-test-results", "save", "cases:edit-test-results"),
        ("cases:edit-test-results", "save_continue", "cases:edit-report-details"),
        ("cases:edit-report-details", "save", "cases:edit-report-details"),
        ("cases:edit-report-details", "save_continue", "cases:edit-qa-process"),
        ("cases:edit-qa-process", "save", "cases:edit-qa-process"),
        ("cases:edit-qa-process", "save_continue", "cases:edit-contact-details"),
        ("cases:edit-contact-details", "save", "cases:edit-contact-details"),
        (
            "cases:edit-contact-details",
            "save_continue",
            "cases:edit-report-correspondence",
        ),
        (
            "cases:edit-report-correspondence",
            "save",
            "cases:edit-report-correspondence",
        ),
        (
            "cases:edit-report-correspondence",
            "save_continue",
            "cases:edit-twelve-week-correspondence",
        ),
        (
            "cases:edit-report-followup-due-dates",
            "save_return",
            "cases:edit-report-correspondence",
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "save",
            "cases:edit-twelve-week-correspondence",
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "save_continue",
            "cases:edit-twelve-week-retest",
        ),
        (
            "cases:edit-twelve-week-correspondence-due-dates",
            "save_return",
            "cases:edit-twelve-week-correspondence",
        ),
        (
            "cases:edit-no-psb-response",
            "save_continue",
            "cases:edit-twelve-week-correspondence",
        ),
        ("cases:edit-twelve-week-retest", "save", "cases:edit-twelve-week-retest"),
        (
            "cases:edit-twelve-week-retest",
            "save_continue",
            "cases:edit-review-changes",
        ),
        ("cases:edit-review-changes", "save", "cases:edit-review-changes"),
        (
            "cases:edit-review-changes",
            "save_continue",
            "cases:edit-case-close",
        ),
        ("cases:edit-case-close", "save", "cases:edit-case-close"),
        (
            "cases:edit-case-close",
            "save_continue",
            "cases:edit-enforcement-body-correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "save",
            "cases:edit-enforcement-body-correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "save_continue",
            "cases:edit-post-case",
        ),
        ("cases:edit-post-case", "save", "cases:edit-post-case"),
        (
            "cases:edit-post-case",
            "save_exit",
            "cases:case-detail",
        ),
    ],
)
def test_platform_case_edit_redirects_based_on_button_pressed(
    case_edit_path,
    button_name,
    expected_redirect_path,
    admin_client,
):
    """
    Test that a successful case update redirects based on the button pressed
    when the case testing methodology is platform
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "version": case.version,
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}'


def test_add_qa_comment(admin_client, admin_user):
    """Test adding a QA comment"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:add-qa-comment", kwargs={"case_id": case.id}),
        {
            "save_return": "Button value",
            "body": QA_COMMENT_BODY,
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(case=case)

    assert comment.body == QA_COMMENT_BODY
    assert comment.user == admin_user

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event: Event = Event.objects.get(content_type=content_type, object_id=comment.id)

    assert event.type == EVENT_TYPE_MODEL_CREATE


def test_add_qa_comment_redirects_to_qa_process(admin_client):
    """Test adding a QA comment redirects to QA process page"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:add-qa-comment", kwargs={"case_id": case.id}),
        {
            "save_return": "Button value",
        },
    )
    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse("cases:edit-qa-process", kwargs={"pk": case.id})}?discussion=open#qa-discussion'
    )


def test_add_contact_form_appears(admin_client):
    """Test that pressing the add contact button adds a new contact form"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": case.version,
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
            "form-0-name": "",
            "form-0-job_title": "",
            "form-0-email": CONTACT_EMAIL,
            "form-0-notes": "",
            "version": case.version,
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200

    contacts: QuerySet[Contact] = Contact.objects.filter(case=case)
    assert contacts.count() == 1
    assert list(contacts)[0].email == CONTACT_EMAIL


def test_delete_contact(admin_client):
    """Test that pressing the remove contact button deletes the contact"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": case.version,
            f"remove_contact_{contact.id}": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "No contacts have been entered")

    contact_on_database = Contact.objects.get(pk=contact.id)
    assert contact_on_database.is_deleted is True


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


def test_link_to_accessibility_statement_displayed(admin_client):
    """
    Test that the link to the accessibility statement is displayed.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        f"""<p class="govuk-body-m">
            <a href="{ACCESSIBILITY_STATEMENT_URL}" target="_blank" class="govuk-link">
                Open accessibility statement page
            </a>
        </p>""",
        html=True,
    )


def test_link_to_accessibility_statement_not_displayed(admin_client):
    """
    Test that the link to the accessibility statement is not displayed
    if none has been entered
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "No accessibility statement")


def test_updating_report_sent_date(admin_client):
    """Test that populating the report sent date populates the report followup due dates"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
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
    Test that populating the report sent date updates existing report followup due dates
    """
    case: Case = Case.objects.create(
        report_followup_week_1_due_date=OTHER_DATE,
        report_followup_week_4_due_date=OTHER_DATE,
        report_followup_week_12_due_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date != OTHER_DATE
    assert case_from_db.report_followup_week_4_due_date != OTHER_DATE
    assert case_from_db.report_followup_week_12_due_date != OTHER_DATE


def test_report_followup_due_dates_not_changed_if_repot_sent_date_already_set(
    admin_client,
):
    """
    Test that updating the report sent date populates report followup due dates
    """
    case: Case = Case.objects.create(report_sent_date=OTHER_DATE)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_sent_date_0": REPORT_SENT_DATE.day,
            "report_sent_date_1": REPORT_SENT_DATE.month,
            "report_sent_date_2": REPORT_SENT_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_due_date is not None
    assert case_from_db.report_followup_week_4_due_date is not None
    assert case_from_db.report_followup_week_12_due_date is not None


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
        f'<div class="govuk-hint">Due {amp_format_date(ONE_WEEK_FOLLOWUP_DUE_DATE)}</div>',
    )
    assertContains(
        response,
        f'<div class="govuk-hint">Due {amp_format_date(FOUR_WEEK_FOLLOWUP_DUE_DATE)}</div>',
    )
    assertContains(
        response,
        f'<span class="govuk-hint">Due {amp_format_date(TWELVE_WEEK_FOLLOWUP_DUE_DATE)}</span>',
        html=True,
    )


def test_setting_report_followup_populates_sent_dates(admin_client):
    """Test that ticking the report followup checkboxes populates the report followup sent dates"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_followup_week_1_sent_date": "on",
            "report_followup_week_4_sent_date": "on",
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date == TODAY
    assert case_from_db.report_followup_week_4_sent_date == TODAY


def test_setting_report_followup_does_not_update_sent_dates(admin_client):
    """Test that ticking the report followup checkboxes does not update the report followup sent dates"""
    case: Case = Case.objects.create(
        report_followup_week_1_sent_date=OTHER_DATE,
        report_followup_week_4_sent_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "report_followup_week_1_sent_date": "on",
            "report_followup_week_4_sent_date": "on",
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date == OTHER_DATE
    assert case_from_db.report_followup_week_4_sent_date == OTHER_DATE


def test_unsetting_report_followup_sent_dates(admin_client):
    """Test that not ticking the report followup checkboxes clears the report followup sent dates"""
    case: Case = Case.objects.create(
        report_followup_week_1_sent_date=OTHER_DATE,
        report_followup_week_4_sent_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.report_followup_week_1_sent_date is None
    assert case_from_db.report_followup_week_4_sent_date is None


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
    organisation_name_case: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    domain_case: Case = Case.objects.create(home_page_url=HOME_PAGE_URL)

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


# def test_audit_shows_link_to_create_audit_when_no_audit_exists_and_audit_is_platform(
#     admin_client,
# ):
#     """
#     Test that audit details shows link to create when no audit exists
#     """
#     case: Case = Case.objects.create()

#     response: HttpResponse = admin_client.get(
#         reverse("cases:case-detail", kwargs={"pk": case.id}),
#     )
#     assert response.status_code == 200
#     assertContains(response, "A test does not exist for this case.")


# @pytest.mark.parametrize(
#     "audit_table_row",
#     [
#         ("Link to test"),
#         ("Test created"),
#         ("Screen size"),
#         ("Exemptions"),
#         ("Exemptions notes"),
#         ("Initial website compliance decision"),
#         ("Initial website compliance notes"),
#         ("Initial accessibility statement compliance decision"),
#         ("Initial accessibility statement compliance notes"),
#     ],
# )
# def test_audit_shows_table_when_audit_exists_and_audit_is_platform(
#     admin_client, audit_table_row
# ):
#     """
#     Test that audit details shows link to create when no audit exists
#     """
#     case: Case = Case.objects.create()
#     Audit.objects.create(case=case)
#     response: HttpResponse = admin_client.get(
#         reverse("cases:case-detail", kwargs={"pk": case.id}),
#     )
#     assert response.status_code == 200
#     assertContains(response, audit_table_row)


def test_report_details_shows_link_to_create_report_when_no_report_exists_and_report_is_platform(
    admin_client,
):
    """
    Test that audit details shows link to create when no audit exists
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response, "A report does not exist for this case. Create a report in"
    )


@pytest.mark.parametrize(
    "audit_table_row",
    [
        ("Link to report"),
        ("Notes"),
        ("View final HTML report"),
        ("Report views"),
        ("Unique visitors to report"),
    ],
)
def test_report_shows_table_when_report_exists_and_report_is_platform(
    admin_client, audit_table_row
):
    """
    Test that audit details shows link to create when no audit exists
    """
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    Report.objects.create(case=case)
    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, audit_table_row)


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
    "flag_name, section_name, edit_url_name",
    [
        ("case_details_complete_date", "Case details", "edit-case-details"),
        ("contact_details_complete_date", "Contact details", "edit-contact-details"),
        ("testing_details_complete_date", "Testing details", "edit-test-results"),
        ("reporting_details_complete_date", "Report details", "edit-report-details"),
        ("qa_process_complete_date", "QA process", "edit-qa-process"),
        (
            "report_correspondence_complete_date",
            "Report correspondence",
            "edit-report-correspondence",
        ),
        (
            "twelve_week_correspondence_complete_date",
            "12-week correspondence",
            "edit-twelve-week-correspondence",
        ),
        ("review_changes_complete_date", "Reviewing changes", "edit-review-changes"),
        (
            "twelve_week_retest_complete_date",
            "12-week retest",
            "edit-twelve-week-retest",
        ),
        ("case_close_complete_date", "Closing the case", "edit-case-close"),
        (
            "enforcement_correspondence_complete_date",
            "Equality body summary",
            "edit-enforcement-body-correspondence",
        ),
        ("post_case_complete_date", "Post case summary", "edit-post-case"),
    ],
)
def test_section_complete_check_displayed_in_platform_testing_methodology(
    flag_name, section_name, edit_url_name, admin_client
):
    """
    Test that the section complete tick is displayed in contents
    when case testing methodology is platform
    """
    case: Case = Case.objects.create()
    setattr(case, flag_name, TODAY)
    case.save()
    edit_url: str = reverse(f"cases:{edit_url_name}", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="#{edit_url_name[5:]}" class="govuk-link govuk-link--no-visited-state">
            {section_name}<span class="govuk-visually-hidden">complete</span></a>
            |
            <a id="{edit_url_name}" href="{edit_url}" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden">complete</span>
            </a>
            &check;
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "flag_name, section_name, section_id",
    [
        ("case_details_complete_date", "Case details", "case-details"),
        ("testing_details_complete_date", "Testing details", "test-results"),
        ("reporting_details_complete_date", "Report details", "report-details"),
        ("qa_process_complete_date", "QA process", "qa-process"),
        ("contact_details_complete_date", "Contact details", "contact-details"),
        (
            "report_correspondence_complete_date",
            "Report correspondence",
            "report-correspondence",
        ),
        (
            "twelve_week_correspondence_complete_date",
            "12-week correspondence",
            "twelve-week-correspondence",
        ),
        (
            "review_changes_complete_date",
            "Reviewing changes",
            "review-changes",
        ),
        (
            "final_website_complete_date",
            "Final website compliance decision",
            "final-website",
        ),
        (
            "final_statement_complete_date",
            "Final accessibility statement compliance decision",
            "final-statement",
        ),
        (
            "case_close_complete_date",
            "Closing the case",
            "case-close",
        ),
    ],
)
def test_section_complete_check_displayed_in_testing_spreadsheet_methodology(
    flag_name, section_name, section_id, admin_client
):
    """
    Test that the section complete tick is displayed in contents
    when case testing methodology is spreadsheet
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )
    setattr(case, flag_name, TODAY)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="#{section_id}" class="govuk-link govuk-link--no-visited-state">
            {section_name}<span class="govuk-visually-hidden">complete</span></a>
            &check;
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        ("cases:edit-case-details", "case_details_complete_date", "Case details"),
        ("cases:edit-test-results", "testing_details_complete_date", "Testing details"),
        (
            "cases:edit-report-details",
            "reporting_details_complete_date",
            "Report details",
        ),
        ("cases:edit-qa-process", "qa_process_complete_date", "QA process"),
        (
            "cases:edit-contact-details",
            "contact_details_complete_date",
            "Contact details",
        ),
        (
            "cases:edit-report-correspondence",
            "report_correspondence_complete_date",
            "Report correspondence",
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "twelve_week_correspondence_complete_date",
            "12-week correspondence",
        ),
        (
            "cases:edit-twelve-week-retest",
            "twelve_week_retest_complete_date",
            "12-week retest",
        ),
        (
            "cases:edit-review-changes",
            "review_changes_complete_date",
            "Reviewing changes",
        ),
        ("cases:edit-case-close", "case_close_complete_date", "Closing the case"),
        (
            "cases:edit-enforcement-body-correspondence",
            "enforcement_correspondence_complete_date",
            "Equality body summary",
        ),
        ("cases:edit-post-case", "post_case_complete_date", "Post case summary"),
    ],
)
def test_section_complete_check_displayed_in_steps_platform_methodology(
    step_url, flag_name, step_name, admin_client
):
    """
    Test that the section complete tick is displayed in list of steps
    when case testing methodology is platform
    """
    case: Case = Case.objects.create()
    setattr(case, flag_name, TODAY)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f'{step_name}<span class="govuk-visually-hidden">complete</span> &check;',
        html=True,
    )


def test_twelve_week_retest_page_shows_link_to_create_test_page_if_none_found(
    admin_client,
):
    """
    Test that the twelve week retest page shows the link to the test results page
    when no test exists on the case.
    """
    case: Case = Case.objects.create(testing_methodology="platform")

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "This case does not have a test.")

    edit_test_results_url: str = reverse(
        "cases:edit-test-results", kwargs={"pk": case.id}
    )
    assertContains(
        response,
        f"""<a href="{edit_test_results_url}"
            class="govuk-link govuk-link--no-visited-state">
                testing details
        </a>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_start_retest_button_if_no_retest_exists(
    admin_client,
):
    """
    Test that the twelve week retest page shows start retest button when a
    test exists with no retest.
    """
    case: Case = Case.objects.create(testing_methodology="platform")
    audit: Audit = Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "This case does not have a retest.")
    assertContains(response, "Click Start retest to move to the testing environment.")

    start_retest_url: str = reverse(
        "audits:audit-retest-start", kwargs={"pk": audit.id}
    )
    assertContains(
        response,
        f"""<a href="{start_retest_url}"
            role="button" draggable="false" class="govuk-button govuk-button--secondary"
            data-module="govuk-button">
            Start retest
        </a>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_view_retest_button_if_retest_exists(
    admin_client,
):
    """
    Test that the twelve week retest page shows view retest button when a
    test with a retest exists.
    """
    case: Case = Case.objects.create(testing_methodology="platform")
    audit: Audit = Audit.objects.create(case=case, retest_date=date.today())

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    view_retest_url: str = reverse(
        "audits:audit-retest-detail", kwargs={"pk": audit.id}
    )
    assertContains(
        response,
        f"""<a href="{view_retest_url}"
            role="button" draggable="false" class="govuk-button govuk-button--secondary"
            data-module="govuk-button">
            View retest
        </a>""",
        html=True,
    )


def test_case_review_changes_view_contains_link_to_test_results_url(admin_client):
    """Test that the case review changes view contains the link to the test results"""
    test_results_url: str = "https://test-results-url"
    case: Case = Case.objects.create(
        test_results_url=test_results_url,
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-review-changes", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<div class="govuk-hint">'
        f'The retest form can be found in the <a href="{test_results_url}"'
        ' class="govuk-link govuk-link--no-visited-state" target="_blank">test results</a>'
        "</div>",
    )


def test_case_review_changes_view_contains_no_link_to_test_results_url(admin_client):
    """
    Test that the case review changes view contains no link to the test results if none is on case
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-review-changes", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<div class="govuk-hint">'
        "There is no test spreadsheet for this case"
        "</div>",
    )


def test_case_review_changes_view_contains_no_mention_of_spreadsheet_if_platform_testing(
    admin_client,
):
    """
    Test that the case review changes view contains no mention of the lack of a link
    to the test results if none is on case and the methodology is platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-review-changes", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        '<div class="govuk-hint">'
        "There is no test spreadsheet for this case"
        "</div>",
    )


def test_calculate_report_followup_dates():
    """
    Test that the report followup dates are calculated correctly.
    """
    case: Case = Case()
    report_sent_date: date = date(2020, 1, 1)

    updated_case = calculate_report_followup_dates(
        case=case, report_sent_date=report_sent_date
    )

    assert updated_case.report_followup_week_1_due_date == date(2020, 1, 8)
    assert updated_case.report_followup_week_4_due_date == date(2020, 1, 29)
    assert updated_case.report_followup_week_12_due_date == date(2020, 3, 25)


def test_calculate_twelve_week_chaser_dates():
    """
    Test that the twelve week chaser dates are calculated correctly.
    """
    case: Case = Case()
    twelve_week_update_requested_date: date = date(2020, 1, 1)

    updated_case = calculate_twelve_week_chaser_dates(
        case=case, twelve_week_update_requested_date=twelve_week_update_requested_date
    )

    assert updated_case.twelve_week_1_week_chaser_due_date == date(2020, 1, 8)


@pytest.mark.parametrize(
    "due_date, expected_help_text",
    [
        (date(2020, 1, 1), "Due 1 January 2020"),
        (None, "None"),
    ],
)
def test_format_due_date_help_text(due_date, expected_help_text):
    """
    Test due date formatting for help text
    """
    assert format_due_date_help_text(due_date) == expected_help_text


def test_case_details_includes_link_to_auditors_cases(admin_client):
    """
    Test that the case details page contains a link to all the auditor's cases
    """
    user: User = User.objects.create(first_name="Joe", last_name="Bloggs")
    case: Case = Case.objects.create(auditor=user)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    user_id: int = user.id
    assertContains(
        response,
        f"""<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Auditor</th>
            <td class="govuk-table__cell amp-width-one-half">
                <a href="{reverse("cases:case-list")}?auditor={ user_id }" rel="noreferrer noopener" class="govuk-link">
                    Joe Bloggs
                </a>
            </td>
        </tr>""",
        html=True,
    )


def test_case_details_has_no_link_to_auditors_cases_if_no_auditor(admin_client):
    """
    Test that the case details page contains no link to the auditor's cases if no auditor is set
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Auditor</th>
            <td class="govuk-table__cell amp-width-one-half">None</td>
        </tr>""",
        html=True,
    )


def test_case_details_includes_link_to_report(admin_client):
    """
    Test that the case details page contains a link to the report
    """
    report_final_pdf_url: str = "https://report-final-pdf-url.com"
    case: Case = Case.objects.create(
        report_methodology=REPORT_METHODOLOGY_ODT,
        report_final_pdf_url=report_final_pdf_url,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        f"""<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">
            Link to final PDF report</th>
            <td class="govuk-table__cell amp-width-one-half">
                <a href="{report_final_pdf_url}" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Final draft (PDF)
                </a>
            </td>
        </tr>""",
        html=True,
    )


def test_case_details_includes_no_link_to_report(admin_client):
    """
    Test that the case details page contains no link to the report if none is set
    """
    case: Case = Case.objects.create(report_methodology=REPORT_METHODOLOGY_ODT)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Link to final PDF report</th>
            <td class="govuk-table__cell amp-width-one-half">None</td>
        </tr>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_link_label",
    [
        "Edit case details",
        #        "Edit testing details",
        "Edit report details",
        "Edit QA process",
        "Edit contact details",
        "Edit report correspondence",
        "Edit 12-week correspondence",
        #        "Edit 12-week retest",
        "Edit reviewing changes",
        "Edit closing the case",
        "Edit equality body summary",
        "Edit post case summary",
    ],
)
def test_case_details_shows_edit_links(
    edit_link_label,
    admin_client,
):
    """
    Test case details show edit links when testing methodology is platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, edit_link_label)


@pytest.mark.parametrize(
    "edit_link_label",
    [
        "Edit equality body summary",
        "Edit post case summary",
    ],
)
def test_case_details_shows_edit_links_when_spreadsheet(
    edit_link_label,
    admin_client,
):
    """
    Test case details show edit links when testing methodology is spreadsheet.
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, edit_link_label)


@pytest.mark.parametrize(
    "edit_link_label",
    [
        "Edit case details",
        "Edit testing details",
        "Edit report details",
        "Edit QA process",
        "Edit contact details",
        "Edit report correspondence",
        "Edit 12-week correspondence",
        "Edit 12-week retest",
        "Edit reviewing changes",
        "Edit closing the case",
    ],
)
def test_case_details_hides_edit_links_when_spreadsheet(
    edit_link_label,
    admin_client,
):
    """
    Test case details does not show edit links when testing methodology is
    spreadsheet.
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertNotContains(response, edit_link_label)


def test_status_change_message_shown(admin_client):
    """Test updating the case status causes a message to be shown on the next page"""
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)

    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-details", kwargs={"pk": case.id}),
        {
            "auditor": user.id,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "version": case.version,
            "save": "Save and continue",
        },
        follow=True,
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<div class="govuk-inset-text">
            Status changed from 'Unassigned case' to 'Test in progress'
        </div>""",
        html=True,
    )


@pytest.mark.django_db
def test_qa_process_approval_notifies_auditor(rf):
    """Test approving the report on the QA process page notifies the auditor"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME, auditor=user)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.post(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "report_approved_status": REPORT_APPROVED_STATUS_APPROVED,
            "save": "Button value",
        },
    )
    request.user = request_user

    response: HttpResponse = CaseQAProcessUpdateView.as_view()(request, pk=case.id)

    assert response.status_code == 302

    notification: Optional[Notification] = Notification.objects.filter(
        user=user
    ).first()

    assert notification is not None
    assert (
        notification.body == f"{request_user.get_full_name()} QA approved Case {case}"
    )


@pytest.mark.parametrize(
    "useful_link, edit_url_name",
    [
        ("zendesk_url", "edit-case-details"),
        ("trello_url", "edit-contact-details"),
        ("zendesk_url", "edit-test-results"),
        ("trello_url", "edit-report-details"),
        ("trello_url", "edit-qa-process"),
        ("zendesk_url", "edit-report-correspondence"),
        ("trello_url", "edit-twelve-week-correspondence"),
        ("zendesk_url", "edit-review-changes"),
        ("zendesk_url", "edit-case-close"),
        ("trello_url", "edit-enforcement-body-correspondence"),
        ("zendesk_url", "edit-post-case"),
    ],
)
def test_useful_links_displayed_in_edit(useful_link, edit_url_name, admin_client):
    """
    Test that the useful links are displayed on all edit pages
    """
    case: Case = Case.objects.create(home_page_url="https://home_page_url.com")
    setattr(case, useful_link, f"https://{useful_link}.com")
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(f"cases:{edit_url_name}", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "<li>Unassigned case</li>")

    assertContains(
        response,
        """<li>
            <a href="https://home_page_url.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                Link to website
            </a>
        </li>""",
        html=True,
    )

    if useful_link == "trello_url":
        assertContains(
            response,
            """<li>
                <a href="https://trello_url.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Trello
                </a>
            </li>""",
            html=True,
        )
        assertNotContains(
            response,
            """<li>
                <a href="https://zendesk_url.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Zendesk
                </a>
            </li>""",
            html=True,
        )
    else:
        assertNotContains(
            response,
            """<li>
                <a href="https://trello_url.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Trello
                </a>
            </li>""",
            html=True,
        )
        assertContains(
            response,
            """<li>
                <a href="https://zendesk_url.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Zendesk
                </a>
            </li>""",
            html=True,
        )


def test_case_reviewer_updated_when_report_approved(admin_client, admin_user):
    """
    Test that the case QA auditor is set to the current user when report is approved
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
        {
            "report_approved_status": "yes",
            "version": case.version,
            "save": "Save and continue",
        },
    )

    assert response.status_code == 302
    updated_case: Case = Case.objects.get(pk=case.id)
    assert updated_case.reviewer == admin_user


@pytest.mark.django_db
def test_create_case_with_duplicates_shows_previous_url_field(admin_client):
    """
    Test that create case with duplicates found shows URL to previous case field
    """
    Case.objects.create(
        home_page_url=HOME_PAGE_URL,
        organisation_name="other organisation name",
    )
    Case.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url="other_url",
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "organisation_name": ORGANISATION_NAME,
        },
    )

    assert response.status_code == 200
    assertContains(
        response,
        "If the website has been previously audited, include a link to the case below",
    )


def test_updating_case_create_event(admin_client):
    """Test that updating a case also creates an event"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "report_correspondence_complete_date": "on",
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    content_type: ContentType = ContentType.objects.get_for_model(Case)
    event: Event = Event.objects.get(content_type=content_type, object_id=case.id)

    assert event.type == EVENT_TYPE_MODEL_UPDATE


def test_add_contact_also_creates_event(admin_client):
    """Test adding a contact also creates an event"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "",
            "form-0-name": "",
            "form-0-job_title": "",
            "form-0-email": CONTACT_EMAIL,
            "form-0-notes": "",
            "version": case.version,
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200
    contacts: QuerySet[Contact] = Contact.objects.filter(case=case)
    assert contacts.count() == 1
    contact: Contact = list(contacts)[0]

    content_type: ContentType = ContentType.objects.get_for_model(Contact)
    event: Event = Event.objects.get(content_type=content_type, object_id=contact.id)

    assert event.type == EVENT_TYPE_MODEL_CREATE


def test_delete_contact_adds_update_event(admin_client):
    """Test that pressing the remove contact button adds an update event"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": case.version,
            f"remove_contact_{contact.id}": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200

    content_type: ContentType = ContentType.objects.get_for_model(Contact)
    event: Event = Event.objects.get(content_type=content_type, object_id=contact.id)

    assert event.type == EVENT_TYPE_MODEL_UPDATE


def test_links_to_contact_and_accessibility_pages_shown(admin_client):
    """
    Test that links to the contact and accessibility statement pages on the
    organisation website are shown on the contact details page.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_CONTACT, url=CONTACT_STATEMENT_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, ACCESSIBILITY_STATEMENT_URL)
    assertContains(response, CONTACT_STATEMENT_URL)


def test_links_to_contact_and_accessibility_pages_not_shown(admin_client):
    """
    Test that links to the contact and accessibility statement pages on the
    organisation website are not shown on the contact details page if none have
    been recorded.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "No contact page.")
    assertContains(response, "No accessibility statement page.")


def test_update_case_checks_version(admin_client):
    """Test that updating a case shows an error if the version of the case has changed"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version - 1,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {ORGANISATION_NAME} | #1 has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_url_name",
    [
        "case-detail",
        "edit-case-details",
        "edit-test-results",
        "edit-report-details",
        "edit-qa-process",
        "edit-contact-details",
        "edit-report-correspondence",
        "edit-twelve-week-correspondence",
        "edit-twelve-week-retest",
        "edit-review-changes",
        "edit-case-close",
        "edit-enforcement-body-correspondence",
        "edit-post-case",
    ],
)
def test_platform_shows_notification_if_fully_compliant(
    edit_url_name,
    admin_client,
):
    """
    Test cases with fully compliant website and accessibility statement show
    notification to that effect on report details page.
    """
    case: Case = Case.objects.create(
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    )

    response: HttpResponse = admin_client.get(
        reverse(f"cases:{edit_url_name}", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<h3 class="govuk-notification-banner__heading amp-max-width-100">
            The case has a compliant website and a compliant accessibility statement.
        </h3>""",
        html=True,
    )


@pytest.mark.parametrize(
    "report_methodology, report_link_label",
    [
        (REPORT_METHODOLOGY_PLATFORM, "Link to report</th>"),
        (REPORT_METHODOLOGY_ODT, "Link to report draft"),
    ],
)
def test_case_details_shows_link_to_report(
    report_methodology,
    report_link_label,
    admin_client,
):
    """
    Test link to correct type is report is shown on case detail page.
    """
    case: Case = Case.objects.create(report_methodology=report_methodology)
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, report_link_label)


def test_platform_report_correspondence_shows_link_to_report_if_none_published(
    admin_client,
):
    """
    Test cases using platform-based reports show a link to report details if no
    report has been published.
    """
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    report_publisher_url: str = reverse(
        "reports:report-publisher", kwargs={"pk": report.id}
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<p class="govuk-body-m">
            A published report does not exist for this case. Publish report in
            <a href="{report_publisher_url}" class="govuk-link govuk-link--no-visited-state">
                Case > Report publisher
            </a>
        </p>""",
        html=True,
    )


def test_non_platform_qa_process_shows_no_link_to_draft_report(admin_client):
    """
    Test that the QA process page shows that the link to report draft is none
    when none is set and the report methodology is not platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<div class="govuk-form-group">
            <label class="govuk-label"><b>Link to report draft</b></label>
            <div class="govuk-hint">None</div>
        </div>""",
        html=True,
    )


def test_non_platform_qa_process_shows_link_to_draft_report(admin_client):
    """
    Test that the QA process page shows the link to report draft
    when the report methodology is not platform.
    """
    case: Case = Case.objects.create(
        report_draft_url=DRAFT_REPORT_URL,
        report_methodology=REPORT_METHODOLOGY_ODT,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label class="govuk-label"><b>Link to report draft</b></label>
            <div class="govuk-hint">
                <a href="{DRAFT_REPORT_URL}" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    Link to report draft
                </a>
            </div>
        </div>""",
        html=True,
    )


def test_non_platform_report_correspondence_shows_no_link_to_report(admin_client):
    """
    Test cases using platform-based reports show no link to report details if no
    report has been published.
    """
    case: Case = Case.objects.create()
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertNotContains(
        response, "A published report does not exist for this case.", html=True
    )


def test_platform_qa_process_shows_no_link_to_preview_report(admin_client):
    """
    Test that the QA process page shows that the link to report draft is none
    when no report exists and the report methodology is platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<div class="govuk-form-group">
            <label class="govuk-label"><b>Link to report draft</b></label>
            <div class="govuk-hint">None</div>
        </div>""",
        html=True,
    )


def test_platform_qa_process_shows_link_to_preview_report(admin_client):
    """
    Test that the QA process page shows the link to preview draft
    when the report methodology is platform.
    """
    case: Case = Case.objects.create()

    report: Report = Report.objects.create(case=case)
    report_publisher_url: str = reverse(
        "reports:report-publisher", kwargs={"pk": report.id}
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label class="govuk-label"><b>Link to report draft</b></label>
            <div class="govuk-hint">
                <a href="{report_publisher_url}" rel="noreferrer noopener" target="_blank" class="govuk-link govuk-link--no-visited-state">
                    Report publisher
                </a>
            </div>
        </div>""",
        html=True,
    )


def test_platform_qa_process_shows_link_to_publish_report(admin_client):
    """
    Test that the QA process page shows the link to publish the report
    when the report methodology is platform and report has not been published.
    """
    case: Case = Case.objects.create()

    report: Report = Report.objects.create(case=case)
    report_confirm_publish_url: str = reverse(
        "reports:report-confirm-publish", kwargs={"pk": report.id}
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label class="govuk-label"><b>Published report</b></label>
            <div class="govuk-hint">
                HTML report has not been published. Publish report in
                <a href="{report_confirm_publish_url}" class="govuk-link govuk-link--no-visited-state">
                    Case > Report publisher > Publish HTML report</a>
            </div>
        </div>""",
        html=True,
    )


def test_platform_qa_process_shows_link_to_s3_report(admin_client):
    """
    Test that the QA process page shows the link to report on S3
    when the report methodology is platform and report has been published.
    """
    case: Case = Case.objects.create()
    Report.objects.create(case=case)
    s3_report: S3Report = S3Report.objects.create(
        case=case, guid="guid", version=0, latest_published=True
    )
    s3_report_url: str = (
        f"{settings.AMP_PROTOCOL}{settings.AMP_VIEWER_DOMAIN}/reports/{s3_report.guid}"
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label class="govuk-label"><b>Published report</b></label>
            <div class="govuk-hint">
                <a href="{s3_report_url}" rel="noreferrer noopener"
                    target="_blank" class="govuk-link">
                    View final HTML report
                </a>
            </div>
        </div>""",
        html=True,
    )


def test_non_platform_qa_process_shows_final_report_fields(admin_client):
    """
    Test that the QA process page shows the final report fields
    when the report methodology is not platform.
    """
    case: Case = Case.objects.create(report_methodology=REPORT_METHODOLOGY_ODT)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(response, "Link to final PDF report")
    assertContains(response, "Link to final ODT report")


def test_platform_qa_process_does_not_show_final_report_fields(admin_client):
    """
    Test that the QA process page does not show the final report fields
    when the report methodology is platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertNotContains(response, "Link to final PDF report")
    assertNotContains(response, "Link to final ODT report")


def test_qa_process_opens_discussion(admin_client):
    """
    Test that the QA process page opens the discussion details element
    by default.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        f'{reverse("cases:edit-qa-process", kwargs={"pk": case.id})}?discussion=open',
    )

    assert response.status_code == 200
    assertContains(
        response, '<details class="govuk-details" data-module="govuk-details" open>'
    )


def test_report_corespondence_shows_link_to_create_report(admin_client):
    """
    Test that the report correspondence page shows link to create report
    if one does not exist.
    """
    case: Case = Case.objects.create()
    report_details_url: str = reverse(
        "cases:edit-report-details", kwargs={"pk": case.id}
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-correspondence", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        f"""<p class="govuk-body-m">
            A published report does not exist for this case. Create a report in
            <a href="{report_details_url}" class="govuk-link govuk-link--no-visited-state">
                Case > Report details
            </a>
        </p>""",
        html=True,
    )


def test_twelve_week_correspondence_psb_contact(admin_client):
    """
    Test that the twelve week correspondence page shows full page when
    contact has been made with the public sector body
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-correspondence", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        "The public sector body has been as unresponsive to this case.",
    )
    assertContains(
        response,
        "Edit 12-week correspondence due dates",
    )
    assertContains(
        response,
        "12-week deadline",
    )


def test_twelve_week_correspondence_no_psb_contact(admin_client):
    """
    Test that the twelve week correspondence page shows small page when no
    contact has been made with the public sector body
    """
    case: Case = Case.objects.create(no_psb_contact=BOOLEAN_TRUE)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-correspondence", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200
    assertContains(
        response,
        "The public sector body has been as unresponsive to this case.",
    )
    assertNotContains(
        response,
        "Edit 12-week correspondence due dates",
    )
    assertNotContains(
        response,
        "12-week deadline",
    )


def test_status_workflow_assign_an_auditor(admin_client, admin_user):
    """
    Test that the status workflow page ticks 'Assign an auditor' only
    when an auditor is assigned.
    """
    case: Case = Case.objects.create()
    case_pk_kwargs: Dict[str, int] = {"pk": case.id}

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{reverse('cases:edit-case-details', kwargs=case_pk_kwargs)}"
                class="govuk-link govuk-link--no-visited-state">
                Assign an auditor</a></li>""",
        html=True,
    )

    case.auditor = admin_user
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{reverse('cases:edit-case-details', kwargs=case_pk_kwargs)}"
                class="govuk-link govuk-link--no-visited-state">
                Assign an auditor</a>&check;</li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name,label,field_name,field_value",
    [
        (
            "cases:edit-test-results",
            "Initial website compliance decision is not filled in",
            "is_website_compliant",
            IS_WEBSITE_COMPLIANT_COMPLIANT,
        ),
        (
            "cases:edit-test-results",
            "Initial accessibility statement decision is not filled in",
            "accessibility_statement_state",
            ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        ),
        (
            "cases:edit-qa-process",
            "Report ready to be reviewed needs to be Yes",
            "report_review_status",
            REPORT_READY_TO_REVIEW,
        ),
        (
            "cases:edit-qa-process",
            "Report approved needs to be Yes",
            "report_approved_status",
            REPORT_APPROVED_STATUS_APPROVED,
        ),
        (
            "cases:edit-report-correspondence",
            "Report sent on requires a date",
            "report_sent_date",
            TODAY,
        ),
        (
            "cases:edit-report-correspondence",
            "Report acknowledged requires a date",
            "report_acknowledged_date",
            TODAY,
        ),
        (
            "cases:edit-no-psb-response",
            "No response from PSB",
            "no_psb_contact",
            BOOLEAN_TRUE,
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "12-week update requested requires a date",
            "twelve_week_update_requested_date",
            TODAY,
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "12-week update received requires a date or mark the case as having no response",
            "twelve_week_correspondence_acknowledged_date",
            TODAY,
        ),
        (
            "cases:edit-twelve-week-correspondence",
            "12-week update received requires a date or mark the case as having no response",
            "no_psb_contact",
            BOOLEAN_TRUE,
        ),
        (
            "cases:edit-review-changes",
            "Is this case ready for final decision? needs to be Yes",
            "is_ready_for_final_decision",
            BOOLEAN_TRUE,
        ),
        (
            "cases:edit-case-close",
            "Case completed requires a decision",
            "case_completed",
            CASE_COMPLETED_SEND,
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "Date sent to equality body requires a date",
            "sent_to_enforcement_body_sent_date",
            TODAY,
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "Equality body pursuing this case? should either be 'Yes, completed' or 'Yes, in progress'",
            "enforcement_body_pursuing",
            ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "Equality body pursuing this case? should be 'Yes, completed'",
            "enforcement_body_pursuing",
            ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
        ),
    ],
)
def test_status_workflow_page(path_name, label, field_name, field_value, admin_client):
    """
    Test that the status workflow page ticks its action links
    only when the linked action's value has been set.
    """
    case: Case = Case.objects.create()
    case_pk_kwargs: Dict[str, int] = {"pk": case.id}
    link_url: str = reverse(path_name, kwargs=case_pk_kwargs)

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{link_url}" class="govuk-link govuk-link--no-visited-state">
                {label}</a></li>""",
        html=True,
    )

    setattr(case, field_name, field_value)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{link_url}"
                class="govuk-link govuk-link--no-visited-state">
                {label}</a>&check;</li>""",
        html=True,
    )


def test_case_steps_shown_when_platform_testing(admin_client):
    """
    Test case steps shown when testing methodology is platform.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-enforcement-body-correspondence", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<h2 class="govuk-heading-m amp-margin-bottom-5">Case steps</h2>""",
        html=True,
    )
    assertNotContains(
        response,
        """<h2 class="govuk-heading-m amp-margin-bottom-5">Post case</h2>""",
        html=True,
    )


def test_case_steps_hidden_when_testing_spreadsheet(admin_client):
    """
    Test case details not showm edit links when testing methodology is spreadsheet.
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-enforcement-body-correspondence", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<h2 class="govuk-heading-m amp-margin-bottom-5">Post case</h2>""",
        html=True,
    )
    assertNotContains(
        response,
        """<h2 class="govuk-heading-m amp-margin-bottom-5">Case steps</h2>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_case_url_name, nav_link_name,nav_link_label",
    [
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-case-details",
            "Case details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-test-results",
            "Testing details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-report-details",
            "Report details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-qa-process",
            "QA process",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-contact-details",
            "Contact details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-report-correspondence",
            "Report correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-twelve-week-correspondence",
            "12-week correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-twelve-week-retest",
            "12-week retest",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-review-changes",
            "Reviewing changes",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-case-close",
            "Closing the case",
        ),
        (
            "cases:edit-post-case",
            "cases:edit-enforcement-body-correspondence",
            "Equality body summary",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-post-case",
            "Post case summary",
        ),
    ],
)
def test_navigation_links_shown_when_platform_testing(
    edit_case_url_name,
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test case steps' navigation links are shown when testing methodology is
    platform.
    """
    case: Case = Case.objects.create()
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse(edit_case_url_name, kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state">{nav_link_label}</a>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_case_url_name, nav_link_name,nav_link_label",
    [
        (
            "cases:edit-post-case",
            "cases:edit-enforcement-body-correspondence",
            "Equality body summary",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-post-case",
            "Post case summary",
        ),
    ],
)
def test_navigation_links_shown_when_spreadsheet_testing(
    edit_case_url_name,
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test correct case steps' navigation links are shown when testing methodology
    is spreadsheet.
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse(edit_case_url_name, kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state">{nav_link_label}</a>""",
        html=True,
    )


@pytest.mark.parametrize(
    "edit_case_url_name, nav_link_name,nav_link_label",
    [
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-case-details",
            "Case details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-test-results",
            "Testing details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-report-details",
            "Report details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-qa-process",
            "QA process",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-contact-details",
            "Contact details",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-report-correspondence",
            "Report correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-twelve-week-correspondence",
            "12-week correspondence",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-twelve-week-retest",
            "12-week retest",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-review-changes",
            "Reviewing changes",
        ),
        (
            "cases:edit-enforcement-body-correspondence",
            "cases:edit-case-close",
            "Closing the case",
        ),
    ],
)
def test_navigation_links_hidden_when_spreadsheet_testing(
    edit_case_url_name,
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test correct case steps' navigation links are not hodden when testing
    methodology is spreadsheet.
    """
    case: Case = Case.objects.create(
        testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
    )
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse(edit_case_url_name, kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertNotContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state">{nav_link_label}</a>""",
        html=True,
    )


# def test_case_details_hides_link_to_test_results_when_not_present(admin_client):
#     """
#     Test case details hides link to test results when URL not present
#     when testing methodology is spreadsheet.
#     """
#     case: Case = Case.objects.create(
#         testing_methodology=TESTING_METHODOLOGY_SPREADSHEET
#     )

#     response: HttpResponse = admin_client.get(
#         reverse("cases:case-detail", kwargs={"pk": case.id}),
#     )
#     assert response.status_code == 200

#     assertContains(
#         response,
#         """<tr class="govuk-table__row">
#             <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">
#                 Link to test results
#             </th>
#             <td class="govuk-table__cell amp-width-one-half">None</td>
#         </tr>""",
#         html=True,
#     )


def test_case_details_contents_hides_link_to_12_week_retest_when_testing_methodology_spreadsheet(
    admin_client,
):
    """
    Test case details hides contents link to 12-week retest
    when testing methodology is spreadsheet.
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        """<a href="#twelve-week-retest" class="govuk-link govuk-link--no-visited-state">
            12-week retest</a>""",
        html=True,
    )

    case.testing_methodology = TESTING_METHODOLOGY_SPREADSHEET
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertNotContains(
        response,
        """<a href="#twelve-week-retest" class="govuk-link govuk-link--no-visited-state">
            12-week retest</a>""",
        html=True,
    )


def test_outstanding_issues(admin_client):
    """
    Test out standing issues page renders according to URL parameters.
    """
    audit: Audit = create_audit_and_check_results()
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": audit.case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "Group by WCAG error")
    assertNotContains(response, "Group by Page")
    assertContains(response, """<h2 id="page-2" class="govuk-heading-l">Home</h2>""")
    assertNotContains(
        response, """<h2 id="wcag-77" class="govuk-heading-m">Axe WCAG</h2>"""
    )

    response: HttpResponse = admin_client.get(f"{url}?view=WCAG+view")

    assert response.status_code == 200

    assertNotContains(response, "Group by WCAG error")
    assertContains(response, "Group by page")
    assertNotContains(response, """<h2 id="page-2" class="govuk-heading-l">Home</h2>""")
    assertContains(
        response, """<h2 id="wcag-77" class="govuk-heading-m">Axe WCAG</h2>"""
    )

    response: HttpResponse = admin_client.get(f"{url}?view=Page+view")

    assert response.status_code == 200

    assertContains(response, "Group by WCAG error")
    assertNotContains(response, "Group by page")
    assertContains(response, """<h2 id="page-2" class="govuk-heading-l">Home</h2>""")
    assertNotContains(
        response, """<h2 id="wcag-77" class="govuk-heading-m">Axe WCAG</h2>"""
    )


def test_outstanding_issues_overview(admin_client):
    """
    Test out standing issues page shows overview.
    """
    audit: Audit = create_audit_and_check_results()
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": audit.case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "0 of 3 WCAG errors have been fixed", html=True)
    assertContains(response, "0 of 12 statement errors have been fixed", html=True)
