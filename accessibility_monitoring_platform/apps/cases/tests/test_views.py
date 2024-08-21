"""
Tests for cases views
"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from moto import mock_aws
from pytest_django.asserts import assertContains, assertNotContains

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)
from ...audits.tests.test_models import ERROR_NOTES, create_audit_and_check_results
from ...comments.models import Comment
from ...common.models import Boolean, EmailTemplate, Event, Sector
from ...common.utils import amp_format_date
from ...exports.csv_export_utils import (
    CASE_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ...notifications.models import Task
from ...reports.models import Report
from ...s3_read_write.models import S3Report
from ..models import (
    Case,
    CaseCompliance,
    CaseEvent,
    Contact,
    EqualityBodyCorrespondence,
    ZendeskTicket,
)
from ..utils import create_case_and_compliance
from ..views import (
    FOUR_WEEKS_IN_DAYS,
    ONE_WEEK_IN_DAYS,
    TWELVE_WEEKS_IN_DAYS,
    CaseReportApprovedUpdateView,
    calculate_no_contact_chaser_dates,
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
    find_duplicate_cases,
    format_due_date_help_text,
)

CONTACT_EMAIL: str = "test@email.com"
DOMAIN: str = "domain.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}"
ORGANISATION_NAME: str = "Organisation name"
REPORT_SENT_DATE: date = date(2021, 2, 28)
UPDATE_REQUESTED_DATE: date = date(2021, 5, 10)
OTHER_DATE: date = date(2020, 12, 31)
ONE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
FOUR_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=FOUR_WEEKS_IN_DAYS
)
TWELVE_WEEK_FOLLOWUP_DUE_DATE: date = REPORT_SENT_DATE + timedelta(
    days=TWELVE_WEEKS_IN_DAYS
)
ONE_WEEK_CHASER_DUE_DATE: date = TWELVE_WEEK_FOLLOWUP_DUE_DATE + timedelta(
    days=ONE_WEEK_IN_DAYS
)
DEACTIVATE_NOTES: str = """I am
a deactivate note,
I am"""
STATEMENT_COMPLIANCE_NOTES: str = "Accessibility Statement note"
TODAY: date = date.today()
DRAFT_REPORT_URL: str = "https://draft-report-url.com"
case_feedback_survey_columns_to_export_str: str = ",".join(
    column.column_header for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
)
case_equality_body_columns_to_export_str: str = ",".join(
    column.column_header for column in EQUALITY_BODY_COLUMNS_FOR_EXPORT
)
case_columns_to_export_str: str = ",".join(
    column.column_header for column in CASE_COLUMNS_FOR_EXPORT
)
ACCESSIBILITY_STATEMENT_URL: str = "https://example.com/accessibility-statement"
CONTACT_STATEMENT_URL: str = "https://example.com/contact"
TODAY: date = date.today()
QA_COMMENT_BODY: str = "QA comment body"
CASE_ARCHIVE: List[Dict] = {
    "sections": [
        {
            "name": "Archived section one",
            "complete": "2021-10-21",
            "fields": [
                {
                    "name": "archived_date_field_one",
                    "data_type": "date",
                    "label": "Date field",
                    "value": "2021-04-19",
                    "display_value": "19 April 2021",
                },
                {
                    "name": "archived_choice_field",
                    "data_type": "str",
                    "label": "Status field",
                    "value": "case-closed-sent-to-equalities-body",
                    "display_value": "Case closed and sent to equalities body",
                },
            ],
            "subsections": [
                {
                    "name": "Archived subsection a",
                    "complete": None,
                    "fields": [
                        {
                            "name": "archived_datetime_field_one",
                            "data_type": "datetime",
                            "label": "Datetime field",
                            "value": "2023-03-01T13:01:17+00:00",
                            "display_value": "1 March 2023 1:17pm",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Archived section two",
            "complete": None,
            "fields": [
                {
                    "name": "archived_url",
                    "data_type": "link",
                    "label": "Archived URL",
                    "value": "https://www.example.com",
                    "display_value": "www.example.com",
                },
                {
                    "name": "archived_notes",
                    "data_type": "markdown",
                    "label": "Archived notes",
                    "value": "Monitoring suspended - private practice",
                    "display_value": None,
                },
            ],
            "subsections": None,
        },
    ]
}
RESOLVED_EQUALITY_BODY_MESSAGE: str = "Resolved equality body correspondence message"
RESOLVED_EQUALITY_BODY_NOTES: str = "Resolved equality body correspondence notes"
UNRESOLVED_EQUALITY_BODY_MESSAGE: str = (
    "Unresolved equality body correspondence message"
)
UNRESOLVED_EQUALITY_BODY_NOTES: str = "Unresolved equality body correspondence notes"
STATEMENT_CHECK_RESULT_REPORT_COMMENT: str = "Statement check result report comment"
STATEMENT_CHECK_RESULT_RETEST_COMMENT: str = "Statement check result retest comment"
REPORT_ACKNOWLEDGED_WARNING: str = (
    "The report has been acknowledged by the organisation, and no further follow-up is needed."
)
TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING: str = (
    "The request for a final update has been acknowledged by the organisation"
)
RECOMMENDATION_NOTE: str = "Recommendation note"
ZENDESK_URL: str = "https://zendesk.com/ticket"
ZENDESK_SUMMARY: str = "Zendesk ticket summary"
PAGE_LOCATION: str = "Press A and then B"
EXAMPLE_EMAIL_TEMPLATE_ID: int = 4
RETEST_NOTES: str = "Retest notes"
HOME_PAGE_ERROR_NOTES: str = "Home page error note"
STATEMENT_PAGE_ERROR_NOTES: str = "Statement page error note"
OUTSTANDING_ISSUE_NOTES: str = "Outstanding error found."
CORRESPONDENCE_PROCESS_PAGES: List[Tuple[str, str]] = [
    ("edit-request-contact-details", "Request contact details"),
    ("edit-one-week-contact-details", "One-week follow-up"),
    ("edit-four-week-contact-details", "Four-week follow-up"),
    ("edit-no-psb-response", "Unresponsive PSB"),
]


def add_user_to_auditor_groups(user: User) -> None:
    auditor_group: Group = Group.objects.create(name="Auditor")
    historic_auditor_group: Group = Group.objects.create(name="Historic auditor")
    qa_auditor_group: Group = Group.objects.create(name="QA auditor")
    auditor_group.user_set.add(user)
    historic_auditor_group.user_set.add(user)
    qa_auditor_group.user_set.add(user)


def test_archived_case_view_case_includes_contents(admin_client):
    """
    Test that the View case page for an archived case shows links to sections
    """
    case: Case = Case.objects.create(archive=json.dumps(CASE_ARCHIVE))

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<a href="#archived-section-one" class="govuk-link govuk-link--no-visited-state">
        Archived section one <span class="govuk-visually-hidden">complete</span></a>""",
        html=True,
    )
    assertContains(
        response,
        """<a href="#archived-section-two" class="govuk-link govuk-link--no-visited-state">
        Archived section two</a>""",
        html=True,
    )


def test_archived_case_view_case_includes_sections(admin_client):
    """
    Test that the View case page for an archived case shows sections and subsections.
    """
    case: Case = Case.objects.create(archive=json.dumps(CASE_ARCHIVE))

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<span class="govuk-accordion__section-button" id="accordion-heading-archived-section-one">
            Archived section one
            <span class="govuk-visually-hidden">complete</span>
            ✓
        </span>""",
        html=True,
    )
    assertContains(
        response,
        """<p id="archived-subsection-a" class="govuk-body-m"><b>Archived subsection a</b></p>""",
        html=True,
    )
    assertContains(
        response,
        """<span class="govuk-accordion__section-button" id="accordion-heading-archived-section-two">
            Archived section two
        </span>""",
        html=True,
    )


def test_archived_case_view_case_includes_fields(admin_client):
    """
    Test that the View case page for an archived case shows fields
    """
    case: Case = Case.objects.create(archive=json.dumps(CASE_ARCHIVE))

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Date field</th>
            <td class="govuk-table__cell amp-width-one-half">19 April 2021</td>
        </tr>
        """,
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Status field</th>
            <td class="govuk-table__cell amp-width-one-half">Case closed and sent to equalities body</td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Datetime field</th>
            <td class="govuk-table__cell amp-width-one-half">1 March 2023 1:17pm</td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Archived URL</th>
            <td class="govuk-table__cell amp-width-one-half">
                <a href="https://www.example.com" rel="noreferrer noopener" target="_blank" class="govuk-link">
                    www.example.com
                </a>
            </td>
        </tr>""",
        html=True,
    )
    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__cell amp-font-weight-normal amp-width-one-half">Archived notes</th>
            <td class="govuk-table__cell amp-width-one-half amp-notes">
                 <p>Monitoring suspended - private practice</p>
            </td>
        </tr>""",
        html=True,
    )


def test_archived_case_view_case_includes_post_case_sections(admin_client):
    """
    Test that the View case page for an archived case shows expected post case.
    """
    case: Case = Case.objects.create(
        archive=json.dumps(CASE_ARCHIVE), variant=Case.Variant.ARCHIVED
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(response, "Statement enforcement")
    assertContains(response, "Equality body metadata")
    assertContains(response, "Equality body correspondence")
    assertContains(response, "Equality body retest overview")
    assertContains(response, "Legacy end of case data")


def test_non_archived_case_view_case_has_no_legacy_section(admin_client):
    """
    Test that the View case page for a non-archived case has no
    legacy section.
    """
    case: Case = Case.objects.create(variant=Case.Variant.CLOSE_CASE)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )

    assertContains(response, "Statement enforcement")
    assertContains(response, "Equality body metadata")
    assertContains(response, "Equality body correspondence")
    assertContains(response, "Equality body retest overview")
    assertNotContains(response, "Legacy end of case data")


def test_view_case_includes_tests(admin_client):
    """
    Test that the View case displays test and 12-week retest.
    """
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, "Initial test metadata")
    assertContains(response, "Date of test")
    assertContains(response, "Initial statement compliance decision")

    assertContains(response, "12-week retest metadata")
    assertContains(response, "Date of retest")


def test_view_case_includes_zendesk_tickets(admin_client):
    """
    Test that the View case displays Zendesk tickets.
    """
    case: Case = Case.objects.create()
    ZendeskTicket.objects.create(
        case=case,
        url=ZENDESK_URL,
        summary=ZENDESK_SUMMARY,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(response, "PSB Zendesk tickets")
    assertContains(response, ZENDESK_URL)
    assertContains(response, ZENDESK_SUMMARY)


def test_case_detail_view_leaves_out_deleted_contact(admin_client):
    """Test that deleted Contacts are not included in context"""
    case: Case = Case.objects.create()
    Contact.objects.create(
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
    assertContains(response, "Undeleted Contact")
    assertNotContains(response, "Deleted Contact")


def test_case_list_view_filters_by_unassigned_qa_case(admin_client):
    """Test that Cases where Report is ready to QA can be filtered by status"""
    Case.objects.create(organisation_name="Excluded")
    Case.objects.create(organisation_name="Included", report_review_status="yes")

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
    Case.objects.create(
        organisation_name="Included", psb_location=Case.PsbLocation.SCOTLAND
    )
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


@pytest.mark.parametrize(
    "filter_field_name",
    ["sent_to_enforcement_body_sent_date", "case_updated_date"],
)
def test_case_list_view_date_filters(filter_field_name, admin_client):
    """
    Test that the case list view page can be filtered by date range on a field.
    """
    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(
        included_case,
        filter_field_name,
        datetime(year=2021, month=6, day=5, tzinfo=ZoneInfo("UTC")),
    )
    included_case.save()
    excluded_case: Case = Case.objects.create(organisation_name="Excluded")
    setattr(
        excluded_case,
        filter_field_name,
        datetime(year=2021, month=5, day=5, tzinfo=ZoneInfo("UTC")),
    )
    excluded_case.save()

    url_parameters = f"date_type={filter_field_name}&date_start_0=1&date_start_1=6&date_start_2=2021&date_end_0=10&date_end_1=6&date_end_2=2021"
    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameters}"
    )

    assert response.status_code == 200
    assertContains(
        response, '<p class="govuk-body-m govuk-!-font-weight-bold">1 case found</p>'
    )
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


def test_case_list_view_audit_date_of_test_filters(admin_client):
    """
    Test that the case list view page can be filtered by date range on audit
    date of test.
    """
    included_audit_date_of_test: datetime = datetime(
        year=2021, month=6, day=5, tzinfo=ZoneInfo("UTC")
    )
    excluded_audit_date_of_test: datetime = datetime(
        year=2021, month=5, day=5, tzinfo=ZoneInfo("UTC")
    )
    included_case: Case = Case.objects.create(organisation_name="Included")
    excluded_case: Case = Case.objects.create(organisation_name="Excluded")
    Audit.objects.create(case=included_case, date_of_test=included_audit_date_of_test)
    Audit.objects.create(case=excluded_case, date_of_test=excluded_audit_date_of_test)

    url_parameters = "date_type=audit_case__date_of_test&date_start_0=1&date_start_1=6&date_start_2=2021&date_end_0=10&date_end_1=6&date_end_2=2021"
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


def test_case_export_list_view(admin_client):
    """Test that the case export list view returns csv data"""
    response: HttpResponse = admin_client.get(reverse("cases:case-export-list"))

    assert response.status_code == 200
    assertContains(response, case_columns_to_export_str)


@pytest.mark.parametrize(
    "export_view_name",
    [
        "cases:case-export-list",
        "cases:export-feedback-survey-cases",
    ],
)
def test_case_export_view_filters_by_search(export_view_name, admin_client):
    """
    Test that the case exports can be filtered by search from top menu
    """
    included_case: Case = Case.objects.create(
        organisation_name="Included", enforcement_body=Case.EnforcementBody.ECNI
    )
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
        ("cases:edit-case-metadata", "<b>Case metadata</b>"),
        ("cases:edit-test-results", "<li>Testing details</li>"),
        ("cases:edit-report-details", "<li>Report details</li>"),
        ("cases:edit-qa-comments", "<li>QA comments</li>"),
        ("cases:edit-report-approved", "<li>Report approved</li>"),
        ("cases:edit-publish-report", "<li>Publish report</li>"),
        (
            "cases:zendesk-tickets",
            '<h1 class="govuk-heading-xl amp-margin-bottom-15">PSB Zendesk tickets</h1>',
        ),
        ("cases:manage-contact-details", "<b>Manage contact details</b>"),
        ("cases:edit-request-contact-details", "<b>Request contact details</b>"),
        ("cases:edit-one-week-contact-details", "<b>One-week follow-up</b>"),
        ("cases:edit-four-week-contact-details", "<b>Four-week follow-up</b>"),
        ("cases:edit-report-sent-on", "<b>Report sent on</b>"),
        ("cases:edit-report-one-week-followup", "<b>One week follow-up</b>"),
        ("cases:edit-report-four-week-followup", "<b>Four week follow-up</b>"),
        ("cases:edit-report-acknowledged", "<b>Report acknowledged</b>"),
        ("cases:edit-12-week-update-requested", "<b>12-week update requested</b>"),
        (
            "cases:edit-12-week-one-week-followup-final",
            "<b>One week follow-up for final update</b>",
        ),
        (
            "cases:edit-12-week-update-request-ack",
            "<b>12-week update request acknowledged</b>",
        ),
        (
            "cases:outstanding-issues",
            '<h1 class="govuk-heading-xl amp-margin-bottom-15">Outstanding issues</h1>',
        ),
    ],
)
def test_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the case-specific view page loads"""
    case: Case = Case.objects.create(enable_correspondence_process=True)

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, expected_content, html=True)


def test_create_contact_page_loads(admin_client):
    """Test that the create Contact page loads"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-create", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        "<b>Add contact</b>",
        html=True,
    )


def test_update_contact_page_loads(admin_client):
    """Test that the update Contact page loads"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-update", kwargs={"pk": contact.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-15">Edit contact</h1>""",
        html=True,
    )


def test_create_zendesk_ticket_page_loads(admin_client):
    """Test that the create Zendesk ticket page loads"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:create-zendesk-ticket", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h1 class="govuk-heading-xl amp-margin-bottom-15">Add PSB Zendesk ticket</h1>',
        html=True,
    )


def test_update_zendesk_ticket_page_loads(admin_client):
    """Test that the update Zendesk ticket page loads"""
    case: Case = Case.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h1 class="govuk-heading-xl amp-margin-bottom-15">Edit PSB Zendesk ticket</h1>',
        html=True,
    )


def test_create_zendesk_ticket_view(admin_client):
    """Test that the create Zendesk ticket view works"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:create-zendesk-ticket", kwargs={"case_id": case.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(case=case).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event: Event = Event.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event.type == Event.Type.CREATE


def test_update_zendesk_ticket_view(admin_client):
    """Test that the update Zendesk ticket view works"""
    case: Case = Case.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("cases:update-zendesk-ticket", kwargs={"pk": zendesk_ticket.id}),
        {
            "url": ZENDESK_URL,
            "summary": ZENDESK_SUMMARY,
        },
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.filter(case=case).first()

    assert zendesk_ticket is not None
    assert zendesk_ticket.url == ZENDESK_URL
    assert zendesk_ticket.summary == ZENDESK_SUMMARY

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event: Event = Event.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event.type == Event.Type.UPDATE


def test_delete_zendesk_ticket_view(admin_client):
    """Test that the delete Zendesk ticket view works"""
    case: Case = Case.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    assert zendesk_ticket.is_deleted is False

    response: HttpResponse = admin_client.get(
        reverse("cases:delete-zendesk-ticket", kwargs={"pk": zendesk_ticket.id})
    )

    assert response.status_code == 302
    assert response.url == "/cases/1/zendesk-tickets/"

    zendesk_ticket_from_db: ZendeskTicket = ZendeskTicket.objects.get(
        id=zendesk_ticket.id
    )

    assert zendesk_ticket_from_db.is_deleted is True

    content_type: ContentType = ContentType.objects.get_for_model(ZendeskTicket)
    event: Event = Event.objects.get(
        content_type=content_type, object_id=zendesk_ticket.id
    )

    assert event.type == Event.Type.UPDATE


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
        ("save_continue_case", reverse("cases:edit-case-metadata", kwargs={"pk": 1})),
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
        ("save_continue_case", reverse("cases:edit-case-metadata", kwargs={"pk": 3})),
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
    assert case_event.event_type == CaseEvent.EventType.CREATE
    assert case_event.message == "Created case"


def test_updating_case_creates_case_event(admin_client):
    """
    Test that updating a case creates a case event
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-review-changes", kwargs={"pk": case.id}),
        {
            "is_ready_for_final_decision": "yes",
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.READY_FOR_FINAL_DECISION
    assert (
        case_event.message == "Case ready for final decision changed from 'No' to 'Yes'"
    )


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        ("cases:edit-case-metadata", "save", "cases:edit-case-metadata"),
        ("cases:edit-case-metadata", "save_continue", "cases:edit-test-results"),
        ("cases:edit-test-results", "save", "cases:edit-test-results"),
        ("cases:edit-test-results", "save_continue", "cases:edit-report-details"),
        ("cases:edit-report-details", "save", "cases:edit-report-details"),
        (
            "cases:edit-report-details",
            "save_continue",
            "cases:edit-qa-comments",
        ),
        ("cases:edit-qa-comments", "save", "cases:edit-qa-comments"),
        ("cases:edit-qa-comments", "save_continue", "cases:edit-report-approved"),
        ("cases:edit-report-approved", "save", "cases:edit-report-approved"),
        ("cases:edit-report-approved", "save_continue", "cases:edit-publish-report"),
        ("cases:edit-publish-report", "save", "cases:edit-publish-report"),
        (
            "cases:edit-publish-report",
            "save_continue",
            "cases:manage-contact-details",
        ),
        ("cases:manage-contact-details", "save", "cases:manage-contact-details"),
        (
            "cases:manage-contact-details",
            "save_continue",
            "cases:edit-report-sent-on",
        ),
        (
            "cases:edit-request-contact-details",
            "save",
            "cases:edit-request-contact-details",
        ),
        (
            "cases:edit-request-contact-details",
            "save_continue",
            "cases:edit-one-week-contact-details",
        ),
        (
            "cases:edit-one-week-contact-details",
            "save",
            "cases:edit-one-week-contact-details",
        ),
        (
            "cases:edit-one-week-contact-details",
            "save_continue",
            "cases:edit-four-week-contact-details",
        ),
        (
            "cases:edit-four-week-contact-details",
            "save",
            "cases:edit-four-week-contact-details",
        ),
        (
            "cases:edit-four-week-contact-details",
            "save_continue",
            "cases:edit-no-psb-response",
        ),
        ("cases:edit-no-psb-response", "save", "cases:edit-no-psb-response"),
        ("cases:edit-no-psb-response", "save_continue", "cases:edit-report-sent-on"),
        ("cases:edit-report-sent-on", "save", "cases:edit-report-sent-on"),
        (
            "cases:edit-report-sent-on",
            "save_continue",
            "cases:edit-report-one-week-followup",
        ),
        (
            "cases:edit-report-one-week-followup",
            "save",
            "cases:edit-report-one-week-followup",
        ),
        (
            "cases:edit-report-one-week-followup",
            "save_continue",
            "cases:edit-report-four-week-followup",
        ),
        (
            "cases:edit-report-four-week-followup",
            "save",
            "cases:edit-report-four-week-followup",
        ),
        (
            "cases:edit-report-four-week-followup",
            "save_continue",
            "cases:edit-report-acknowledged",
        ),
        ("cases:edit-report-acknowledged", "save", "cases:edit-report-acknowledged"),
        (
            "cases:edit-report-acknowledged",
            "save_continue",
            "cases:edit-12-week-update-requested",
        ),
        (
            "cases:edit-12-week-update-requested",
            "save",
            "cases:edit-12-week-update-requested",
        ),
        (
            "cases:edit-12-week-update-requested",
            "save_continue",
            "cases:edit-12-week-one-week-followup-final",
        ),
        (
            "cases:edit-12-week-one-week-followup-final",
            "save",
            "cases:edit-12-week-one-week-followup-final",
        ),
        (
            "cases:edit-12-week-one-week-followup-final",
            "save_continue",
            "cases:edit-12-week-update-request-ack",
        ),
        (
            "cases:edit-12-week-update-request-ack",
            "save",
            "cases:edit-12-week-update-request-ack",
        ),
        (
            "cases:edit-12-week-update-request-ack",
            "save_continue",
            "cases:edit-twelve-week-retest",
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
            "cases:edit-enforcement-recommendation",
        ),
        (
            "cases:edit-enforcement-recommendation",
            "save",
            "cases:edit-enforcement-recommendation",
        ),
        (
            "cases:edit-enforcement-recommendation",
            "save_continue",
            "cases:edit-case-close",
        ),
        ("cases:edit-case-close", "save", "cases:edit-case-close"),
        (
            "cases:edit-case-close",
            "save_continue",
            "cases:edit-statement-enforcement",
        ),
        (
            "cases:edit-statement-enforcement",
            "save",
            "cases:edit-statement-enforcement",
        ),
        (
            "cases:edit-statement-enforcement",
            "save_continue",
            "cases:edit-equality-body-metadata",
        ),
        (
            "cases:edit-equality-body-metadata",
            "save",
            "cases:edit-equality-body-metadata",
        ),
        (
            "cases:edit-equality-body-metadata",
            "save_continue",
            "cases:list-equality-body-correspondence",
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
            "case_completed": "no-decision",
            "version": case.version,
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}'


@pytest.mark.parametrize(
    "case_edit_path, expected_redirect_path",
    [
        ("cases:edit-case-close", "cases:edit-equality-body-metadata"),
        ("cases:edit-equality-body-metadata", "cases:legacy-end-of-case"),
    ],
)
def test_platform_update_redirects_based_on_case_variant(
    case_edit_path, expected_redirect_path, admin_client
):
    """
    Test that a case save and continue redirects as expected when case is not of the
    equality body close case variant.
    """
    case: Case = Case.objects.create(variant=Case.Variant.ARCHIVED)

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "case_completed": "no-decision",
            "version": case.version,
            "save_continue": "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == f'{reverse(expected_redirect_path, kwargs={"pk": case.id})}'


def test_qa_comments_creates_comment(admin_client, admin_user):
    """Test adding a comment using QA comments page"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-qa-comments", kwargs={"pk": case.id}),
        {
            "save": "Button value",
            "version": case.version,
            "body": QA_COMMENT_BODY,
        },
    )
    assert response.status_code == 302

    comment: Comment = Comment.objects.get(case=case)

    assert comment.body == QA_COMMENT_BODY
    assert comment.user == admin_user

    content_type: ContentType = ContentType.objects.get_for_model(Comment)
    event: Event = Event.objects.get(content_type=content_type, object_id=comment.id)

    assert event.type == Event.Type.CREATE


def test_qa_comments_does_not_create_comment(admin_client, admin_user):
    """Test QA comments page does not create a blank comment"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-qa-comments", kwargs={"pk": case.id}),
        {
            "save": "Button value",
            "version": case.version,
            "body": "",
        },
    )
    assert response.status_code == 302

    assert Comment.objects.filter(case=case).count() == 0


def test_no_contact_chaser_dates_set(
    admin_client,
):
    """
    Test that updating the no-contact email sent date populates chaser due dates
    """
    case: Case = Case.objects.create()

    assert case.no_contact_one_week_chaser_due_date is None
    assert case.no_contact_four_week_chaser_due_date is None

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-request-contact-details", kwargs={"pk": case.id}),
        {
            "seven_day_no_contact_email_sent_date_0": TODAY.day,
            "seven_day_no_contact_email_sent_date_1": TODAY.month,
            "seven_day_no_contact_email_sent_date_2": TODAY.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.no_contact_one_week_chaser_due_date is not None
    assert case_from_db.no_contact_four_week_chaser_due_date is not None


def test_link_to_accessibility_statement_displayed(admin_client):
    """
    Test that the link to the accessibility statement is displayed.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=Page.Type.STATEMENT, url=ACCESSIBILITY_STATEMENT_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:manage-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        f"""<p class="govuk-body-m">
            <a href="{ACCESSIBILITY_STATEMENT_URL}" target="_blank" class="govuk-link">
                Open accessibility statement page in new tab
            </a>
        </p>""",
        html=True,
    )


def test_statement_page_location_displayed(admin_client):
    """
    Test that the accessibility statement location is displayed.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.STATEMENT,
        url=ACCESSIBILITY_STATEMENT_URL,
        location=PAGE_LOCATION,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_contact_page_location_displayed(admin_client):
    """
    Test that the contact page location is displayed.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        page_type=Page.Type.CONTACT,
        url="https://example.com/contact",
        location=PAGE_LOCATION,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_link_to_accessibility_statement_not_displayed(admin_client):
    """
    Test that the link to the accessibility statement is not displayed
    if none has been entered
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:manage-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "No accessibility statement")


def test_updating_report_sent_date(admin_client):
    """Test that populating the report sent date populates the report followup due dates"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-sent-on", kwargs={"pk": case.id}),
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


def test_report_followup_due_dates_changed(admin_client):
    """
    Test that populating the report sent date updates existing report followup due dates
    """
    case: Case = Case.objects.create(
        report_followup_week_1_due_date=OTHER_DATE,
        report_followup_week_4_due_date=OTHER_DATE,
        report_followup_week_12_due_date=OTHER_DATE,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-sent-on", kwargs={"pk": case.id}),
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


def test_report_followup_due_dates_not_changed_if_report_sent_date_already_set(
    admin_client,
):
    """
    Test that updating the report sent date populates report followup due dates
    """
    case: Case = Case.objects.create(report_sent_date=OTHER_DATE)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-sent-on", kwargs={"pk": case.id}),
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


def test_twelve_week_1_week_chaser_due_date_updated(admin_client):
    """
    Test that updating the twelve week update requested date updates the
    twelve week 1 week chaser due date
    """
    case: Case = Case.objects.create(twelve_week_update_requested_date=OTHER_DATE)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-12-week-update-requested", kwargs={"pk": case.id}),
        {
            "twelve_week_update_requested_date_0": UPDATE_REQUESTED_DATE.day,
            "twelve_week_update_requested_date_1": UPDATE_REQUESTED_DATE.month,
            "twelve_week_update_requested_date_2": UPDATE_REQUESTED_DATE.year,
            "version": case.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert (
        case_from_db.twelve_week_1_week_chaser_due_date
        == UPDATE_REQUESTED_DATE + timedelta(days=ONE_WEEK_IN_DAYS)
    )


def test_case_report_one_week_followup_contains_followup_due_date(admin_client):
    """Test that the case report one week followup view contains the followup due date"""
    case: Case = Case.objects.create(
        report_followup_week_1_due_date=ONE_WEEK_FOLLOWUP_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(ONE_WEEK_FOLLOWUP_DUE_DATE)}",
    )


def test_case_report_one_week_followup_shows_warning_if_report_ack(admin_client):
    """
    Test that the case report one week followup view shows a warning if the report
    has been acknowledged
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, REPORT_ACKNOWLEDGED_WARNING)

    case.report_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-one-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, REPORT_ACKNOWLEDGED_WARNING)


def test_case_report_four_week_followup_contains_followup_due_date(admin_client):
    """Test that the case report four week followup view contains the followup due date"""
    case: Case = Case.objects.create(
        report_followup_week_4_due_date=FOUR_WEEK_FOLLOWUP_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(FOUR_WEEK_FOLLOWUP_DUE_DATE)}",
    )


def test_case_report_four_week_followup_shows_warning_if_report_ack(admin_client):
    """
    Test that the case report four week followup view shows a warning if the report
    has been acknowledged
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, REPORT_ACKNOWLEDGED_WARNING)

    case.report_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-report-four-week-followup", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, REPORT_ACKNOWLEDGED_WARNING)


def test_case_report_twelve_week_1_week_chaser_contains_followup_due_date(admin_client):
    """
    Test that the one week followup for final update view contains the one week chaser due date
    """
    case: Case = Case.objects.create(
        twelve_week_1_week_chaser_due_date=ONE_WEEK_CHASER_DUE_DATE,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-12-week-one-week-followup-final", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"Due {amp_format_date(ONE_WEEK_CHASER_DUE_DATE)}",
    )


def test_case_report_twelve_week_1_week_chaser_shows_warning_if_12_week_cores_ack(
    admin_client,
):
    """
    Test that the one week followup for final update view shows a warning if the 12-week
    correspondence has been acknowledged
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-12-week-one-week-followup-final", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING)

    case.twelve_week_correspondence_acknowledged_date = TODAY
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-12-week-one-week-followup-final", kwargs={"pk": case.id})
    )

    assert response.status_code == 200

    assertContains(response, TWELVE_WEEK_CORES_ACKNOWLEDGED_WARNING)


def test_no_psb_response_redirects_to_enforcement_recommendation(admin_client):
    """Test no PSB response redirects to enforcement recommendation"""
    case: Case = Case.objects.create(
        no_psb_contact=Boolean.YES,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-no-psb-response", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "no_psb_contact": "on",
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302
    assert (
        response.url
        == f'{reverse("cases:edit-enforcement-recommendation", kwargs={"pk": case.id})}'
    )


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


def test_audit_shows_link_to_create_audit_when_no_audit_exists(
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
    assertContains(response, "A test does not exist for this case")


def test_report_details_shows_when_no_report_exists(
    admin_client,
):
    """
    Test that report details shows when no report exists
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "A report does not exist for this case")


@pytest.mark.parametrize(
    "audit_table_row",
    [
        ("Preview report"),
        ("Notes"),
        ("View published HTML report"),
        ("Report views"),
        ("Unique visitors to report"),
    ],
)
def test_report_shows_expected_rows(admin_client, audit_table_row):
    """Test that audit details shows expected rows"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    Report.objects.create(case=case)
    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, audit_table_row)


@pytest.mark.parametrize(
    "flag_name, section_name, edit_url_name",
    [
        (
            "case_details_complete_date",
            "Case details > Case metadata",
            "edit-case-metadata",
        ),
        ("testing_details_complete_date", "Testing details", "edit-test-results"),
        ("reporting_details_complete_date", "Report details", "edit-report-details"),
        ("qa_auditor_complete_date", "Report approved", "edit-report-approved"),
        (
            "manage_contact_details_complete_date",
            "Contact details > Manage contact details",
            "manage-contact-details",
        ),
        (
            "request_contact_details_complete_date",
            "Contact details > Request contact details",
            "edit-request-contact-details",
        ),
        (
            "one_week_contact_details_complete_date",
            "Contact details > One-week follow-up",
            "edit-one-week-contact-details",
        ),
        (
            "four_week_contact_details_complete_date",
            "Contact details > Four-week follow-up",
            "edit-four-week-contact-details",
        ),
        (
            "report_sent_on_complete_date",
            "Report correspondence > Report sent on",
            "edit-report-sent-on",
        ),
        (
            "one_week_followup_complete_date",
            "Report correspondence > One week follow-up",
            "edit-report-one-week-followup",
        ),
        (
            "four_week_followup_complete_date",
            "Report correspondence > Four week follow-up",
            "edit-report-four-week-followup",
        ),
        (
            "report_acknowledged_complete_date",
            "Report correspondence > Report acknowledged",
            "edit-report-acknowledged",
        ),
        (
            "twelve_week_update_requested_complete_date",
            "12-week correspondence > 12-week update requested",
            "edit-12-week-update-requested",
        ),
        (
            "one_week_followup_final_complete_date",
            "12-week correspondence > One week follow-up for final update",
            "edit-12-week-one-week-followup-final",
        ),
        (
            "twelve_week_update_request_ack_complete_date",
            "12-week correspondence > 12-week update request acknowledged",
            "edit-12-week-update-request-ack",
        ),
        (
            "twelve_week_retest_complete_date",
            "12-week retest",
            "edit-twelve-week-retest",
        ),
        (
            "review_changes_complete_date",
            "Closing the case > Reviewing changes",
            "edit-review-changes",
        ),
        (
            "enforcement_recommendation_complete_date",
            "Closing the case > Enforcement recommendation",
            "edit-enforcement-recommendation",
        ),
        (
            "case_close_complete_date",
            "Closing the case > Closing the case",
            "edit-case-close",
        ),
    ],
)
def test_section_complete_check_displayed(
    flag_name, section_name, edit_url_name, admin_client
):
    """
    Test that the section complete tick is displayed in contents
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
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
            <a href="#{slugify(section_name)}" class="govuk-link govuk-link--no-visited-state">
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
    "flag_name, section_name, edit_url_name",
    [
        ("publish_report_complete_date", "Publish report", "edit-publish-report"),
    ],
)
def test_no_anchor_section_complete_check_displayed(
    flag_name, section_name, edit_url_name, admin_client
):
    """
    Test that the section complete tick is displayed in contents where there is no anchor
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
            {section_name}<span class="govuk-visually-hidden">complete</span>
            |
            <a id="{edit_url_name}" href="{edit_url}" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden">complete</span>
            </a>
            &check;
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "case_page_url",
    [
        "cases:edit-case-metadata",
        "cases:edit-test-results",
        "cases:edit-report-details",
        "cases:edit-qa-comments",
        "cases:edit-report-approved",
        "cases:edit-publish-report",
        "cases:manage-contact-details",
        "cases:edit-contact-create",
        "cases:edit-request-contact-details",
        "cases:edit-one-week-contact-details",
        "cases:edit-four-week-contact-details",
        # "cases:edit-no-psb-response",  Nav not in UI design
        "cases:edit-report-sent-on",
        "cases:edit-report-one-week-followup",
        "cases:edit-report-four-week-followup",
        "cases:edit-report-acknowledged",
        "cases:edit-12-week-update-requested",
        "cases:edit-12-week-one-week-followup-final",
        "cases:edit-12-week-update-request-ack",
        "cases:edit-twelve-week-retest",
        "cases:edit-review-changes",
        "cases:edit-enforcement-recommendation",
        "cases:edit-case-close",
        "cases:edit-post-case",
        "cases:status-workflow",
        "cases:outstanding-issues",
        "cases:edit-statement-enforcement",
        "cases:edit-equality-body-metadata",
        "cases:list-equality-body-correspondence",
        "cases:create-equality-body-correspondence",
        "cases:edit-retest-overview",
        "cases:legacy-end-of-case",
        "cases:zendesk-tickets",
        "cases:create-zendesk-ticket",
        # "cases:email-template-list",  Nav not in UI design
        # "cases:email-template-preview",  Nav not in UI design
    ],
)
def test_case_navigation_shown_on_case_pages(case_page_url, admin_client):
    """
    Test that the case navigation sections appear on all case pages
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)

    case_key: str = (
        "case_id"
        if case_page_url
        in [
            "cases:create-equality-body-correspondence",
            "cases:create-zendesk-ticket",
            "cases:edit-contact-create",
        ]
        else "pk"
    )

    response: HttpResponse = admin_client.get(
        reverse(case_page_url, kwargs={case_key: case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/5)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


def test_case_navigation_shown_on_edit_equality_body_cores_page(admin_client):
    """
    Test that the case navigation sections appear on edit equality
    body correspondence page
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/5)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


def test_case_navigation_shown_on_edit_contact_page(admin_client):
    """
    Test that the case navigation sections appear on edit contact page
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
    contact: Contact = Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:edit-contact-update",
            kwargs={"pk": contact.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/5)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


def test_case_navigation_shown_on_update_zendesk_ticket_page(admin_client):
    """
    Test that the case navigation sections appear on edit zendesk ticket page
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:update-zendesk-ticket",
            kwargs={"pk": zendesk_ticket.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, "Case details (0/1)", html=True)
    assertContains(response, "Contact details (0/5)", html=True)
    assertContains(response, "Report correspondence (0/4)", html=True)
    assertContains(response, "12-week correspondence (0/3)", html=True)
    assertContains(response, "Closing the case (0/3)", html=True)


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        ("cases:edit-test-results", "testing_details_complete_date", "Testing details"),
        (
            "cases:edit-report-details",
            "reporting_details_complete_date",
            "Report details",
        ),
        ("cases:edit-report-approved", "qa_auditor_complete_date", "Report approved"),
        ("cases:edit-publish-report", "publish_report_complete_date", "Publish report"),
        (
            "cases:edit-twelve-week-retest",
            "twelve_week_retest_complete_date",
            "12-week retest",
        ),
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


@pytest.mark.parametrize(
    "step_url, flag_name, step_name",
    [
        ("cases:edit-case-metadata", "case_details_complete_date", "Case metadata"),
        (
            "cases:edit-request-contact-details",
            "request_contact_details_complete_date",
            "Request contact details",
        ),
        (
            "cases:edit-one-week-contact-details",
            "one_week_contact_details_complete_date",
            "One-week follow-up",
        ),
        (
            "cases:edit-four-week-contact-details",
            "four_week_contact_details_complete_date",
            "Four-week follow-up",
        ),
        ("cases:edit-report-sent-on", "report_sent_on_complete_date", "Report sent on"),
        (
            "cases:edit-report-one-week-followup",
            "one_week_followup_complete_date",
            "One week follow-up",
        ),
        (
            "cases:edit-report-four-week-followup",
            "four_week_followup_complete_date",
            "Four week follow-up",
        ),
        (
            "cases:edit-report-acknowledged",
            "report_acknowledged_complete_date",
            "Report acknowledged",
        ),
        (
            "cases:edit-12-week-update-requested",
            "twelve_week_update_requested_complete_date",
            "12-week update requested",
        ),
        (
            "cases:edit-12-week-one-week-followup-final",
            "one_week_followup_final_complete_date",
            "One week follow-up for final update",
        ),
        (
            "cases:edit-12-week-update-request-ack",
            "twelve_week_update_request_ack_complete_date",
            "12-week update request acknowledged",
        ),
        (
            "cases:edit-review-changes",
            "review_changes_complete_date",
            "Reviewing changes",
        ),
        (
            "cases:edit-enforcement-recommendation",
            "enforcement_recommendation_complete_date",
            "Enforcement recommendation",
        ),
        ("cases:edit-case-close", "case_close_complete_date", "Closing the case"),
    ],
)
def test_section_complete_check_displayed_in_nav_details(
    step_url, flag_name, step_name, admin_client
):
    """
    Test that the section complete tick is displayed in list of steps
    when step is complete
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
    setattr(case, flag_name, TODAY)
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(step_url, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li><b>{step_name}</b>
                <span class="govuk-visually-hidden">complete</span> &check;
        </li>""",
        html=True,
    )


def test_manage_contact_details_page_complete_check_displayed_in_nav_details(
    admin_client,
):
    """
    Test that the Manage contact details complete tick is displayed in list of steps
    """
    case: Case = Case.objects.create(manage_contact_details_complete_date=TODAY)

    response: HttpResponse = admin_client.get(
        reverse("cases:manage-contact-details", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<li>
            <b>Manage contact details</b>
            <span class="govuk-visually-hidden">complete</span> &check;
            <ul class="amp-nav-list-subpages">
            </ul>
        </li>""",
        html=True,
    )


def test_add_contact_page_in_case_nav_when_current_page(
    admin_client,
):
    """
    Test that the add contact page appears in the case nav
    when it is the current page
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-create", kwargs={"case_id": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<li>
            <a href="/cases/1/manage-contact-details/" class="govuk-link govuk-link--no-visited-state">Manage contact details</a>
            <ul class="amp-nav-list-subpages">
                <li class="amp-nav-list-subpages amp-margin-top-5"><b>Add contact</b></li>
            </ul>
        </li>""",
        html=True,
    )


def test_twelve_week_retest_page_shows_link_to_create_test_page_if_none_found(
    admin_client,
):
    """
    Test that the twelve week retest page shows the link to the test results page
    when no test exists on the case.
    """
    case: Case = Case.objects.create()

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
    case: Case = Case.objects.create()
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
    case: Case = Case.objects.create()
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


def test_twelve_week_retest_page_shows_if_statement_exists(
    admin_client,
):
    """
    Test that the twelve week retest page shows if statement exists.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case, retest_date=date.today())

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__header amp-width-one-half">Statement exists</th>
            <td class="govuk-table__cell amp-width-one-half">No</td>
        </tr>""",
        html=True,
    )

    StatementPage.objects.create(
        audit=audit, added_stage=StatementPage.AddedStage.TWELVE_WEEK
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-twelve-week-retest", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<tr class="govuk-table__row">
            <th scope="row" class="govuk-table__header amp-width-one-half">Statement exists</th>
            <td class="govuk-table__cell amp-width-one-half">Yes</td>
        </tr>""",
        html=True,
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


def test_calculate_no_contact_chaser_dates():
    """
    Test that the no contact details chaser dates are calculated correctly.
    """
    case: Case = Case()
    seven_day_no_contact_email_sent_date: date = date(2020, 1, 1)

    updated_case = calculate_no_contact_chaser_dates(
        case=case,
        seven_day_no_contact_email_sent_date=seven_day_no_contact_email_sent_date,
    )

    assert updated_case.no_contact_one_week_chaser_due_date == date(2020, 1, 8)
    assert updated_case.no_contact_four_week_chaser_due_date == date(2020, 1, 29)


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


@pytest.mark.parametrize(
    "edit_link_label",
    [
        "edit-case-metadata",
        "edit-test-results",
        "edit-report-details",
        "edit-report-approved",
        "edit-publish-report",
        "edit-qa-comments",
        "manage-contact-details",
        "edit-twelve-week-retest",
        "edit-review-changes",
        "edit-case-close",
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


def test_status_change_message_shown(admin_client):
    """Test updating the case status causes a message to be shown on the next page"""
    user: User = User.objects.create()
    add_user_to_auditor_groups(user)

    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
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
def test_report_approved_notifies_auditor(rf):
    """
    Test approving the report on the Report approved page notifies the auditor
    when the report is approved.
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME, auditor=user)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.post(
        reverse("cases:edit-report-approved", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "report_approved_status": Case.ReportApprovedStatus.APPROVED,
            "save": "Button value",
        },
    )
    request.user = request_user

    response: HttpResponse = CaseReportApprovedUpdateView.as_view()(request, pk=case.id)

    assert response.status_code == 302

    task: Optional[Task] = Task.objects.filter(user=user).first()

    assert task is not None
    assert task.description == f"{request_user.get_full_name()} QA approved Case {case}"


@pytest.mark.django_db
def test_publish_report_no_report(admin_client):
    """
    Test publish report page when not ready to be published
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "To publish this report, you need to:")
    assertContains(response, "Set the report status to Ready to Review in")

    assertNotContains(response, "The report is approved and ready for publication.")
    assertNotContains(response, "Create HTML report")

    assertNotContains(response, "The report is now published and available for viewing")
    assertNotContains(response, "Save and continue")


@pytest.mark.django_db
def test_publish_report_first_time(admin_client):
    """
    Test publish report page when publishing report for first time
    """
    case: Case = Case.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(response, "To publish this report, you need to:")
    assertNotContains(response, "Set the report status to Ready to Review in")

    assertContains(response, "The report is approved and ready for publication.")
    assertContains(response, "Create HTML report")

    assertNotContains(response, "The report is now published and available for viewing")
    assertNotContains(response, "Save and continue")


@mock_aws
def test_publish_report(admin_client):
    """Test publishing a report"""
    case: Case = Case.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )
    Report.objects.create(case=case)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-publish-report", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "create_html_report": "Create HTML report",
        },
        follow=True,
    )

    assert response.status_code == 200

    assertContains(response, "The report is now published and available for viewing")


@pytest.mark.django_db
def test_publish_report_already_published(admin_client):
    """
    Test publish report page when report has already been published
    """
    case: Case = Case.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )
    Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-publish-report", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(response, "To publish this report, you need to:")
    assertNotContains(response, "Set the report status to Ready to Review in")

    assertNotContains(response, "The report is approved and ready for publication.")
    assertNotContains(response, "Create HTML report")

    assertContains(response, "The report is now published and available for viewing")
    assertContains(response, "Save and continue")


@pytest.mark.parametrize(
    "useful_link, edit_url_name",
    [
        ("zendesk_url", "edit-case-metadata"),
        ("trello_url", "manage-contact-details"),
        ("zendesk_url", "edit-test-results"),
        ("trello_url", "edit-report-details"),
        ("zendesk_url", "edit-review-changes"),
        ("zendesk_url", "edit-case-close"),
    ],
)
def test_frequently_used_links_displayed_in_edit(
    useful_link, edit_url_name, admin_client
):
    """
    Test that the frequently used links are displayed on all edit pages
    """
    case: Case = Case.objects.create(home_page_url="https://home_page_url.com")
    setattr(case, useful_link, f"https://{useful_link}.com")
    case.save()
    psb_zendesk_url: str = reverse("cases:zendesk-tickets", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse(f"cases:{edit_url_name}", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{psb_zendesk_url}" class="govuk-link govuk-link--no-visited-state">
                PSB Zendesk tickets
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
        reverse("cases:edit-report-details", kwargs={"pk": case.id}),
        {
            "version": case.version,
            "reporting_details_complete_date": "on",
            "save": "Button value",
        },
    )
    assert response.status_code == 302

    content_type: ContentType = ContentType.objects.get_for_model(Case)
    event: Event = Event.objects.get(content_type=content_type, object_id=case.id)

    assert event.type == Event.Type.UPDATE


def test_update_case_checks_version(admin_client):
    """Test that updating a case shows an error if the version of the case has changed"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-report-details", kwargs={"pk": case.id}),
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
        "edit-case-metadata",
        "edit-test-results",
        "edit-report-details",
        "edit-report-approved",
        "edit-publish-report",
        "edit-qa-comments",
        "manage-contact-details",
        "edit-twelve-week-retest",
        "edit-review-changes",
        "edit-case-close",
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
    case: Case = create_case_and_compliance(
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
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
            <a href="{reverse('cases:edit-case-metadata', kwargs=case_pk_kwargs)}"
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
            <a href="{reverse('cases:edit-case-metadata', kwargs=case_pk_kwargs)}"
                class="govuk-link govuk-link--no-visited-state">
                Assign an auditor</a>&check;</li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name,label,field_name,field_value",
    [
        (
            "cases:edit-no-psb-response",
            "No response from PSB",
            "no_psb_contact",
            Boolean.YES,
        ),
        (
            "cases:edit-review-changes",
            "Is this case ready for final decision? needs to be Yes",
            "is_ready_for_final_decision",
            Boolean.YES,
        ),
        (
            "cases:edit-case-close",
            "Case completed requires a decision",
            "case_completed",
            Case.CaseCompleted.COMPLETE_SEND,
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


def test_status_workflow_links_to_statement_overview(admin_client, admin_user):
    """
    Test that the status workflow page provides a link to the statement overview
    page when the case test uses statement checks. Checkmark set when overview
    statement checks have been entered.
    """
    case: Case = Case.objects.create()
    case_pk_kwargs: Dict[str, int] = {"pk": case.id}
    audit: Audit = Audit.objects.create(case=case)
    audit_pk_kwargs: Dict[str, int] = {"pk": audit.id}

    for statement_check in StatementCheck.objects.all():
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    overview_url: str = reverse(
        "audits:edit-statement-overview", kwargs=audit_pk_kwargs
    )
    assertContains(
        response,
        f"""<li>
            <a href="{overview_url}" class="govuk-link govuk-link--no-visited-state">
                Statement overview not filled in
            </a></li>""",
        html=True,
    )

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:status-workflow", kwargs=case_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<li>
            <a href="{overview_url}" class="govuk-link govuk-link--no-visited-state">
                Statement overview not filled in
            </a>&check;</li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "nav_link_name,nav_link_label",
    [
        (
            "cases:edit-test-results",
            "Testing details",
        ),
        (
            "cases:edit-report-details",
            "Report details",
        ),
        (
            "cases:edit-report-approved",
            "Report approved",
        ),
        (
            "cases:edit-publish-report",
            "Publish report",
        ),
        (
            "cases:edit-qa-comments",
            "QA comments",
        ),
        ("cases:manage-contact-details", "Manage contact details"),
        (
            "cases:edit-request-contact-details",
            "Request contact details",
        ),
        (
            "cases:edit-one-week-contact-details",
            "One-week follow-up",
        ),
        (
            "cases:edit-four-week-contact-details",
            "Four-week follow-up",
        ),
        ("cases:edit-report-sent-on", "Report sent on"),
        (
            "cases:edit-report-one-week-followup",
            "One week follow-up",
        ),
        (
            "cases:edit-report-four-week-followup",
            "Four week follow-up",
        ),
        (
            "cases:edit-report-acknowledged",
            "Report acknowledged",
        ),
        (
            "cases:edit-12-week-update-requested",
            "12-week update requested",
        ),
        (
            "cases:edit-12-week-one-week-followup-final",
            "One week follow-up for final update",
        ),
        (
            "cases:edit-12-week-update-request-ack",
            "12-week update request acknowledged",
        ),
        (
            "cases:edit-twelve-week-retest",
            "12-week retest",
        ),
        (
            "cases:edit-review-changes",
            "Reviewing changes",
        ),
    ],
)
def test_navigation_links_shown(
    nav_link_name,
    nav_link_label,
    admin_client,
):
    """
    Test case steps' navigation links are shown
    """
    case: Case = Case.objects.create(enable_correspondence_process=True)
    nav_link_url: str = reverse(nav_link_name, kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{nav_link_url}" class="govuk-link govuk-link--no-visited-state">{nav_link_label}</a>""",
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
        response, """<h2 id="wcag-77" class="govuk-heading-l">Axe WCAG</h2>"""
    )

    response: HttpResponse = admin_client.get(f"{url}?view=WCAG+view")

    assert response.status_code == 200

    assertNotContains(response, "Group by WCAG error")
    assertContains(response, "Group by page")
    assertNotContains(response, """<h2 id="page-2" class="govuk-heading-l">Home</h2>""")
    assertContains(
        response, """<h2 id="wcag-77" class="govuk-heading-l">Axe WCAG</h2>"""
    )

    response: HttpResponse = admin_client.get(f"{url}?view=Page+view")

    assert response.status_code == 200

    assertContains(response, "Group by WCAG error")
    assertNotContains(response, "Group by page")
    assertContains(response, """<h2 id="page-2" class="govuk-heading-l">Home</h2>""")
    assertNotContains(
        response, """<h2 id="wcag-77" class="govuk-heading-l">Axe WCAG</h2>"""
    )


def test_outstanding_issues_overview(admin_client):
    """
    Test out standing issues page shows overview.
    """
    audit: Audit = create_audit_and_check_results()
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": audit.case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "WCAG errors: 0 of 3 fixed (0%)", html=True)
    assertContains(response, "Statement errors: 0 of 12 fixed (0%)", html=True)


def test_outstanding_issues_overview_percentage(admin_client):
    """
    Test out standing issues page shows overview percentages calculated
    correctly.
    """
    audit: Audit = create_audit_and_check_results()
    audit.archive_audit_retest_scope_state = Audit.Scope.PRESENT
    audit.save()
    home_page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    check_result: CheckResult = home_page.all_check_results[0]
    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": audit.case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "WCAG errors: 1 of 3 fixed (33%)", html=True)
    assertContains(response, "Statement errors: 1 of 12 fixed (8%)", html=True)


def test_outstanding_issues_new_case(admin_client):
    """
    Test out standing issues page shows placeholder text for case without audit
    """
    case: Case = Case.objects.create()
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "This is a new case and does not have any test data.")


@pytest.mark.parametrize(
    "type, label",
    [
        ("overview", "Statement overview"),
        ("website", "Statement information"),
        ("compliance", "Compliance status"),
        ("non-accessible", "Non-accessible content overview"),
        ("preparation", "Preparation"),
        ("feedback", "Feedback and enforcement procedure"),
        ("custom", "Custom statement issues"),
    ],
)
def test_outstanding_issues_statement_checks(type, label, admin_client):
    """Test that outstanding issues shows expected statement checks"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    statement_check: StatementCheck = StatementCheck.objects.filter(type=type).first()
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=type,
        statement_check=statement_check,
    )
    edit_url: str = f"edit-retest-statement-{type}"
    url: str = reverse("cases:outstanding-issues", kwargs={"pk": case.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertNotContains(response, f"{label}</h2>")
    assertNotContains(response, edit_url)

    statement_check_result.check_result_state = StatementCheckResult.Result.NO
    statement_check_result.save()

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertContains(response, f"{label}</h2>")
    assertContains(response, edit_url)

    statement_check_result.retest_state = StatementCheckResult.Result.YES
    statement_check_result.save()

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertNotContains(response, f"{label}</h2>")
    assertNotContains(response, edit_url)


@pytest.mark.parametrize(
    "url_name",
    ["cases:case-detail", "cases:edit-case-metadata"],
)
def test_frequently_used_links_displayed(url_name, admin_client):
    """
    Test that the frequently used links are displayed
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Frequently used links")
    assertContains(response, "View outstanding issues")
    assertContains(response, "Email templates")
    assertContains(response, "View website")


def test_twelve_week_email_template_contains_issues(admin_client):
    """
    Test twelve week email template contains issues.
    """
    audit: Audit = create_audit_and_check_results()
    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.HOME)
    page.url = "https://example.com"
    page.save()
    Report.objects.create(case=audit.case)
    email_template: EmailTemplate = EmailTemplate.objects.get(
        slug=EmailTemplate.Slug.TWELVE_WEEK_REQUEST
    )
    url: str = reverse(
        "cases:email-template-preview",
        kwargs={"case_id": audit.case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, ERROR_NOTES)


def test_twelve_week_email_template_contains_no_issues(admin_client):
    """
    Test twelve week email template with no issues contains placeholder text.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    email_template: EmailTemplate = EmailTemplate.objects.get(
        slug=EmailTemplate.Slug.TWELVE_WEEK_REQUEST
    )
    url: str = reverse(
        "cases:email-template-preview",
        kwargs={"case_id": audit.case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "We found no major issues.")


def test_outstanding_issues_are_unfixed_in_email_template_context(admin_client):
    """
    Test outstanding issues (issues_table) contains only unfixed issues
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        notes=OUTSTANDING_ISSUE_NOTES,
    )

    email_template: EmailTemplate = EmailTemplate.objects.create(
        template="{{ issues_tables.0.rows.0.cell_content_2 }}",
        created_by=user,
        updated_by=user,
    )
    url: str = reverse(
        "cases:email-template-preview",
        kwargs={"case_id": audit.case.id, "pk": email_template.id},
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, OUTSTANDING_ISSUE_NOTES)

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertNotContains(response, OUTSTANDING_ISSUE_NOTES)


def test_equality_body_correspondence(admin_client):
    """
    Test equality body correspondence page renders according to URL parameters.
    """
    case: Case = Case.objects.create()
    EqualityBodyCorrespondence.objects.create(
        case=case,
        message=RESOLVED_EQUALITY_BODY_MESSAGE,
        notes=RESOLVED_EQUALITY_BODY_NOTES,
        status=EqualityBodyCorrespondence.Status.RESOLVED,
    )
    EqualityBodyCorrespondence.objects.create(
        case=case,
        message=UNRESOLVED_EQUALITY_BODY_MESSAGE,
        notes=UNRESOLVED_EQUALITY_BODY_NOTES,
    )
    url: str = reverse(
        "cases:list-equality-body-correspondence", kwargs={"pk": case.id}
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, RESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, RESOLVED_EQUALITY_BODY_NOTES)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_NOTES)

    response: HttpResponse = admin_client.get(f"{url}?view=unresolved")

    assert response.status_code == 200

    assertNotContains(response, RESOLVED_EQUALITY_BODY_MESSAGE)
    assertNotContains(response, RESOLVED_EQUALITY_BODY_NOTES)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_MESSAGE)
    assertContains(response, UNRESOLVED_EQUALITY_BODY_NOTES)


def test_equality_body_correspondence_status_toggle(admin_client):
    """
    Test equality body correspondence page buttons toggles the status
    """
    case: Case = Case.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case,
            message=UNRESOLVED_EQUALITY_BODY_MESSAGE,
            notes=UNRESOLVED_EQUALITY_BODY_NOTES,
        )
    )

    assert (
        equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.UNRESOLVED
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:list-equality-body-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            f"toggle_status_{equality_body_correspondence.id}": "Mark as resolved",
        },
    )

    assert response.status_code == 302

    updated_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(id=equality_body_correspondence.id)
    )

    assert (
        updated_equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.RESOLVED
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:list-equality-body-correspondence", kwargs={"pk": case.id}),
        {
            "version": case.version,
            f"toggle_status_{equality_body_correspondence.id}": "Mark as resolved",
        },
    )

    assert response.status_code == 302

    updated_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(id=equality_body_correspondence.id)
    )

    assert (
        updated_equality_body_correspondence.status
        == EqualityBodyCorrespondence.Status.UNRESOLVED
    )


def test_create_equality_body_correspondence_save_return_redirects(admin_client):
    """
    Test that a successful equality body correspondence create redirects
    to list when save_return button pressed
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:create-equality-body-correspondence", kwargs={"case_id": case.id}
        ),
        {
            "save_return": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "cases:list-equality-body-correspondence", kwargs={"pk": case.id}
    )


def test_create_equality_body_correspondence_save_redirects(admin_client):
    """
    Test that a successful equality body correspondence create redirects
    to update page when save button pressed
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:create-equality-body-correspondence", kwargs={"case_id": case.id}
        ),
        {
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.get(case=case)
    )

    assert response.url == reverse(
        "cases:edit-equality-body-correspondence",
        kwargs={"pk": equality_body_correspondence.id},
    )


def test_update_equality_body_correspondence_save_return_redirects(admin_client):
    """
    Test that a successful equality body correspondence update redirects
    to list when save_return button pressed
    """
    case: Case = Case.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
        {
            "save_return": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "cases:list-equality-body-correspondence", kwargs={"pk": case.id}
    )


def test_update_equality_body_correspondence_save_redirects(admin_client):
    """
    Test that a successful equality body correspondence update redirects
    to itself when save button pressed
    """
    case: Case = Case.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:edit-equality-body-correspondence",
            kwargs={"pk": equality_body_correspondence.id},
        ),
        {
            "save": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "cases:edit-equality-body-correspondence",
        kwargs={"pk": equality_body_correspondence.id},
    )


def test_updating_equality_body_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the equality body updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: Case = Case.objects.create(home_page_url="https://example.com")
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "enforcement_body": Case.EnforcementBody.ECNI,
            "version": case.version,
            "save": "Button value",
            "home_page_url": "https://example.com",
        },
    )
    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_updating_home_page_url_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the home page URL updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: Case = Case.objects.create(home_page_url="https://example.com")
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "home_page_url": "https://example.com/updated",
            "version": case.version,
            "save": "Button value",
            "enforcement_body": Case.EnforcementBody.ECNI,
        },
    )
    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_updating_organisation_name_updates_published_report_data_updated_time(
    admin_client,
):
    """
    Test that updating the organisation name updates the published report data updated
    time (so a notification banner to republish the report is shown).
    """
    case: Case = Case.objects.create(home_page_url="https://example.com")
    audit: Audit = Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    assert audit.published_report_data_updated_time is None

    response: HttpResponse = admin_client.post(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
        {
            "organisation_name": "New name",
            "version": case.version,
            "save": "Button value",
            "home_page_url": "https://example.com",
            "enforcement_body": Case.EnforcementBody.ECNI,
        },
    )

    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.published_report_data_updated_time is not None


def test_case_close(admin_client):
    """
    Test that case close renders as expected:
    """
    case: Case = Case.objects.create(
        home_page_url=HOME_PAGE_URL, recommendation_notes=f"* {RECOMMENDATION_NOTE}"
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    # Required columns labelled as such; Missing data labelled as incomplete
    assertContains(response, "Published report | Required and incomplete", html=True)

    # Required data with default value labelled as incomplete
    assertContains(
        response,
        "Initial Accessibility Statement Decision | Required and incomplete",
        html=True,
    )

    # URL data rendered as link
    assertContains(
        response,
        f"""<a href="{HOME_PAGE_URL}"
            class="govuk-link" target="_blank">
            {HOME_PAGE_URL}</a>""",
        html=True,
    )

    # Edit link label used
    assertContains(
        response,
        """<a href="/cases/1/manage-contact-details/"
            class="govuk-link govuk-link--no-visited-state">
            Go to contact details</a>""",
        html=True,
    )

    # Markdown data rendered as html
    assertContains(response, f"<li>{RECOMMENDATION_NOTE}</li>")

    # Extra label for percentage shown
    assertContains(response, "(Derived from retest results)")


def test_case_close_missing_data(admin_client):
    """
    Test that case close renders as expected when data is missing
    """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertNotContains(
        response, "All fields are complete and the case can now be closed."
    )

    assertContains(
        response,
        """<li>
            Organisation is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-case-metadata/#id_organisation_name-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Organisation</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Website URL is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-case-metadata/#id_home_page_url-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Website URL</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        "<li>Published report is missing</li>",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Enforcement recommendation is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_recommendation_for_enforcement-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Enforcement recommendation</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Enforcement recommendation notes including exemptions is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_recommendation_notes-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Enforcement recommendation notes including exemptions</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
            Date when compliance decision email sent to public sector body is missing
            <span class="amp-nowrap">(<a href="/cases/1/edit-enforcement-recommendation/#id_compliance_email_sent_date-label" class="govuk-link govuk-link--no-visited-state">
                Edit<span class="govuk-visually-hidden"> Date when compliance decision email sent to public sector body</span></a>)</span>
        </li>""",
        html=True,
    )
    assertContains(
        response,
        "<li>Initial Accessibility Statement Decision is missing</li>",
        html=True,
    )


def test_case_close_no_missing_data(admin_client):
    """
    Test that case close renders as expected when no data is missing
    """
    case: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=HOME_PAGE_URL,
        recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION,
        recommendation_notes=RECOMMENDATION_NOTE,
        compliance_email_sent_date=date.today(),
    )
    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    case.compliance.save()
    Audit.objects.create(
        case=case,
        initial_disproportionate_burden_claim=Audit.DisproportionateBurden.NO_CLAIM,
    )
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-case-close", kwargs={"pk": case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response, "The case has missing data and can not be submitted to EHRC."
    )
    assertContains(response, "All fields are complete and the case can now be closed.")


def test_case_overview(admin_client):
    """Test case overview."""
    audit: Audit = create_audit_and_check_results()
    accessibility_statement_page: Page = audit.accessibility_statement_page
    accessibility_statement_page.url = "https://example.com"
    accessibility_statement_page.retest_page_missing_date = TODAY
    accessibility_statement_page.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": audit.case.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-10">Initial test: 3</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-10">Retest: 3 (0% fixed) (1 deleted page)</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-10">Initial test: 12</p>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-m amp-margin-bottom-10">Retest test: No statement found</p>""",
        html=True,
    )


def test_case_email_template_list_view(admin_client):
    """Test case email template list page is rendered"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:email-template-list", kwargs={"case_id": case.id})
    )

    assert response.status_code == 200

    assertContains(response, ">Email templates</h1>")


def test_case_email_template_preview_view(admin_client):
    """Test case email template list page is rendered"""
    case: Case = Case.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.get(
        pk=EXAMPLE_EMAIL_TEMPLATE_ID
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:email-template-preview",
            kwargs={"case_id": case.id, "pk": email_template.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, f">{email_template.name}</h1>")


def test_zendesk_tickets_shown(admin_client):
    """
    Test Zendesk tickets shown in correspondence overview.
    """
    case: Case = Case.objects.create()
    ZendeskTicket.objects.create(case=case, summary=ZENDESK_SUMMARY)

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:edit-request-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, ZENDESK_SUMMARY)


def test_enable_correspondence_process(admin_client):
    """Test enabling of correspondence process"""
    case: Case = Case.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:enable-correspondence-process",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "cases:edit-request-contact-details",
        kwargs={"pk": case.id},
    )

    case_from_db: Case = Case.objects.get(id=case.id)

    assert case_from_db.enable_correspondence_process is True


def test_enabling_correspondence_process(admin_client):
    """Test enabling of correspondence process pages"""
    case: Case = Case.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:manage-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    for url, label in CORRESPONDENCE_PROCESS_PAGES:
        assertNotContains(
            response,
            f"""<a href="/cases/1/{url}/"
                class="govuk-link govuk-link--no-visited-state">
                {label}</a>""",
            html=True,
        )

    case.enable_correspondence_process = True
    case.save()

    response: HttpResponse = admin_client.get(
        reverse(
            "cases:manage-contact-details",
            kwargs={"pk": case.id},
        )
    )

    assert response.status_code == 200

    for url, label in CORRESPONDENCE_PROCESS_PAGES:
        assertContains(
            response,
            f"""<a href="/cases/1/{url}/"
                class="govuk-link govuk-link--no-visited-state">
                {label}</a>""",
            html=True,
        )


def test_add_contact_details_redirects_correctly(admin_client):
    """
    Test add contact details page redirects based on
    enable_correspondence_process value
    """
    case: Case = Case.objects.create()

    assert case.enable_correspondence_process is False

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:manage-contact-details",
            kwargs={"pk": case.id},
        ),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "cases:edit-report-sent-on",
        kwargs={"pk": case.id},
    )

    case.enable_correspondence_process = True
    case.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "cases:manage-contact-details",
            kwargs={"pk": case.id},
        ),
        {
            "version": case.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "cases:edit-request-contact-details",
        kwargs={"pk": case.id},
    )
