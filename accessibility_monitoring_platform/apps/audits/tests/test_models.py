"""
Tests for cases models
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from django.db.models.query import QuerySet
from pytest_django.asserts import assertQuerySetEqual

from ...common.models import Boolean
from ...simplified.models import SimplifiedCase
from ..models import (
    AuditOverview,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementCheckResultRound,
    StatementPage,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultRetest,
    WcagDefinition,
    WcagPageInitial,
    WcagPageRetest,
)
from .create_test_data import (
    WCAG_TYPE_AXE_NAME,
    WCAG_TYPE_PDF_NAME,
    create_initial_statement_audit,
    create_initial_wcag_audit,
    create_retest_statement_audit,
    create_retest_wcag_audit,
    create_simplified_case_with_initial_and_12_week_audits,
)

TODAY: date = date.today()
PREVIOUS_STATEMENT_CHECKS_TIME: datetime = datetime(2025, 4, 1, tzinfo=timezone.utc)
PAGE_NAME: str = "Page name"
WCAG_DESCRIPTION: str = "WCAG definition description"
DATETIME_AUDIT_UPDATED: datetime = datetime(2021, 9, 20, tzinfo=timezone.utc)
DATETIME_PAGE_UPDATED: datetime = datetime(2021, 9, 22, tzinfo=timezone.utc)
DATETIME_CHECK_RESULT_UPDATED: datetime = datetime(2021, 9, 24, tzinfo=timezone.utc)
INITIAL_NOTES: str = "Initial notes"
FINAL_NOTES: str = "Final notes"
INCOMPLETE_DEADLINE_TEXT: str = "Incomplete deadline text"
INSUFFICIENT_DEADLINE_TEXT: str = "Insufficient deadline text"
ERROR_NOTES: str = "Error notes"
STATEMENT_LINK: str = "https://example.com/accessibility-statement"
ACCESSIBILITY_PAGE_STATEMENT_CHECK_ID: int = 1
REPORT_COMMENT: str = "Report comment"
GOOGLE_DRIVE_LINK: str = "https://drive.google.com/link1"
NON_GOOGLE_DRIVE_LINK: str = "https://example.com/link2"
STATEMENT_PAGE_URL: str = "https://example.com/statement"
STATEMENT_PAGE_LOCATION: str = "Statement location"


@pytest.mark.django_db
def test_wcag_audit_updated_updated():
    """Test the wcag audit updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_UPDATED)):
        wcag_audit.save()

    assert wcag_audit.updated == DATETIME_AUDIT_UPDATED


@pytest.mark.django_db
def test_audit_overview_wcag_audits():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.wcag_audits.count() == 0

    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)

    assert audit_overview.wcag_audits.count() == 1

    wcag_audit.is_deleted = True
    wcag_audit.save()

    assert audit_overview.wcag_audits.count() == 0


@pytest.mark.django_db
def test_audit_overview_initial_wcag_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.initial_wcag_audit is None

    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)

    assert audit_overview.initial_wcag_audit == wcag_audit


@pytest.mark.django_db
def test_audit_overview_first_twelve_week_wcag_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.first_twelve_week_wcag_audit is None

    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )

    assert audit_overview.first_twelve_week_wcag_audit == wcag_audit


@pytest.mark.django_db
def test_audit_overview_equality_body_wcag_audits():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.equality_body_wcag_audits.count() == 0

    WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert audit_overview.equality_body_wcag_audits.count() == 1


@pytest.mark.django_db
def test_audit_overview_first_equality_body_wcag_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.first_equality_body_wcag_audit is None

    first_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert audit_overview.first_equality_body_wcag_audit == first_wcag_audit


@pytest.mark.django_db
def test_audit_overview_last_equality_body_wcag_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.last_equality_body_wcag_audit is None

    WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    last_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert audit_overview.last_equality_body_wcag_audit == last_wcag_audit


@pytest.mark.django_db
def test_website_compliance_display():
    """Test website compliance is derived correctly"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    initial_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.website_compliance_display == "Not known"

    initial_wcag_audit.compliance_state = WcagAudit.WebsiteCompliance.PARTIALLY
    initial_wcag_audit.save()

    assert audit_overview.website_compliance_display == "Partially compliant"

    wcag_audit_twelve_week: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )

    assert audit_overview.website_compliance_display == "Partially compliant"

    wcag_audit_twelve_week.compliance_state = WcagAudit.WebsiteCompliance.COMPLIANT
    wcag_audit_twelve_week.save()

    assert audit_overview.website_compliance_display == "Fully compliant"


@pytest.mark.django_db
def test_audit_overview_statement_pages():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.statement_pages.count() == 0

    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )

    assert audit_overview.statement_pages.count() == 1

    statement_page.is_deleted = True
    statement_page.save()

    assert audit_overview.statement_pages.count() == 0


@pytest.mark.django_db
def test_audit_overview_latest_statement_link():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.latest_statement_link is None

    StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=audit_overview,
        url=STATEMENT_PAGE_URL,
    )

    assert audit_overview.latest_statement_link == STATEMENT_PAGE_URL

    StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=audit_overview,
    )

    assert audit_overview.latest_statement_link == STATEMENT_PAGE_URL


@pytest.mark.django_db
def test_wcag_audit_every_wcag_page_initials_returns_all_pages():
    """Deleted and pages which were not found are also excluded"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()

    assert wcag_audit.every_wcag_page_initials.count() == 6


@pytest.mark.django_db
def test_audit_overview_contact_wcag_page_initial():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
    )

    assert audit_overview.contact_wcag_page_initial is None

    contact_wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.CONTACT
    )

    assert audit_overview.contact_wcag_page_initial == contact_wcag_page_initial


@pytest.mark.django_db
def test_audit_overview_statement_wcag_page_initial():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
    )

    assert audit_overview.statement_wcag_page_initial is None

    statement_wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.STATEMENT
    )

    assert audit_overview.statement_wcag_page_initial == statement_wcag_page_initial


@pytest.mark.django_db
def test_audit_overview_archived_google_drive_links():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    StatementPage.objects.create(
        audit_overview=audit_overview,
        backup_url=GOOGLE_DRIVE_LINK,
    )
    StatementPage.objects.create(
        audit_overview=audit_overview,
        backup_url=NON_GOOGLE_DRIVE_LINK,
    )

    assert audit_overview.archived_google_drive_links.count() == 1
    assert (
        audit_overview.archived_google_drive_links.first().backup_url
        == GOOGLE_DRIVE_LINK
    )


@pytest.mark.django_db
def test_audit_unique_statement_page_urls():
    """Test unique statement page urls returns only first with matching URL"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    first_new_statement_page: StatementPage = StatementPage.objects.create(
        audit_overview=audit_overview,
        url=STATEMENT_LINK,
    )
    StatementPage.objects.create(
        audit_overview=audit_overview,
        url=STATEMENT_LINK,
    )

    assert len(audit_overview.unique_statement_page_urls) == 1
    assert audit_overview.unique_statement_page_urls[0] == first_new_statement_page


@pytest.mark.django_db
def test_audit_overview_accessibility_statement_found():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.accessibility_statement_found is False

    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=audit_overview,
    )

    assert audit_overview.accessibility_statement_found is False

    statement_page.url = STATEMENT_PAGE_URL
    statement_page.save()

    assert audit_overview.accessibility_statement_found is True


@pytest.mark.django_db
def test_audit_overview_statement_audits():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.statement_audits.count() == 0

    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.statement_audits.count() == 1

    statement_audit.is_deleted = True
    statement_audit.save()

    assert audit_overview.statement_audits.count() == 0


@pytest.mark.django_db
def test_audit_overview_initial_statement_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.initial_statement_audit is None

    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.initial_statement_audit == statement_audit


@pytest.mark.django_db
def test_audit_overview_twelve_week_statement_audits():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.twelve_week_statement_audits.count() == 0

    StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )

    assert audit_overview.twelve_week_statement_audits.count() == 1


@pytest.mark.django_db
def test_audit_overview_equality_body_statement_audits():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.equality_body_statement_audits.count() == 0

    StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert audit_overview.equality_body_statement_audits.count() == 1


@pytest.mark.django_db
def test_audit_overview_last_statement_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.last_statement_audit is None

    StatementAudit.objects.create(
        simplified_case=simplified_case,
    )
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
    )

    assert audit_overview.last_statement_audit == statement_audit


@pytest.mark.django_db
def test_audit_overview_first_twelve_week_statement_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.first_twelve_week_statement_audit is None

    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )

    assert audit_overview.first_twelve_week_statement_audit == statement_audit


@pytest.mark.django_db
def test_audit_overview_last_equality_body_statement_audit():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.last_equality_body_statement_audit is None

    StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY,
    )
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert audit_overview.last_equality_body_statement_audit == statement_audit


@pytest.mark.django_db
def test_audit_overview_all_overview_statement_checks_have_passed():
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )

    assert audit_overview.all_overview_statement_checks_have_passed is False

    initial_statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
    )
    overview_statement_check: StatementCheck = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).last()
    initial_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=initial_statement_audit,
            statement_check=overview_statement_check,
            type=StatementCheck.Type.OVERVIEW,
        )
    )

    assert audit_overview.all_overview_statement_checks_have_passed is False

    initial_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.YES
    )
    initial_statement_check_result.save()

    assert audit_overview.all_overview_statement_checks_have_passed is True

    twelve_week_statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    twelve_week_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=twelve_week_statement_audit,
            statement_check=overview_statement_check,
            type=StatementCheck.Type.OVERVIEW,
        )
    )

    assert audit_overview.all_overview_statement_checks_have_passed is False

    twelve_week_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.YES
    )
    twelve_week_statement_check_result.save()

    assert audit_overview.all_overview_statement_checks_have_passed is True


@pytest.mark.django_db
def test_audit_overview_last_edited():
    """
    Create the AuditOverview and related data with known advancing datetimes and
    check that the last edited datetime advances also.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        audit_overview: AuditOverview = AuditOverview.objects.create(
            simplified_case=simplified_case
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED

    with patch(
        "django.utils.timezone.now",
        Mock(return_value=DATETIME_PAGE_UPDATED + timedelta(days=1)),
    ):
        wcag_audit: WcagAudit = WcagAudit.objects.create(
            simplified_case=simplified_case
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED + timedelta(days=1)

    with patch(
        "django.utils.timezone.now",
        Mock(return_value=DATETIME_PAGE_UPDATED + timedelta(days=2)),
    ):
        wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
            wcag_audit=wcag_audit,
            url="https://example.com",
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED + timedelta(days=2)

    with patch(
        "django.utils.timezone.now",
        Mock(return_value=DATETIME_PAGE_UPDATED + timedelta(days=3)),
    ):
        wcag_definition: WcagDefinition = WcagDefinition.objects.all().first()
        wcag_check_result_initial: WcagCheckResultInitial = (
            WcagCheckResultInitial.objects.create(
                wcag_audit=wcag_audit,
                wcag_page_initial=wcag_page_initial,
                type=wcag_definition.type,
                wcag_definition=wcag_definition,
            )
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED + timedelta(days=3)

    with patch(
        "django.utils.timezone.now",
        Mock(return_value=DATETIME_PAGE_UPDATED + timedelta(days=4)),
    ):
        wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
            wcag_audit=wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED + timedelta(days=4)

    with patch(
        "django.utils.timezone.now",
        Mock(return_value=DATETIME_PAGE_UPDATED + timedelta(days=5)),
    ):
        WcagCheckResultRetest.objects.create(
            wcag_audit=wcag_audit,
            wcag_page_retest=wcag_page_retest,
            wcag_definition=wcag_definition,
            wcag_check_result_initial=wcag_check_result_initial,
        )

    assert audit_overview.last_edited == DATETIME_PAGE_UPDATED + timedelta(days=5)


@pytest.mark.django_db
def test_wcag_audit_every_wcag_page_initials_returns_pdf_and_statement_last():
    """Statement page returned last. PDF page second-last"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()

    assert (
        wcag_audit.every_wcag_page_initials.last().page_type
        == WcagPageInitial.Type.STATEMENT
    )
    assert (
        list(wcag_audit.every_wcag_page_initials)[-2].page_type
        == WcagPageInitial.Type.PDF
    )


@pytest.mark.django_db
def test_wcag_page_initial_get_absolute_url():
    """
    Test WcagPage.get_absolute_url is as expected
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.STATEMENT
    )

    assert (
        wcag_page_initial.get_absolute_url()
        == f"/audits/pages/{wcag_page_initial.id}/edit-audit-page-checks/"
    )


@pytest.mark.django_db
def test_page_str():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = wcag_audit.every_wcag_page_initials.filter(
        page_type=WcagPageInitial.Type.STATEMENT
    ).first()

    assert wcag_page_initial.__str__() == "Accessibility statement"


@pytest.mark.django_db
def test_html_page_page_title():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = wcag_audit.every_wcag_page_initials.filter(
        page_type=WcagPageInitial.Type.STATEMENT
    ).first()

    assert wcag_page_initial.page_title == "Accessibility statement page"


@pytest.mark.django_db
def test_pdf_page_page_title():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = wcag_audit.every_wcag_page_initials.filter(
        page_type=WcagPageInitial.Type.PDF
    ).first()
    wcag_page_initial.name = "File"
    wcag_page_initial.save()

    assert wcag_page_initial.page_title == "File"


@pytest.mark.django_db
def test_audit_testable_pages_returns_expected_page():
    """Deleted, not found and pages without URLs excluded"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    testable_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    for wcag_page_initial in WcagPageInitial.objects.filter(
        wcag_audit=wcag_audit
    ).exclude(page_type=WcagPageInitial.Type.HOME):
        if wcag_page_initial.page_type == WcagPageInitial.Type.PDF:
            wcag_page_initial.not_found = Boolean.YES
        else:
            wcag_page_initial.url = ""
        wcag_page_initial.save()

    assert len(wcag_audit.testable_wcag_page_initials) == 1
    assert wcag_audit.testable_wcag_page_initials[0].id == testable_page.id


@pytest.mark.django_db
def test_audit_retestable_pages_returns_expected_page():
    """Deleted, not found, pages without URLs and missing pages excluded"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    retestable_wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
        url="https://example.com",
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=retestable_wcag_page_initial,
        url=retestable_wcag_page_initial.url,
    )
    unretestable_wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
        url="https://example.com",
        not_found="yes",
    )
    WcagPageRetest.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=unretestable_wcag_page_initial,
        url=unretestable_wcag_page_initial.url,
        page_missing_date=date.today(),
    )

    assert len(wcag_audit.retestable_wcag_page_retests) == 1
    assert wcag_audit.retestable_wcag_page_retests[0].id == wcag_page_retest.id


@pytest.mark.django_db
def test_audit_missing_at_retest_pages():
    """Test missing at retest pages."""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )

    assert len(twelve_week_wcag_audit.wcag_page_retests_missing_at_retest) == 0

    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.filter(
        wcag_audit=twelve_week_wcag_audit,
    ).first()
    wcag_page_retest.page_missing_date = TODAY
    wcag_page_retest.save()

    assert len(twelve_week_wcag_audit.wcag_page_retests_missing_at_retest) == 1
    assert (
        twelve_week_wcag_audit.wcag_page_retests_missing_at_retest[0]
        == wcag_page_retest
    )


@pytest.mark.django_db
def test_audit_missing_at_retest_check_results():
    """Test missing at retest check results."""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )

    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(
            wcag_audit=twelve_week_wcag_audit,
        )
    ).first()
    wcag_page_retest: WcagPageRetest = wcag_check_result_retest.wcag_page_retest

    assert len(twelve_week_wcag_audit.missing_at_retest_check_results) == 0

    wcag_page_retest.page_missing_date = TODAY
    wcag_page_retest.save()

    assert len(twelve_week_wcag_audit.missing_at_retest_check_results) == 2


@pytest.mark.django_db
def test_wcag_page_initial_string():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = wcag_audit.every_wcag_page_initials[0]

    assert str(wcag_page_initial) == "Home"

    wcag_page_initial.name = PAGE_NAME

    assert str(wcag_page_initial) == PAGE_NAME


@pytest.mark.django_db
def test_wcag_page_initial_anchor():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = wcag_audit.every_wcag_page_initials[0]

    assert wcag_page_initial.anchor == f"test-page-{wcag_page_initial.id}"


@pytest.mark.django_db
def test_wcag_audit_wcag_failed_check_result_initials_returns_only_failed_checks():
    """
    Test wcag_failed_check_result_initials attribute of WcagAudit returns only check
    results where failed is "yes".
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 0

    wcag_check_result_initial: WcagCheckResultInitial = (
        wcag_audit.wcagcheckresultinitial_set.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 1


@pytest.mark.django_db
def test_audit_wcag_failed_check_result_initials_for_deleted_page_not_returned():
    """
    Test wcag_failed_check_result_initials attribute of audit returns only check
    results where failed is "yes" and associated page has not been deleted.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_check_result_initial: WcagCheckResultInitial = (
        wcag_audit.wcagcheckresultinitial_set.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 1

    wcag_page_initial: WcagPageInitial = wcag_check_result_initial.wcag_page_initial
    wcag_page_initial.is_deleted = True
    wcag_page_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 0


@pytest.mark.django_db
def test_wcag_audit_wcag_failed_check_result_retests_for_missing_page_not_returned():
    """
    Test wcag_failed_check_result_retests attribute of audit returns only check
    results where retest page missing is not set.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_check_result_initial: WcagCheckResultInitial = (
        wcag_audit.wcagcheckresultinitial_set.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 1

    wcag_page_initial: WcagPageInitial = wcag_check_result_initial.wcag_page_initial
    wcag_page_initial.page_missing_date = TODAY
    wcag_page_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_retests) == 0


@pytest.mark.django_db
def test_wcag_audit_failed_check_results_for_is_contact_page_page_not_returned():
    """
    Test failed_check_results attribute of audit returns only check results where
    failed is "yes" and associated page has not got is_contact_page (used for form
    pages) is not set.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_check_result_initial: WcagCheckResultInitial = (
        wcag_audit.wcagcheckresultinitial_set.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 1

    wcag_page_initial: WcagPageInitial = wcag_check_result_initial.wcag_page_initial
    wcag_page_initial.is_contact_page = Boolean.YES
    wcag_page_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) == 0


@pytest.mark.django_db
def test_wcag_audit_accessibility_statement_wcag_page_initial_returns_page():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.STATEMENT
    )

    assert wcag_audit.accessibility_statement_wcag_page_initial == wcag_page_initial


@pytest.mark.django_db
def test_wcag_page_initial_all_wcag_check_result_initials_returns_check_results():
    """
    Test all_wcag_check_result_initials attribute of WcagPageInitial returns
    expected check results.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    home_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )

    assert len(home_page.all_wcag_check_result_initials) == 2
    assert home_page.all_wcag_check_result_initials[0].type == WcagDefinition.Type.AXE
    assert (
        home_page.all_wcag_check_result_initials[1].type == WcagDefinition.Type.MANUAL
    )


@pytest.mark.django_db
def test_wcag_audit_wcag_failed_check_result_initials_returns_statement_check_results_last():
    """
    Test wcag_failed_check_result_initials attribute of page returns Statement page
    check results last.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    for wcag_check_result_initial in WcagCheckResultInitial.objects.filter(
        wcag_audit=wcag_audit
    ):
        wcag_check_result_initial.check_result_state = (
            WcagCheckResultInitial.Result.ERROR
        )
        wcag_check_result_initial.save()

    assert len(wcag_audit.wcag_failed_check_result_initials) > 3
    assert (
        wcag_audit.wcag_failed_check_result_initials.last().wcag_page_initial.page_type
        == WcagPageInitial.Type.STATEMENT
    )


@pytest.mark.django_db
def test_wcag_page_initial_page_title():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    home_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    pdf_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.PDF
    )

    assert home_page.page_title == "Home page"
    assert pdf_page.page_title == "PDF"

    home_page.name = "Homepage"
    home_page.save()
    pdf_page.name = "Document"
    pdf_page.save()

    assert home_page.page_title == "Homepage page"
    assert pdf_page.page_title == "Document"


def test_wcag_definition_strings():
    """
    Test WCAG definitions return expected string values.
    """
    wcag_definition: WcagDefinition = WcagDefinition(
        type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )
    assert str(wcag_definition) == f"{WCAG_TYPE_PDF_NAME} (PDF)"

    wcag_definition_with_description: WcagDefinition = WcagDefinition(
        type=WcagDefinition.Type.PDF,
        name=WCAG_TYPE_PDF_NAME,
        description=WCAG_DESCRIPTION,
    )
    assert (
        str(wcag_definition_with_description)
        == f"{WCAG_TYPE_PDF_NAME}: {WCAG_DESCRIPTION} (PDF)"
    )


@pytest.mark.django_db
def test_wcag_definition_start_end_date_range():
    """
    Test that an WCAG definition within a date range returned.
    """
    WcagDefinition.objects.all().delete()
    past_date: date = date(2020, 1, 1)
    current_date: date = date(2023, 1, 1)
    future_date: date = date(2024, 1, 1)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    WcagDefinition.objects.create(date_end=past_date)
    WcagDefinition.objects.create(date_start=future_date)

    assert WcagDefinition.objects.all().count() == 3

    assert WcagDefinition.objects.on_date(current_date).count() == 1

    assert WcagDefinition.objects.on_date(current_date).first() == wcag_definition


@pytest.mark.django_db
def test_accessibility_statement_found():
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    StatementPage.objects.create(
        simplified_case=wcag_audit.simplified_case,
        audit_overview=wcag_audit.simplified_case.audit_overview,
        url=STATEMENT_LINK,
    )

    assert (
        wcag_audit.simplified_case.audit_overview.accessibility_statement_found is True
    )


@pytest.mark.django_db
def test_page_updated_updated():
    """Test the page updated field is updated"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        wcag_page_initial.save()

    assert wcag_page_initial.updated == DATETIME_PAGE_UPDATED


@pytest.mark.django_db
def test_wcag_check_result_initial_updated_updated():
    """Test the WCAG check result initial updated field is updated"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=wcag_audit,
        ).first()
    )
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_UPDATED)
    ):
        wcag_check_result_initial.save()

    assert wcag_check_result_initial.updated == DATETIME_CHECK_RESULT_UPDATED


@pytest.mark.django_db
def test_audit_fixed_check_results():
    """Test that wcag_fixed_check_result_retests returns the expected values"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 0

    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(wcag_audit=twelve_week_wcag_audit).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.FIXED
    wcag_check_result_retest.save()

    wcag_check_result_initial: WcagCheckResultInitial = (
        wcag_check_result_retest.wcag_check_result_initial
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 1
    assert (
        twelve_week_wcag_audit.wcag_fixed_check_result_retests[0].id
        == wcag_check_result_retest.id
    )


@pytest.mark.django_db
def test_audit_wcag_unfixed_check_result_retests():
    """Test that wcag_unfixed_check_result_retests returns the expected values"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    for counter, wcag_check_result_initial in enumerate(
        WcagCheckResultInitial.objects.filter(wcag_audit=initial_wcag_audit)
    ):
        wcag_check_result_initial.check_result_state = (
            WcagCheckResultInitial.Result.ERROR
        )
        wcag_check_result_initial.save()
        if counter > 2:
            break

    assert twelve_week_wcag_audit.wcag_unfixed_check_result_retests.count() == 4

    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(wcag_audit=twelve_week_wcag_audit).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.FIXED
    wcag_check_result_retest.save()

    assert twelve_week_wcag_audit.wcag_unfixed_check_result_retests.count() == 3


def test_statement_check_str():
    """Tests an StatementCheck __str__ contains the expected string"""
    statement_check: StatementCheck = StatementCheck(label="Label")

    assert statement_check.__str__() == "Label (Custom statement issues)"

    statement_check.success_criteria = "Success criteria"

    assert (
        statement_check.__str__() == "Label: Success criteria (Custom statement issues)"
    )


@pytest.mark.django_db
def test_statement_check_result_initial_edit_initial_url_name():
    statement_audit: StatementAudit = create_initial_statement_audit()
    statement_check_result_initial: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=statement_audit,
            statement_check__type=StatementCheck.Type.COMPLIANCE,
        ).first()
    )

    assert (
        statement_check_result_initial.edit_initial_url_name
        == "audits:edit-statement-compliance"
    )


@pytest.mark.django_db
def test_statement_check_result_retest_edit_12_week_url_name():
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )
    statement_check_result_retest: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=twelve_week_statement_audit,
            statement_check__type=StatementCheck.Type.COMPLIANCE,
        ).first()
    )

    assert (
        statement_check_result_retest.edit_12_week_url_name
        == "audits:edit-retest-statement-compliance"
    )


@pytest.mark.django_db
def test_statement_check_result_initial_str():
    statement_audit: StatementAudit = create_initial_statement_audit()
    statement_check_result: StatementCheckResult = (
        statement_audit.overview_statement_check_results.first()
    )

    assert (
        statement_check_result.__str__()
        == f"{statement_audit} | {statement_check_result.statement_check} [{statement_check_result.issue_identifier}]"
    )

    custom_statement_check_result: StatementCheckResult = (
        statement_audit.custom_statement_check_results.first()
    )

    assert (
        custom_statement_check_result.__str__()
        == f"{statement_audit} | Custom [{custom_statement_check_result.issue_identifier}]"
    )


@pytest.mark.django_db
def test_statement_audit_statement_check_results():
    """
    Tests statement audit statement_check_results contains the matching initial or
    retest statement check results.
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )

    assertQuerySetEqual(
        initial_statement_audit.statementcheckresultround_set.all(),
        initial_statement_audit.statement_check_results,
    )
    assertQuerySetEqual(
        twelve_week_statement_audit.statementcheckresultround_set.all(),
        twelve_week_statement_audit.statement_check_results,
    )


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
        ("custom", "custom"),
    ],
)
@pytest.mark.django_db
def test_statement_audit_specific_statement_check_results(type, attr):
    """
    Tests specific statement audit statement_check_results property contains the
    matching statement check results.
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )
    statement_check_results_initial: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=initial_statement_audit,
            type=type,
        )
    )
    statement_check_results_retest: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=twelve_week_statement_audit,
            type=type,
        )
    )

    assertQuerySetEqual(
        getattr(initial_statement_audit, f"{attr}_statement_check_results"),
        statement_check_results_initial,
    )
    assertQuerySetEqual(
        getattr(twelve_week_statement_audit, f"{attr}_statement_check_results"),
        statement_check_results_retest,
    )


@pytest.mark.django_db
def test_statement_audit_statement_check_result_initial():
    """
    Test StatementAudit.statement_cound_check returns the first overview check result.
    Only worked prior to 30 July 2025 when there was a second overview check.
    """
    with patch(
        "django.utils.timezone.now", Mock(return_value=PREVIOUS_STATEMENT_CHECKS_TIME)
    ):
        initial_statement_audit: StatementAudit = create_initial_statement_audit()
    statement_found_check_result_initial: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=initial_statement_audit,
            type=StatementCheck.Type.OVERVIEW,
        ).first()
    )

    assert (
        initial_statement_audit.statement_found_check
        == statement_found_check_result_initial
    )


@pytest.mark.django_db
def test_audit_statement_structure_check():
    """
    Tests audit statement_structure_check property.
    Only worked prior to 30 July 2025 when there was a second overview check.
    """
    with patch(
        "django.utils.timezone.now", Mock(return_value=PREVIOUS_STATEMENT_CHECKS_TIME)
    ):
        initial_statement_audit: StatementAudit = create_initial_statement_audit()
    statement_structure_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=initial_statement_audit,
            type=StatementCheck.Type.OVERVIEW,
        ).last()
    )

    assert (
        initial_statement_audit.statement_structure_check
        == statement_structure_check_result
    )


@pytest.mark.django_db
def test_statement_audit_overview_statement_checks_complete():
    """Tests statement_audit overview_statement_checks_complete property"""
    statement_audit: StatementAudit = create_initial_statement_audit()

    for statement_check_result in statement_audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert statement_audit.overview_statement_checks_complete is True

    for statement_check_result in statement_audit.overview_statement_check_results:
        statement_check_result.check_result_state = (
            StatementCheckResult.Result.NOT_TESTED
        )
        statement_check_result.save()
        break

    assert statement_audit.overview_statement_checks_complete is False


@pytest.mark.django_db
def test_statement_audit_failed_statement_check_results():
    """
    Tests a statement_audit.failed_statement_check_results contains the failed
    statement check results.
    """
    statement_audit: StatementAudit = create_initial_statement_audit()
    failed_statement_check_results: QuerySet[StatementCheckResultRound] = (
        StatementCheckResultRound.objects.filter(
            statement_audit=statement_audit,
            check_result_state=StatementCheckResultRound.Result.NO,
        )
    )

    assert failed_statement_check_results.count() == 1  # Custom issue
    assertQuerySetEqual(
        statement_audit.failed_statement_check_results, failed_statement_check_results
    )

    for statement_check_result_initial in StatementCheckResultRound.objects.filter(
        statement_audit=statement_audit
    ):
        statement_check_result_initial.check_result_state = (
            StatementCheckResultRound.Result.NO
        )
        statement_check_result_initial.save()
    failed_statement_check_results: QuerySet[StatementCheckResultRound] = (
        StatementCheckResultRound.objects.filter(
            statement_audit=statement_audit,
            check_result_state=StatementCheckResultRound.Result.NO,
        )
    )

    assert failed_statement_check_results.count() > 1
    assertQuerySetEqual(
        statement_audit.failed_statement_check_results, failed_statement_check_results
    )


@pytest.mark.parametrize(
    "type, attr",
    [
        ("overview", "overview"),
        ("website", "website"),
        ("compliance", "compliance"),
        ("non-accessible", "non_accessible"),
        ("preparation", "preparation"),
        ("feedback", "feedback"),
    ],
)
@pytest.mark.django_db
def test_statement_audit_contains_specific_outstanding_statement_check_results(
    type, attr
):
    """Tests statement audit contains specific outstanding statement check results."""
    statement_audit: StatementAudit = create_initial_statement_audit()
    for count, statement_check_result_initial in enumerate(
        StatementCheckResultRound.objects.filter(statement_audit=statement_audit)
    ):
        if count % 2 == 0:
            statement_check_result_initial.check_result_state = (
                StatementCheckResultRound.Result.YES
            )
        else:
            statement_check_result_initial.check_result_state = (
                StatementCheckResultRound.Result.NO
            )
        statement_check_result_initial.save()
    failed_statement_check_results: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=statement_audit,
            type=type,
            check_result_state=StatementCheckResultRound.Result.NO,
        )
    )

    assert failed_statement_check_results.count() > 0
    assertQuerySetEqual(
        getattr(statement_audit, f"{attr}_outstanding_statement_check_results"),
        failed_statement_check_results,
    )


@pytest.mark.django_db
def test_statement_audit_outstanding_statement_check_results_includes_new_failures():
    """
    Tests specific statement_audit outstanding_statement_check_results property
    contains new custom errors found for the first time on 12-week retest.
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )
    twelve_week_statement_check_result_retest: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=twelve_week_statement_audit,
            type=StatementCheck.Type.RETEST,
            public_comment="Custom issue found at 12-weeks",
        )
    )

    assert (
        twelve_week_statement_check_result_retest
        in twelve_week_statement_audit.outstanding_statement_check_results
    )


@pytest.mark.django_db
def test_statement_audit_all_overview_statement_checks_have_passed():
    """
    Tests statement_audit.all_overview_statement_checks_have_passed shows if all
    statement check results have passed on test or retest
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )

    assert initial_statement_audit.all_overview_statement_checks_have_passed is False

    overview_statement_check_result_initials: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=initial_statement_audit,
            type=StatementCheck.Type.OVERVIEW,
        )
    )
    for statement_check_result in overview_statement_check_result_initials:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert initial_statement_audit.all_overview_statement_checks_have_passed is True

    assert (
        twelve_week_statement_audit.all_overview_statement_checks_have_passed is False
    )

    overview_statement_check_result_retests: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=twelve_week_statement_audit,
            type=StatementCheck.Type.OVERVIEW,
        )
    )
    for statement_check_result in overview_statement_check_result_retests:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert twelve_week_statement_audit.all_overview_statement_checks_have_passed is True


@pytest.mark.django_db
def test_audit_overview_all_overview_statement_checks_have_passed_when_none():
    """
    Tests audit all overview statement checks have passed is false when
    there are no such checks.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case,
    )

    assert audit_overview.all_overview_statement_checks_have_passed is False


@pytest.mark.django_db
def test_fixed_statement_checks_are_returned():
    """
    Tests fixed statement checks are those which initially failed but passed on a
    retest.
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )

    initial_statement_check_result: StatementCheckResultRound = (
        initial_statement_audit.website_statement_check_results.first()
    )
    initial_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.NO
    )
    initial_statement_check_result.save()

    twelve_week_statement_check_result: StatementCheckResultRound = (
        initial_statement_check_result.twelve_week_retest
    )
    twelve_week_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.YES
    )
    twelve_week_statement_check_result.save()

    assert initial_statement_check_result != twelve_week_statement_check_result
    assert (
        initial_statement_audit.failed_statement_check_results.last()
        == initial_statement_check_result
    )
    assert (
        twelve_week_statement_audit.passed_statement_check_results.first()
        == twelve_week_statement_check_result
    )
    assert (
        twelve_week_statement_audit.fixed_statement_check_results.first()
        == twelve_week_statement_check_result
    )


@pytest.mark.django_db
def test_statement_check_start_end_date_range():
    """
    Test that an statement check within a date range returned.
    """
    StatementCheck.objects.all().delete()
    past_date: date = date(2020, 1, 1)
    current_date: date = date(2023, 1, 1)
    future_date: date = date(2024, 1, 1)
    wcag_definition: StatementCheck = StatementCheck.objects.create()
    StatementCheck.objects.create(date_end=past_date)
    StatementCheck.objects.create(date_start=future_date)

    assert StatementCheck.objects.all().count() == 3

    assert StatementCheck.objects.on_date(current_date).count() == 1

    assert StatementCheck.objects.on_date(current_date).first() == wcag_definition


@pytest.mark.django_db
def test_fixed_checks_count_at_12_week():
    """Test fixed checks count at 12-week retest"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 0

    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(
            wcag_audit=twelve_week_wcag_audit,
            wcag_check_result_initial__wcag_page_initial=wcag_page_initial,
        ).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.FIXED
    wcag_check_result_retest.save()

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 1

    wcag_page_initial.not_found = Boolean.YES
    wcag_page_initial.save()

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 0


@pytest.mark.django_db
def test_fixed_checks_count_in_equality_body_retests():
    """Test fixed checks count at equality body retest"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 0

    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(
            wcag_audit=twelve_week_wcag_audit,
            wcag_check_result_initial__wcag_page_initial=wcag_page_initial,
        ).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.FIXED
    wcag_check_result_retest.save()

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 1

    wcag_page_initial.not_found = Boolean.YES
    wcag_page_initial.save()

    assert twelve_week_wcag_audit.wcag_fixed_check_result_retests.count() == 0


@pytest.mark.django_db
def test_wcag_audit_previous_equality_body_retest():
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()

    assert initial_wcag_audit.previous_equality_body_retest is None

    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )

    assert twelve_week_wcag_audit.previous_equality_body_retest is None

    first_equality_body_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert (
        first_equality_body_wcag_audit.previous_equality_body_retest
        == twelve_week_wcag_audit
    )

    second_equality_body_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert (
        second_equality_body_wcag_audit.previous_equality_body_retest
        == first_equality_body_wcag_audit
    )


@pytest.mark.django_db
def test_wcag_page_retest_all_wcag_check_result_retests():
    create_simplified_case_with_initial_and_12_week_audits()
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial__page_type=WcagPageInitial.Type.HOME
    )

    assertQuerySetEqual(
        wcag_page_retest.all_wcag_check_result_retests,
        WcagCheckResultRetest.objects.filter(wcag_page_retest=wcag_page_retest),
    )


@pytest.mark.django_db
def test_wcag_page_retest_failed_wcag_check_result_retests():
    create_simplified_case_with_initial_and_12_week_audits()
    home_wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial__page_type=WcagPageInitial.Type.HOME
    )
    statement_wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial__page_type=WcagPageInitial.Type.STATEMENT
    )
    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(
            wcag_page_retest=home_wcag_page_retest
        ).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.NOT_FIXED
    wcag_check_result_retest.save()

    assert home_wcag_page_retest.failed_wcag_check_result_retests.count() == 1
    assert statement_wcag_page_retest.failed_wcag_check_result_retests.count() == 0


@pytest.mark.django_db
def test_audit_statement_pages():
    """Test audit statement pages"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    simplified_case: SimplifiedCase = wcag_audit.simplified_case
    audit_overview: AuditOverview = simplified_case.audit_overview

    assert not audit_overview.statement_pages

    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )

    assert audit_overview.statement_pages.count() == 1
    assert audit_overview.statement_pages.first() == statement_page

    statement_page.is_deleted = True
    statement_page.save()

    assert not audit_overview.statement_pages


@pytest.mark.django_db
def test_audit_accessibility_statement_found():
    """Test audit statement found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case,
    )

    assert audit_overview.accessibility_statement_found is False

    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=audit_overview,
        url=STATEMENT_LINK,
    )

    assert audit_overview.accessibility_statement_found is True

    statement_page.is_deleted = True
    statement_page.save()

    assert audit_overview.accessibility_statement_found is False


def test_statement_page_str():
    """
    Test the string representation of the statement page is the backup
    url or url.
    """
    statement_page: StatementPage = StatementPage()

    assert str(statement_page) == ""

    statement_page.backup_url = "backup"

    assert str(statement_page) == "backup"

    statement_page.url = "url"

    assert str(statement_page) == "url"


@pytest.mark.django_db
def test_latest_statement_link_found():
    """
    Test that the latest statement link is returned even when
    it is not on the latest statement page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    early_statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )
    StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )

    assert audit_overview.latest_statement_link is None

    early_statement_page.url = STATEMENT_LINK
    early_statement_page.save()

    assert audit_overview.latest_statement_link == STATEMENT_LINK


@pytest.mark.django_db
def test_wcag_page_retest_all_wcag_page_retests():
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    create_retest_wcag_audit(initial_wcag_audit=initial_wcag_audit)
    twelve_week_wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial__page_type=WcagPageInitial.Type.HOME
    )
    create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    all_wcag_page_retests_for_page: QuerySet[WcagPageRetest] = (
        WcagPageRetest.objects.filter(
            wcag_page_initial=twelve_week_wcag_page_retest.wcag_page_initial
        )
    )

    assertQuerySetEqual(
        twelve_week_wcag_page_retest.all_wcag_page_retests,
        all_wcag_page_retests_for_page,
    )


@pytest.mark.django_db
def test_retest_statement_check_results_label():
    """Test RetestStatementCheckResult.label"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    statement_check_result_round: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(statement_audit=statement_audit)
    )

    assert statement_check_result_round.label == "Custom"

    statement_check: StatementCheck = StatementCheck.objects.get(
        id=ACCESSIBILITY_PAGE_STATEMENT_CHECK_ID
    )
    statement_check_result_round.statement_check = statement_check
    statement_check_result_round.save()

    assert statement_check_result_round.label == "Is there an accessibility page?"


@pytest.mark.django_db
def test_wcag_check_result_initial_matching_wcag_with_notes_check_results():
    """
    Test CheckResult.matching_wcag_with_retest_notes_check_results returns other
    check results on the other pages with the same WCAG definition and retest notes
    """
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    home_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    contact_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.CONTACT
    )
    form_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.FORM
    )
    first_check_result: WcagCheckResultInitial = WcagCheckResultInitial.objects.create(
        wcag_audit=initial_wcag_audit,
        wcag_page_initial=home_page,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    second_check_result: WcagCheckResultInitial = WcagCheckResultInitial.objects.create(
        wcag_audit=initial_wcag_audit,
        wcag_page_initial=contact_page,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        notes="Sample note",
    )
    third_check_result: WcagCheckResultInitial = WcagCheckResultInitial.objects.create(
        wcag_audit=initial_wcag_audit,
        wcag_page_initial=form_page,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
        notes="Another note",
    )

    assert first_check_result.matching_wcag_with_notes_check_results.count() == 2
    assert (
        first_check_result.matching_wcag_with_notes_check_results.first()
        == second_check_result
    )
    assert (
        first_check_result.matching_wcag_with_notes_check_results.last()
        == third_check_result
    )


@pytest.mark.django_db
def test_retest_check_result_matching_wcag_retest_check_results():
    """
    Test RetestCheckResult.matching_wcag_retest_check_results returns
    retest check results on the other pages with the same WCAG definition
    and with retest notes
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    initial_wcag_audit: WcagAudit = simplified_case.audit_overview.initial_wcag_audit
    first_wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.all().first()
    )
    wcag_check_result_initial: WcagCheckResultInitial = (
        first_wcag_check_result_retest.wcag_check_result_initial
    )
    create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )

    assert first_wcag_check_result_retest.other_wcag_check_result_retests.count() == 2
    assertQuerySetEqual(
        first_wcag_check_result_retest.other_wcag_check_result_retests.order_by("id"),
        WcagCheckResultRetest.objects.filter(
            wcag_check_result_initial=wcag_check_result_initial
        )
        .exclude(id=first_wcag_check_result_retest.id)
        .order_by("id"),
    )


@pytest.mark.django_db
def test_check_result_issue_identifier():
    """Test check result gets unique identifier"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case_1: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit_1: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case_1
    )
    wcag_page_initial_1: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit_1, page_type=WcagPageInitial.Type.HOME
    )
    wcag_check_result_initial_1a: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit_1,
            wcag_page_initial=wcag_page_initial_1,
            check_result_state=WcagCheckResultInitial.Result.ERROR,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
    )

    assert wcag_check_result_initial_1a.issue_identifier == "1-A-1"

    wcag_check_result_initial_1b: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit_1,
            wcag_page_initial=wcag_page_initial_1,
            check_result_state=WcagCheckResultInitial.Result.ERROR,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
    )

    assert wcag_check_result_initial_1b.issue_identifier == "1-A-2"

    simplified_case_2: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit_2: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case_2
    )
    wcag_page_initial_2: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit_2, page_type=WcagPageInitial.Type.HOME
    )
    wcag_check_result_initial_2a: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit_2,
            wcag_page_initial=wcag_page_initial_2,
            check_result_state=WcagCheckResultInitial.Result.ERROR,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
    )

    assert wcag_check_result_initial_2a.issue_identifier == "2-A-1"


@pytest.mark.django_db
def test_wcag_issue_identifier():
    """Test populating issue identifier for WCAG check result"""

    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit,
            wcag_page_initial=wcag_page_initial,
            check_result_state=WcagCheckResultInitial.Result.ERROR,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
    )

    assert wcag_check_result_initial.issue_identifier == "1-A-1"


@pytest.mark.django_db
def test_statement_issue_identifier():
    """Test populating issue identifier for statement check results"""

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    statement_check_result_round: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            type=statement_check.type,
            statement_check=statement_check,
        )
    )

    assert statement_check_result_round.issue_identifier == "1-S-1"

    custom_statement_check_result_round: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            public_comment="Custom statement issue",
        )
    )

    assert custom_statement_check_result_round.issue_identifier == "1-SC-2"


@pytest.mark.django_db
def test_statement_audit_new_12_week_custom_statement_check_results():
    """Test statement custom check result found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    new_12_week_custom_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            type=StatementCheck.Type.RETEST,
            public_comment="12-week custom statement issue",
        )
    )

    assert statement_audit.new_12_week_custom_statement_check_results.count() == 1
    assert (
        statement_audit.new_12_week_custom_statement_check_results.first()
        == new_12_week_custom_check_result
    )
