"""
Tests for common views
"""

import logging
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
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
from ...detailed.models import DetailedCase
from ...notifications.models import Task
from ...reports.models import Report, ReportVisitsMetrics
from ...s3_read_write.models import S3Report
from ...simplified.models import CaseCompliance, SimplifiedCase
from ...simplified.utils import create_case_and_compliance
from ...users.tests.test_views import VALID_PASSWORD, VALID_USER_EMAIL, create_user
from ..models import FooterLink, FrequentlyUsedLink, Platform
from ..utils import get_platform_settings

NOT_FOUND_DOMAIN: str = "not-found"
FOUND_DOMAIN: str = "found"
EMAIL_SUBJECT: str = "Email subject"
EMAIL_MESSAGE: str = "Email message"
ISSUE_REPORT_LINK: str = """<a class="govuk-footer__link" href="/common/report-issue/?page_url=/&page_title=Your simplified cases"
target="_blank">Report an issue</a>"""
METRIC_OVER_LAST_30_DAYS: str = """<p id="{metric_id}" class="govuk-body-m">
    <span class="govuk-!-font-size-48"><b>{number_last_30_days}</b></span>
    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg alt="Up arrow" version="1.1" viewBox="-10 0 36.936421 40.000004" id="svg870" width="36.93642" height="40.000004"
        xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
        <defs id="defs874" />
        <g transform="matrix(0,-0.02890173,-0.02890173,0,16.661851,42.167634)" id="g868" style="stroke-width:34.6">
            <path
                fill="currentColor"
                d="M 1113,284 763,-66 H 442 L 676,168 H 75 V 400 H 676 L 442,633 h 321 z"
                id="path866"
                style="stroke-width:897.871" />
        </g>
    </svg>
    {progress_percentage}% over previous 30 days ({number_previous_30_days} {lowercase_label})
</p>"""
METRIC_UNDER_LAST_30_DAYS: str = """<p id="{metric_id}" class="govuk-body-m">
    <span class="govuk-!-font-size-48"><b>{number_last_30_days}</b></span>
    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg alt="Down arrow" version="1.1" viewBox="-10 0 36.936421 40.000004" id="svg870" width="36.93642" height="40.000004"
        xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
        <defs id="defs874" />
            <g transform="matrix(0,0.02890173,0.02890173,0,0.27456977,7.8323783)"
                id="g868" style="stroke-width:34.6">
                    <path
                        fill="currentColor"
                        d="M 1113,284 763,-66 H 442 L 676,168 H 75 V 400 H 676 L 442,633 h 321 z"
                        id="path866"
                        style="stroke-width:897.871" />
        </g>
    </svg>
    {progress_percentage}% under previous 30 days ({number_previous_30_days} {lowercase_label})
</p>"""
METRIC_YEARLY_TABLE: str = """<table id="{table_id}" class="govuk-table">
    <thead class="govuk-table__head">
        <tr class="govuk-table__row">
            <th scope="col" class="govuk-table__header">Month</th>
            <th scope="col" class="govuk-table__header govuk-table__header--numeric">{column_header}</th>
        </tr>
    </thead>
    <tbody class="govuk-table__body">
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">January 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">February 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">March 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">April 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">May 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">June 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">July 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">August 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">September 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">October 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">0</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">November 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">1</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">December 2021</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">2</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">January 2022</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">1</td>
            </tr>
            <tr class="govuk-table__row">
                <td class="govuk-table__cell">Total</td>
                <td class="govuk-table__cell govuk-table__cell--numeric">4</td>
            </tr>
    </tbody>
</table>"""
POLICY_PROGRESS_METRIC: str = """<p id="{id}" class="govuk-body-m">
    <span class="govuk-!-font-size-48 amp-padding-right-20"><b>{percentage}%</b></span>
    {partial_count} out of {total_count}
</p>"""
ACCEPTABLE_WEBSITES_ROW: str = """<tr class="govuk-table__row">
    <td class="govuk-table__cell">December 2021</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">4</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">1</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">2</td>
</tr>"""
COMPLIANT_STATEMENTS_ROW: str = """<tr class="govuk-table__row">
    <td class="govuk-table__cell">December 2021</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">4</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">1</td>
    <td class="govuk-table__cell govuk-table__cell--numeric">2</td>
</tr>"""
LINK_LABEL: str = "Custom frequently used link"
LINK_URL: str = "https://example.com/custom-link"
FOOTER_LINK_LABEL: str = "Custom footer link"
FOOTER_LINK_URL: str = "https://example.com/footer-link"
LOG_MESSAGE: str = "Hello"


@pytest.mark.parametrize(
    "url_name,expected_header",
    [
        ("common:bulk-url-search", "Bulk URL search"),
        ("common:contact-admin", "Contact admin"),
        ("common:edit-active-qa-auditor", ">Active QA auditor</h1>"),
        ("common:platform-history", ">Platform version history</h1>"),
        ("common:issue-report", ">Report an issue</h1>"),
        ("common:platform-checking", ">Tools and sitemap</h1>"),
        ("common:accessibility-statement", ">Accessibility statement</h1>"),
        ("common:privacy-notice", ">Privacy notice</h1>"),
        ("common:markdown-cheatsheet", ">Markdown cheatsheet</h1>"),
        ("common:more-information", "More information about monitoring"),
        ("common:metrics-case", ">Case metrics</h1>"),
        ("common:metrics-policy", ">Policy metrics</h1>"),
        ("common:metrics-report", ">Report metrics</h1>"),
    ],
)
def test_page_renders(url_name, expected_header, admin_client):
    """Test common page is rendered"""
    response: HttpResponse = admin_client.get(reverse(url_name))

    assert response.status_code == 200
    assertContains(response, expected_header)


def test_bulk_url_search_works(admin_client):
    """
    Test that submitting the bulk URL search form redisplays page
    with results of search.
    """
    SimplifiedCase.objects.create(home_page_url=f"https://{FOUND_DOMAIN}.com")

    response: HttpResponse = admin_client.post(
        reverse("common:bulk-url-search"),
        {
            "urls": f"https://{NOT_FOUND_DOMAIN}.com\nhttps://{FOUND_DOMAIN}.com",
            "submit": "Search",
        },
    )
    assert response.status_code == 200
    assertContains(
        response, f"<li>https://{NOT_FOUND_DOMAIN}.com ({NOT_FOUND_DOMAIN})</li>"
    )
    assertContains(
        response,
        f"""<li>
            https://{FOUND_DOMAIN}.com
            (<a href="/cases/?search={FOUND_DOMAIN}" target="_blank" class="govuk-link govuk-link--no-visited-state">{FOUND_DOMAIN}</a>)
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "subject,message",
    [
        (EMAIL_SUBJECT, EMAIL_MESSAGE),
        ("", ""),
        (EMAIL_SUBJECT, ""),
        ("", EMAIL_MESSAGE),
    ],
)
def test_contact_admin_page_sends_email(subject, message, admin_client, mailoutbox):
    """Test contact admin messages are emailed if message or subject entered"""
    response: HttpResponse = admin_client.post(
        reverse("common:contact-admin"),
        {
            "subject": subject,
            "message": message,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard:home")

    if subject or message:
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.subject == subject
        assert email.body == message
        assert email.from_email == "admin@example.com"
        assert email.to == [settings.CONTACT_ADMIN_EMAIL]
    else:
        assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_view_accessibility_statement(client):
    """Test accessibility statement renders. No login required"""
    platform: Platform = get_platform_settings()
    platform.platform_accessibility_statement = "# Accessibility statement header"
    platform.save()

    response: HttpResponse = client.get(reverse("common:accessibility-statement"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Accessibility statement header</h1>""",
        html=True,
    )


@pytest.mark.django_db
def test_view_privacy_notice(client):
    """Test privacy notice renders. No login required."""
    platform: Platform = get_platform_settings()
    platform.platform_privacy_notice = "# Privacy notice header"
    platform.save()

    response: HttpResponse = client.get(reverse("common:privacy-notice"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Privacy notice header</h1>""",
        html=True,
    )


@pytest.mark.parametrize(
    "prototype_name,issue_report_link_expected",
    [
        ("", True),
        ("TEST", True),
        ("anything-else", False),
    ],
)
def test_issue_report_link(prototype_name, issue_report_link_expected, admin_client):
    """
    Test issue report link is rendered on live and test platforms
    but not on prototypes.
    """
    settings.AMP_PROTOTYPE_NAME = prototype_name
    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    if issue_report_link_expected:
        assertContains(response, ISSUE_REPORT_LINK, html=True)
    else:
        assertNotContains(response, ISSUE_REPORT_LINK, html=True)


@pytest.mark.parametrize(
    "case_field, metric_id, lowercase_label",
    [
        ("reporting_details_complete_date", "tests-completed", "tests completed"),
        ("report_sent_date", "reports-sent", "reports sent"),
        ("completed_date", "cases-closed", "cases closed"),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_case_progress_metric_over(
    mock_date, mock_timezone, case_field, metric_id, lowercase_label, admin_client
):
    """
    Test case progress metric, which is over in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 10, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 10)

    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 11, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 16, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2022, 1, 1, tzinfo=timezone.utc)}
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_OVER_LAST_30_DAYS.format(
            metric_id=metric_id,
            number_last_30_days=2,
            progress_percentage=100,
            number_previous_30_days=1,
            lowercase_label=lowercase_label,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_case_created_progress_metric_over(mock_date, mock_timezone, admin_client):
    """
    Test case progress metric, which is over in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 10, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 10)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 11, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 16, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2022, 1, 1, tzinfo=timezone.utc)
    simplified_case.save()

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_OVER_LAST_30_DAYS.format(
            metric_id="cases-created",
            number_last_30_days=2,
            progress_percentage=100,
            number_previous_30_days=1,
            lowercase_label="cases created",
        ),
        html=True,
    )


@pytest.mark.parametrize(
    "case_field, metric_id, lowercase_label",
    [
        ("reporting_details_complete_date", "tests-completed", "tests completed"),
        ("report_sent_date", "reports-sent", "reports sent"),
        ("completed_date", "cases-closed", "cases closed"),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_case_progress_metric_under(
    mock_date, mock_timezone, case_field, metric_id, lowercase_label, admin_client
):
    """
    Test case progress metric, which is under in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 20)

    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 11, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 6, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2022, 1, 1, tzinfo=timezone.utc)}
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_UNDER_LAST_30_DAYS.format(
            metric_id=metric_id,
            number_last_30_days=1,
            progress_percentage=50,
            number_previous_30_days=2,
            lowercase_label=lowercase_label,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_case_created_progress_metric_under(mock_date, mock_timezone, admin_client):
    """
    Test case progress metric, which is under in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 20)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 11, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 6, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2022, 1, 1, tzinfo=timezone.utc)
    simplified_case.save()

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_UNDER_LAST_30_DAYS.format(
            metric_id="cases-created",
            number_last_30_days=1,
            progress_percentage=50,
            number_previous_30_days=2,
            lowercase_label="cases created",
        ),
        html=True,
    )


@pytest.mark.parametrize(
    "label, table_id, case_field",
    [
        (
            "Tests completed",
            "tests-completed-over-the-last-year",
            "reporting_details_complete_date",
        ),
        ("Reports sent", "reports-sent-over-the-last-year", "report_sent_date"),
        ("Cases completed", "cases-completed-over-the-last-year", "completed_date"),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_case_yearly_metric(mock_timezone, label, table_id, case_field, admin_client):
    """
    Test case yearly metric table values.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 11, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 5, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2021, 12, 6, tzinfo=timezone.utc)}
    )
    SimplifiedCase.objects.create(
        **{case_field: datetime(2022, 1, 1, tzinfo=timezone.utc)}
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_YEARLY_TABLE.format(column_header=label, table_id=table_id),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_case_created_yearly_metric(mock_timezone, admin_client):
    """
    Test case yearly metric table values.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 11, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 5, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2021, 12, 6, tzinfo=timezone.utc)
    simplified_case.save()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    simplified_case.created = datetime(2022, 1, 1, tzinfo=timezone.utc)
    simplified_case.save()

    response: HttpResponse = admin_client.get(reverse("common:metrics-case"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_YEARLY_TABLE.format(
            column_header="Cases created", table_id="cases-created-over-the-last-year"
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_policy_progress_metric_website_compliance(mock_timezone, admin_client):
    """
    Test policy progress metric for website compliance is calculated correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send",
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        POLICY_PROGRESS_METRIC.format(
            id="websites-compliant-after-retest-in-the-last-90-days",
            percentage=50,
            partial_count=1,
            total_count=2,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_policy_progress_metric_statement_compliance(mock_timezone, admin_client):
    """
    Test policy progress metric for website compliance is calculated correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = create_case_and_compliance(
        case_completed="complete-no-send",
        statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        POLICY_PROGRESS_METRIC.format(
            id="statements-compliant-after-retest-in-the-last-90-days",
            percentage=50,
            partial_count=1,
            total_count=2,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_policy_progress_metric_website_issues(mock_timezone, admin_client):
    """
    Test policy progress metric for website accessibility issues is calculated correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state="error",
        retest_state="fixed",
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state="error",
        retest_state="not-fixed",
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        POLICY_PROGRESS_METRIC.format(
            id="website-accessibility-issues-fixed-in-the-last-90-days",
            percentage=50,
            partial_count=1,
            total_count=2,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_policy_progress_metric_statement_issues(mock_timezone, admin_client):
    """
    Test policy progress metric for accessibility statement issues is calculated correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
        check_result_state=StatementCheckResult.Result.NO,
        retest_state=StatementCheckResult.Result.YES,
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        POLICY_PROGRESS_METRIC.format(
            id="statement-issues-fixed-in-the-last-90-days",
            percentage=100,
            partial_count=1,
            total_count=1,
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_policy_metric_completed_with_equalities_bodies(mock_timezone, admin_client):
    """
    Test policy metric for completed cases with equalities bodies.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    SimplifiedCase.objects.create(
        created=datetime(2021, 11, 12, tzinfo=timezone.utc),
        enforcement_body_pursuing="yes-completed",
    )
    SimplifiedCase.objects.create(
        created=datetime(2021, 5, 12, tzinfo=timezone.utc),
        enforcement_body_pursuing="yes-in-progress",
    )
    SimplifiedCase.objects.create(
        created=datetime(2021, 2, 1, tzinfo=timezone.utc),
        enforcement_body_pursuing="yes-in-progress",
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        """<p id="cases-completed-with-equalities-bodies" class="govuk-body-m">
            <span class="govuk-!-font-size-48 amp-padding-right-20"><b>1</b></span>
            with 2 in progress
        </p>""",
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_policy_yearly_metric_website_state(mock_timezone, admin_client):
    """
    Test policy yearly metric table values for website state.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        date_of_test=datetime(2021, 9, 15, tzinfo=timezone.utc),
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    initially_compliant_website_case: SimplifiedCase = create_case_and_compliance(
        case_completed="complete-no-send",
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        simplified_case=initially_compliant_website_case,
        date_of_test=datetime(2021, 9, 15, tzinfo=timezone.utc),
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send",
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 11, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send",
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 11, 5, tzinfo=timezone.utc),
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        ACCEPTABLE_WEBSITES_ROW,
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_policy_yearly_metric_statement_state(mock_timezone, admin_client):
    """
    Test policy yearly metric table values for accessibility statement state.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        date_of_test=datetime(2021, 9, 15, tzinfo=timezone.utc),
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    initally_compliant_statement_case: SimplifiedCase = create_case_and_compliance(
        case_completed="complete-no-send",
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        simplified_case=initally_compliant_statement_case,
        date_of_test=datetime(2021, 9, 15, tzinfo=timezone.utc),
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 12, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = create_case_and_compliance(
        case_completed="complete-no-send",
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        case_completed="complete-no-send"
    )
    Audit.objects.create(
        simplified_case=simplified_case,
        retest_date=datetime(2021, 11, 15, tzinfo=timezone.utc),
    )
    fixed_case: SimplifiedCase = create_case_and_compliance(
        case_completed="complete-no-send",
        recommendation_for_enforcement=SimplifiedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
        statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        simplified_case=fixed_case,
        retest_date=datetime(2021, 11, 5, tzinfo=timezone.utc),
    )

    response: HttpResponse = admin_client.get(reverse("common:metrics-policy"))

    assert response.status_code == 200
    assertContains(
        response,
        COMPLIANT_STATEMENTS_ROW,
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_report_published_progress_metric_over(mock_date, mock_timezone, admin_client):
    """
    Test published reports progress metric, which is over in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 10, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 29)

    for created_date in [
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
        datetime(2022, 1, 2, tzinfo=timezone.utc),
    ]:
        with patch(
            "django.utils.timezone.now",
            Mock(return_value=created_date),
        ):
            simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
            S3Report.objects.create(
                base_case=simplified_case, version=1, latest_published=True
            )

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_OVER_LAST_30_DAYS.format(
            metric_id="published-reports",
            number_last_30_days=2,
            progress_percentage=100,
            number_previous_30_days=1,
            lowercase_label="published reports",
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_report_published_progress_metric_under(mock_date, mock_timezone, admin_client):
    """
    Test published reports progress metric, which is under in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 29)

    for created_date in [
        datetime(2021, 11, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 6, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
    ]:
        with patch(
            "django.utils.timezone.now",
            Mock(return_value=created_date),
        ):
            simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
            S3Report.objects.create(
                base_case=simplified_case, version=1, latest_published=True
            )

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_UNDER_LAST_30_DAYS.format(
            metric_id="published-reports",
            number_last_30_days=1,
            progress_percentage=50,
            number_previous_30_days=2,
            lowercase_label="published reports",
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_report_viewed_progress_metric_under(mock_date, mock_timezone, admin_client):
    """
    Test reports viewed progress metric, which is under in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 29, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 29)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    for created_date in [
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 6, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
    ]:
        with patch("django.utils.timezone.now", Mock(return_value=created_date)):
            simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
            ReportVisitsMetrics.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_UNDER_LAST_30_DAYS.format(
            metric_id="report-views",
            number_last_30_days=1,
            progress_percentage=50,
            number_previous_30_days=2,
            lowercase_label="report views",
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_report_acknowledged_progress_metric_under(
    mock_date, mock_timezone, admin_client
):
    """
    Test report acknowledged progress metric, which is under in last 30 days, is calculated and
    displayed correctly.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 29, tzinfo=timezone.utc)
    mock_date.today.return_value = date(2022, 1, 29)

    for acknowledged_date in [
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 6, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
    ]:
        SimplifiedCase.objects.create(report_acknowledged_date=acknowledged_date)

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_UNDER_LAST_30_DAYS.format(
            metric_id="reports-acknowledged",
            number_last_30_days=1,
            progress_percentage=50,
            number_previous_30_days=2,
            lowercase_label="reports acknowledged",
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_report_published_yearly_metric(mock_timezone, admin_client):
    """
    Test report published yearly metric table values.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    for creation_time in [
        datetime(2021, 11, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 6, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
    ]:
        with patch("django.utils.timezone.now", Mock(return_value=creation_time)):
            simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
            S3Report.objects.create(
                base_case=simplified_case, version=1, latest_published=True
            )

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_YEARLY_TABLE.format(
            column_header="Published reports",
            table_id="reports-published-over-the-last-year",
        ),
        html=True,
    )


@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_report_viewed_yearly_metric(mock_timezone, admin_client):
    """
    Test report published yearly metric table values.
    """
    mock_timezone.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    for creation_time in [
        datetime(2021, 11, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 5, tzinfo=timezone.utc),
        datetime(2021, 12, 6, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
    ]:
        with patch("django.utils.timezone.now", Mock(return_value=creation_time)):
            simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
            ReportVisitsMetrics.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(reverse("common:metrics-report"))

    assert response.status_code == 200
    assertContains(
        response,
        METRIC_YEARLY_TABLE.format(
            column_header="Report views", table_id="reports-views-over-the-last-year"
        ),
        html=True,
    )


def test_simplified_case_nav(admin_client):
    """Test simplified case nav rendered correctly"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<h2 class="govuk-heading-s amp-margin-bottom-10">Case tools</h2>',
        html=True,
    )
    assertContains(
        response,
        f"""<li>
            <a href="/simplified/{simplified_case.id}/zendesk-tickets/"
            rel="noreferrer noopener" class="govuk-link govuk-link--no-visited-state">
            PSB Zendesk tickets</a>
        </li>""",
        html=True,
    )


def test_detailed_case_nav(admin_client):
    """Test detailed case nav rendered correctly"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("detailed:case-detail", kwargs={"pk": detailed_case.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<h2 class="govuk-heading-s amp-margin-bottom-10">Case tools</h2>',
        html=True,
    )
    assertContains(
        response,
        f"""<li>
            <a href="/detailed/{detailed_case.id}/zendesk-tickets/"
            rel="noreferrer noopener" class="govuk-link govuk-link--no-visited-state">
            PSB Zendesk tickets</a>
        </li>""",
        html=True,
    )


@pytest.mark.django_db
def test_frequently_used_link_shown(admin_client):
    """Test custom frequently used link is displayed"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    FrequentlyUsedLink.objects.create(label=LINK_LABEL, url=LINK_URL)

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id})
    )

    assert response.status_code == 200
    assertContains(response, LINK_LABEL)
    assertContains(response, LINK_URL)


def test_add_frequently_used_link_form_appears(admin_client):
    """Test that pressing the add link button adds a new link form"""

    response: HttpResponse = admin_client.post(
        reverse("common:edit-frequently-used-links"),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "add_link": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Custom link 1")


def test_add_frequently_used_link(admin_client):
    """Test adding a frequently used link"""

    response: HttpResponse = admin_client.post(
        reverse("common:edit-frequently-used-links"),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "",
            "form-0-label": LINK_LABEL,
            "form-0-url": LINK_URL,
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200

    links: QuerySet[FrequentlyUsedLink] = FrequentlyUsedLink.objects.all()
    assert links.count() == 1
    assert links[0].label == LINK_LABEL
    assert links[0].url == LINK_URL


def test_delete_frequently_used_link(admin_client):
    """Test that pressing the remove link button deletes the link"""
    link: FrequentlyUsedLink = FrequentlyUsedLink.objects.create(
        label=LINK_LABEL, url=LINK_URL
    )

    response: HttpResponse = admin_client.post(
        reverse("common:edit-frequently-used-links"),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            f"remove_link_{link.id}": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "No frequently used links have been entered")

    link_on_database = FrequentlyUsedLink.objects.get(pk=link.id)
    assert link_on_database.is_deleted is True


@pytest.mark.django_db
def test_footer_link_shown(admin_client):
    """Test custom footer link is displayed"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    FooterLink.objects.create(label=FOOTER_LINK_LABEL, url=FOOTER_LINK_URL)

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id})
    )

    assert response.status_code == 200
    assertContains(response, FOOTER_LINK_LABEL)
    assertContains(response, FOOTER_LINK_URL)


def test_add_footer_link_form_appears(admin_client):
    """Test that pressing the add link button adds a new link form"""

    response: HttpResponse = admin_client.post(
        reverse("common:edit-footer-links"),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "add_link": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Footer link 1")


def test_add_footer_link(admin_client):
    """Test adding a footer link"""

    response: HttpResponse = admin_client.post(
        reverse("common:edit-footer-links"),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "",
            "form-0-label": FOOTER_LINK_LABEL,
            "form-0-url": FOOTER_LINK_URL,
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200

    links: QuerySet[FooterLink] = FooterLink.objects.all()
    assert links.count() == 1
    assert links[0].label == FOOTER_LINK_LABEL
    assert links[0].url == FOOTER_LINK_URL


def test_delete_footer_link(admin_client):
    """Test that pressing the remove link button deletes the link"""
    link: FooterLink = FooterLink.objects.create(
        label=FOOTER_LINK_LABEL, url=FOOTER_LINK_URL
    )

    response: HttpResponse = admin_client.post(
        reverse("common:edit-footer-links"),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            f"remove_link_{link.id}": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "No footer links have been entered")

    link_on_database = FooterLink.objects.get(pk=link.id)
    assert link_on_database.is_deleted is True


def test_platform_checking_writes_log(admin_client, caplog):
    """Test platform checking writes to log"""
    response: HttpResponse = admin_client.post(
        reverse("common:platform-checking"),
        {
            "level": logging.WARNING,
            "message": LOG_MESSAGE,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("common:platform-checking")
    assert caplog.record_tuples == [
        ("accessibility_monitoring_platform.apps.common.views", 30, LOG_MESSAGE)
    ]


@pytest.mark.django_db
def test_platform_checking_staff_access(client):
    """Tests if staff users can access platform checking"""
    user: User = create_user()
    user.is_staff = True
    user.save()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse("common:platform-checking"))

    assert response.status_code == 200
    assertContains(response, "Tools and sitemap")


@pytest.mark.django_db
def test_platform_checking_non_staff_access(client):
    """Tests non-staff users cannot access platform checking"""
    create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse("common:platform-checking"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_latest_statement_frequently_used_link(admin_client):
    """
    Test latest accessibility statement link in frequently used links
    is displayed only when one has been entered.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id})
    )

    assert response.status_code == 200

    assertContains(response, "No accessibility statement URL")
    assertNotContains(response, "Latest accessibility statement")

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    StatementPage.objects.create(audit=audit, url="https://example.com/statement")

    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id})
    )

    assert response.status_code == 200

    assertNotContains(response, "No accessibility statement URL")
    assertContains(response, "Latest accessibility statement")


@pytest.mark.django_db
def test_navbar_tasks_emboldened(admin_client, admin_user):
    """
    Test tasks item in the top menu of all pages is rendered as bold when
    one is due.
    """
    response: HttpResponse = admin_client.get(reverse("common:platform-history"))

    assert response.status_code == 200
    assertContains(
        response,
        """<li>
            <a class="govuk-link govuk-link--no-visited-state" href="/notifications/task-list/">
                Tasks (0)
            </a>
        </li>""",
        html=True,
    )

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=admin_user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        base_case=simplified_case,
        user=admin_user,
    )

    response: HttpResponse = admin_client.get(reverse("common:platform-history"))

    assert response.status_code == 200
    assertContains(
        response,
        """<li>
        <b>
            <a class="govuk-link govuk-link--no-visited-state" href="/notifications/task-list/">
                Tasks (1)
            </a>
        </b>
        </li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url, expected_page_name",
    [
        ("/", "Your cases"),
        ("/cases/1/edit-case-metadata/", "Case metadata"),
        ("/audits/1/edit-audit-metadata/", "Initial test metadata"),
    ],
)
def test_page_name(url, expected_page_name, admin_client):
    """
    Test that the page renders and problem page's url and name are populated
    as expected.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.get(
        f"/common/report-issue/?page_url={url}&page_title={expected_page_name}"
    )

    assert response.status_code == 200

    assertContains(response, "Report an issue")
    assertContains(response, url)
    assertContains(response, expected_page_name)


def test_reference_implementations_page(admin_client):
    """Test that the reference implementation page renders"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("common:reference-implementation")
    )

    assert response.status_code == 200

    assertContains(response, "Reference implementation")
