"""
Tests for audits views
"""

import io
from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from moto import mock_aws
from pytest_django.asserts import assertContains, assertNotContains

from accessibility_monitoring_platform.apps.common.models import Boolean

from ...cases.models import CaseFile
from ...cases.utils import S3ReadWriteFile
from ...reports.models import Report
from ...simplified.models import (
    CaseCompliance,
    CaseEvent,
    SimplifiedCase,
    SimplifiedEventHistory,
)
from ..models import (
    Audit,
    AuditOverview,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementCheckResultRound,
    StatementPage,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultInitialNotesHistory,
    WcagCheckResultRetest,
    WcagCheckResultRetestNotesHistory,
    WcagDefinition,
    WcagPageInitial,
    WcagPageRetest,
)
from ..utils import (
    create_checkresults_for_wcag_audit_retest,
    create_mandatory_pages_for_new_audit,
)
from .create_test_data import (
    WCAG_TYPE_AXE_NAME,
    WCAG_TYPE_PDF_NAME,
    create_equality_body_audits,
    create_initial_statement_audit,
    create_initial_wcag_audit,
    create_retest_statement_audit,
    create_retest_wcag_audit,
    create_simplified_case_with_initial_and_12_week_audits,
)

TODAY = date.today()
EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"
CHECK_RESULT_NOTES: str = "Check result notes"
FIXED_ERROR_NOTES: str = "Fixed error notes"
UNFIXED_ERROR_NOTES: str = "Unfixed error notes"
WCAG_DEFINITION_TYPE: str = "axe"
WCAG_DEFINITION_NAME: str = "WCAG definiton name"
WCAG_DEFINITION_URL: str = "https://example.com"
PAGE_RETEST_NOTES: str = "Retest notes"
ORGANISATION_NAME: str = "Organisation name"
CUSTOM_STATEMENT_ISSUE: str = "Custom statement issue"
STATEMENT_CHECK_LABEL: str = "Test statement check"
STATEMENT_CHECK_TYPE: str = "custom"
STATEMENT_CHECK_SUCCESS_CRITERIA: str = "Success criteria"
STATEMENT_CHECK_REPORT_TEXT: str = "Report text"
STATEMENT_PAGE_URL: str = "https://example.com/statement"
WCAG_DEFINITION_HINT: str = "WCAG definition hint text"
PAGE_LOCATION: str = "Press button then click on link"
STATEMENT_CHECK_INITIAL_COMMENT: str = "Statement check initial comment"
STATEMENT_CHECK_CUSTOM_COMMENT: str = "Statement check custom comment"
NEW_12_WEEK_CUSTOM_RETEST_COMMENT: str = "New 12-week custom retest comment"
HISTORIC_RETEST_NOTES: str = "Historic retest notes"
HISTORIC_CHECK_RESULT_NOTES: str = "Historic check result notes"
CASE_FILE_NAME: str = "case_file.txt"
CASE_FILE_CONTENT: str = "Case file content"
FIRST_STATEMENT_CHECK_RESULT_ID: int = 1
SECOND_STATEMENT_CHECK_RESULT_ID: int = 2
STATEMENT_CHECK_RESULT_COMMENT: str = "Statement check result comment"


def create_audit() -> Audit:
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    return audit


def create_wcag_audit() -> Audit:
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    return audit


def create_audit_and_pages() -> Audit:
    audit: Audit = create_audit()
    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=audit.simplified_case
    )
    create_mandatory_pages_for_new_audit(wcag_audit=wcag_audit)
    return audit


def create_audit_and_wcag() -> Audit:
    audit: Audit = create_audit_and_pages()
    WcagDefinition.objects.all().delete()
    WcagDefinition.objects.create(
        id=1, type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    WcagDefinition.objects.create(
        id=2, type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )
    return audit


def create_audit_and_statement_check_results() -> Audit:
    """Create an audit with all types of statement checks"""
    audit: Audit = create_audit_and_wcag()
    for count, statement_check in enumerate(StatementCheck.objects.on_date(TODAY)):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )
    StatementCheckResult.objects.create(
        audit=audit,
        report_comment="Custom statement issue",
    )
    return audit


def create_equality_body_retest() -> Retest:
    """Create equality body retest and associated data"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_page: RetestPage = RetestPage.objects.create(
        retest=retest,
        page=page,
    )
    RetestCheckResult.objects.create(
        retest=retest,
        retest_page=retest_page,
        check_result=check_result,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
    )
    return retest


def test_restore_wcag_page_initial_view(admin_client):
    """Test that restore WCAG page initial view restores audit"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit, is_deleted=True
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:restore-page",
            kwargs={"pk": wcag_page_initial.id},
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-pages",
        kwargs=wcag_audit_pk,
    )

    wcag_page_initial_from_db: WcagPageInitial = WcagPageInitial.objects.get(
        id=wcag_page_initial.id
    )

    assert wcag_page_initial_from_db.is_deleted is False


def test_create_audit_redirects(admin_client):
    """Test that audit create redirects to audit metadata"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse("audits:edit-audit-metadata", kwargs={"pk": 1})


def test_create_audit_does_not_create_a_duplicate(admin_client):
    """Test that audit create does not create a duplicate audit"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    WcagAudit.objects.create(simplified_case=simplified_case)
    AuditOverview.objects.create(simplified_case=simplified_case)

    assert WcagAudit.objects.filter(simplified_case=simplified_case).count() == 1

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs={"case_id": simplified_case.id}),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302
    assert WcagAudit.objects.filter(simplified_case=simplified_case).count() == 1


def test_create_audit_creates_case_event(admin_client):
    """Test that audit create creates a case event"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302
    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=simplified_case
    )
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.CREATE_AUDIT
    assert case_event.message == "Started test"


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:edit-audit-metadata", "Initial test metadata"),
        ("audits:edit-audit-pages", "Add or remove pages"),
        ("audits:edit-website-decision", "Compliance decision"),
        ("audits:edit-audit-wcag-summary", "WCAG summary"),
    ],
)
def test_initial_wcag_audit_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the initial wcag audit view page loads"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    create_initial_statement_audit(simplified_case=wcag_audit.simplified_case)

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=wcag_audit_pk))

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "audits:edit-statement-decision",
            "Initial statement compliance decision",
        ),
        ("audits:edit-audit-statement-summary", "Statement summary"),
    ],
)
def test_initial_statement_audit_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the initial statement audit view page loads"""
    statement_audit: StatementAudit = create_initial_statement_audit()
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=statement_audit_pk)
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:edit-audit-retest-wcag-summary", "WCAG summary"),
        ("audits:edit-audit-retest-metadata", "12-week retest metadata"),
        (
            "audits:edit-audit-retest-website-decision",
            "Compliance decision",
        ),
    ],
)
def test_twelve_week_wcag_audit_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the twelve-week WCAG audit view page loads"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_wcag_audit_pk: dict[str, int] = {
        "pk": simplified_case.audit_overview.first_wcag_audit_12_week_retest.id
    }

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=twelve_week_wcag_audit_pk)
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:edit-audit-retest-statement-summary", "Statement summary"),
        (
            "audits:edit-audit-retest-statement-decision",
            "Compliance decision",
        ),
    ],
)
def test_twelve_week_statement_audit_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the twelve-week statement audit view page loads"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": simplified_case.audit_overview.first_statement_audit_12_week_retest.id
    }

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=twelve_week_statement_audit_pk)
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "audits:edit-retest-statement-overview",
            "Statement overview",
        ),
        (
            "audits:edit-retest-statement-website",
            "Statement information",
        ),
        (
            "audits:edit-retest-statement-compliance",
            "Compliance status",
        ),
        (
            "audits:edit-retest-statement-non-accessible",
            "Non-accessible content",
        ),
        (
            "audits:edit-retest-statement-preparation",
            "Statement preparation",
        ),
        (
            "audits:edit-retest-statement-feedback",
            "Feedback and enforcement procedure",
        ),
        (
            "audits:edit-retest-statement-custom",
            "Custom issues",
        ),
    ],
)
def test_twelve_week_audit_statement_check_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the audit with statement checks-specific view page loads"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": simplified_case.audit_overview.first_statement_audit_12_week_retest.id
    }

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=twelve_week_statement_audit_pk)
    )

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-audit-metadata", "save", "audits:edit-audit-metadata"),
        ("audits:edit-audit-metadata", "save_continue", "audits:edit-audit-pages"),
        ("audits:edit-website-decision", "save", "audits:edit-website-decision"),
        (
            "audits:edit-website-decision",
            "save_continue",
            "audits:edit-audit-wcag-summary",
        ),
        ("audits:edit-audit-wcag-summary", "save", "audits:edit-audit-wcag-summary"),
        (
            "audits:edit-audit-wcag-summary",
            "save_continue",
            "audits:edit-statement-pages",
        ),
    ],
)
def test_initial_wcag_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful initial WCAG audit update redirects based on the
    button pressed
    """
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    initial_wcag_audit_pk: dict[str, int] = {"pk": initial_wcag_audit.id}
    create_initial_statement_audit(simplified_case=initial_wcag_audit.simplified_case)

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=initial_wcag_audit_pk),
        {
            "version": initial_wcag_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=initial_wcag_audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-statement-decision", "save", "audits:edit-statement-decision"),
        (
            "audits:edit-statement-decision",
            "save_continue",
            "audits:edit-audit-statement-summary",
        ),
        (
            "audits:edit-audit-statement-summary",
            "save",
            "audits:edit-audit-statement-summary",
        ),
        (
            "audits:edit-audit-statement-summary",
            "save_continue",
            "simplified:edit-create-report",
        ),
    ],
)
def test_initial_statement_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful initial statement audit update redirects based on the
    button pressed
    """
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    initial_statement_audit: StatementAudit = create_initial_statement_audit(
        simplified_case=initial_wcag_audit.simplified_case
    )
    initial_statement_audit_pk: dict[str, int] = {"pk": initial_statement_audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=initial_statement_audit_pk),
        {
            "version": initial_statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=initial_statement_audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        (
            "audits:edit-audit-retest-metadata",
            "save",
            "audits:edit-audit-retest-metadata",
        ),
        (
            "audits:edit-audit-retest-metadata",
            "save_continue",
            "audits:edit-audit-retest-pages",
        ),
        (
            "audits:edit-audit-retest-pages",
            "save",
            "audits:edit-audit-retest-pages",
        ),
        (
            "audits:edit-audit-retest-website-decision",
            "save",
            "audits:edit-audit-retest-website-decision",
        ),
        (
            "audits:edit-audit-retest-website-decision",
            "save_continue",
            "audits:edit-audit-retest-wcag-summary",
        ),
        (
            "audits:edit-audit-retest-wcag-summary",
            "save",
            "audits:edit-audit-retest-wcag-summary",
        ),
        (
            "audits:edit-audit-retest-wcag-summary",
            "save_continue",
            "audits:edit-audit-retest-statement-pages",
        ),
    ],
)
def test_twelve_week_wcag_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful twelve week WCAG audit update redirects based on the
    button pressed
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_wcag_audit: WcagAudit = (
        simplified_case.audit_overview.first_wcag_audit_12_week_retest
    )
    twelve_week_wcag_audit_pk: dict[str, int] = {"pk": twelve_week_wcag_audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=twelve_week_wcag_audit_pk),
        {
            "version": twelve_week_wcag_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=twelve_week_wcag_audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        (
            "audits:edit-audit-retest-statement-decision",
            "save",
            "audits:edit-audit-retest-statement-decision",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "save_continue",
            "audits:edit-audit-retest-statement-summary",
        ),
        (
            "audits:edit-audit-retest-statement-summary",
            "save",
            "audits:edit-audit-retest-statement-summary",
        ),
        (
            "audits:edit-audit-retest-statement-summary",
            "save_continue",
            "simplified:edit-review-changes",
        ),
    ],
)
def test_twelve_week_statement_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful twelve week statement audit update redirects based on
    the button pressed
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=twelve_week_statement_audit_pk),
        {
            "version": twelve_week_statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    if expected_redirect_path_name == "simplified:edit-review-changes":
        expected_path: str = reverse(
            expected_redirect_path_name, kwargs={"pk": simplified_case.id}
        )
    else:
        expected_path: str = reverse(
            expected_redirect_path_name, kwargs=twelve_week_statement_audit_pk
        )
    assert response.url == expected_path


def test_audit_statement_summary_page_redirect_when_report_exists(admin_client):
    """
    Test that audit statement summary page redirects to Report ready for QA
    when a report exists
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    case_pk: dict[str, int] = {"pk": simplified_case.id}
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-audit-statement-summary", kwargs=twelve_week_statement_audit_pk
        ),
        {
            "version": twelve_week_statement_audit.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("simplified:edit-report-ready-for-qa", kwargs=case_pk)
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-statement-pages", "save", "audits:edit-statement-pages"),
        (
            "audits:edit-statement-pages",
            "save_continue",
            "audits:initial-statement-backup",
        ),
        ("audits:initial-statement-backup", "save", "audits:initial-statement-backup"),
        (
            "audits:initial-statement-backup",
            "save_continue",
            "audits:edit-statement-overview",
        ),
        (
            "audits:edit-audit-retest-statement-pages",
            "save",
            "audits:edit-audit-retest-statement-pages",
        ),
        (
            "audits:edit-audit-retest-statement-pages",
            "save_continue",
            "audits:edit-audit-retest-statement-backup",
        ),
        (
            "audits:edit-audit-retest-statement-backup",
            "save",
            "audits:edit-audit-retest-statement-backup",
        ),
        (
            "audits:edit-audit-retest-statement-backup",
            "save_continue",
            "audits:edit-retest-statement-overview",
        ),
    ],
)
def test_audit_statement_pages_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful audit statement pages update redirects based
    on the button pressed (with statement checks)
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=twelve_week_statement_audit_pk),
        {
            "version": twelve_week_statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=twelve_week_statement_audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-statement-pages",
        "audits:edit-audit-retest-statement-pages",
    ],
)
def test_add_statement_link(url_name, admin_client):
    """Test that add statement link views saves URL"""
    statement_audit: StatementAudit = create_initial_statement_audit()

    response: HttpResponse = admin_client.post(
        reverse(url_name, kwargs={"pk": statement_audit.id}),
        {
            "version": statement_audit.version,
            "statement_url": STATEMENT_PAGE_URL,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    statement_page: StatementPage = StatementPage.objects.get(
        simplified_case=statement_audit.simplified_case
    )

    assert statement_page.url == STATEMENT_PAGE_URL


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:initial-statement-backup",
        "audits:edit-audit-retest-statement-backup",
    ],
)
@mock_aws
def test_add_statement_backup(url_name, admin_client):
    """Test that audit statement backup saves to s3"""
    statement_audit: StatementAudit = create_initial_statement_audit()

    in_memory_file: InMemoryUploadedFile = InMemoryUploadedFile(
        io.BytesIO(CASE_FILE_CONTENT.encode()),
        field_name="name",
        name=CASE_FILE_NAME,
        content_type="text",
        size=len(CASE_FILE_CONTENT),
        charset=None,
    )

    response: HttpResponse = admin_client.post(
        reverse(url_name, kwargs={"pk": statement_audit.simplified_case.id}),
        {
            "version": statement_audit.version,
            "file_to_upload": in_memory_file,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    case_file: CaseFile = CaseFile.objects.get(
        base_case=statement_audit.simplified_case
    )

    assert case_file.name == CASE_FILE_NAME

    s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
    data_s3: bytes | str = s3_read_write.read_case_file_from_s3(case_file=case_file)

    assert isinstance(data_s3, bytes)
    assert data_s3.decode() == CASE_FILE_CONTENT


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        (
            "audits:edit-statement-overview",
            "save",
            "audits:edit-statement-overview",
        ),
        (
            "audits:edit-statement-overview",
            "save_continue",
            "audits:edit-statement-custom",
        ),
        (
            "audits:edit-statement-website",
            "save",
            "audits:edit-statement-website",
        ),
        (
            "audits:edit-statement-website",
            "save_continue",
            "audits:edit-statement-compliance",
        ),
        (
            "audits:edit-statement-compliance",
            "save",
            "audits:edit-statement-compliance",
        ),
        (
            "audits:edit-statement-compliance",
            "save_continue",
            "audits:edit-statement-non-accessible",
        ),
        (
            "audits:edit-statement-non-accessible",
            "save",
            "audits:edit-statement-non-accessible",
        ),
        (
            "audits:edit-statement-non-accessible",
            "save_continue",
            "audits:edit-statement-preparation",
        ),
        (
            "audits:edit-statement-preparation",
            "save",
            "audits:edit-statement-preparation",
        ),
        (
            "audits:edit-statement-preparation",
            "save_continue",
            "audits:edit-statement-feedback",
        ),
        (
            "audits:edit-statement-feedback",
            "save",
            "audits:edit-statement-feedback",
        ),
        (
            "audits:edit-statement-feedback",
            "save_continue",
            "audits:edit-statement-disproportionate",
        ),
        (
            "audits:edit-statement-disproportionate",
            "save",
            "audits:edit-statement-disproportionate",
        ),
        (
            "audits:edit-statement-disproportionate",
            "save_continue",
            "audits:edit-statement-custom",
        ),
        (
            "audits:edit-statement-custom",
            "save",
            "audits:edit-statement-custom",
        ),
        (
            "audits:edit-statement-custom",
            "save_continue",
            "audits:edit-initial-disproportionate-burden",
        ),
        (
            "audits:edit-initial-disproportionate-burden",
            "save",
            "audits:edit-initial-disproportionate-burden",
        ),
        (
            "audits:edit-initial-disproportionate-burden",
            "save_continue",
            "audits:edit-statement-decision",
        ),
    ],
)
def test_initial_audit_statement_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful initial statement audit statement-content page update
    redirects based on the button pressed
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    initial_statement_audit: StatementAudit = (
        simplified_case.audit_overview.statement_audit_initial
    )
    initial_statement_audit_pk: dict[str, int] = {"pk": initial_statement_audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=initial_statement_audit_pk),
        {
            "version": initial_statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=initial_statement_audit_pk
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        (
            "audits:edit-audit-retest-website-decision",
            "save_continue",
            "audits:edit-audit-retest-wcag-summary",
        ),
        (
            "audits:edit-audit-retest-statement-pages",
            "save",
            "audits:edit-audit-retest-statement-pages",
        ),
        (
            "audits:edit-audit-retest-statement-pages",
            "save_continue",
            "audits:edit-audit-retest-statement-backup",
        ),
        (
            "audits:edit-audit-retest-statement-backup",
            "save",
            "audits:edit-audit-retest-statement-backup",
        ),
        (
            "audits:edit-audit-retest-statement-backup",
            "save_continue",
            "audits:edit-retest-statement-overview",
        ),
        (
            "audits:edit-retest-statement-overview",
            "save",
            "audits:edit-retest-statement-overview",
        ),
        (
            "audits:edit-retest-statement-overview",
            "save_continue",
            "audits:edit-retest-statement-custom",
        ),
        (
            "audits:edit-retest-statement-website",
            "save",
            "audits:edit-retest-statement-website",
        ),
        (
            "audits:edit-retest-statement-website",
            "save_continue",
            "audits:edit-retest-statement-compliance",
        ),
        (
            "audits:edit-retest-statement-compliance",
            "save",
            "audits:edit-retest-statement-compliance",
        ),
        (
            "audits:edit-retest-statement-compliance",
            "save_continue",
            "audits:edit-retest-statement-non-accessible",
        ),
        (
            "audits:edit-retest-statement-non-accessible",
            "save",
            "audits:edit-retest-statement-non-accessible",
        ),
        (
            "audits:edit-retest-statement-non-accessible",
            "save_continue",
            "audits:edit-retest-statement-preparation",
        ),
        (
            "audits:edit-retest-statement-preparation",
            "save",
            "audits:edit-retest-statement-preparation",
        ),
        (
            "audits:edit-retest-statement-preparation",
            "save_continue",
            "audits:edit-retest-statement-feedback",
        ),
        (
            "audits:edit-retest-statement-feedback",
            "save",
            "audits:edit-retest-statement-feedback",
        ),
        (
            "audits:edit-retest-statement-feedback",
            "save_continue",
            "audits:edit-retest-statement-disproportionate",
        ),
        (
            "audits:edit-retest-statement-disproportionate",
            "save",
            "audits:edit-retest-statement-disproportionate",
        ),
        (
            "audits:edit-retest-statement-disproportionate",
            "save_continue",
            "audits:edit-retest-statement-custom",
        ),
        (
            "audits:edit-retest-statement-custom",
            "save",
            "audits:edit-retest-statement-custom",
        ),
        (
            "audits:edit-retest-statement-custom",
            "save_continue",
            "audits:edit-twelve-week-disproportionate-burden",
        ),
        (
            "audits:edit-twelve-week-disproportionate-burden",
            "save",
            "audits:edit-twelve-week-disproportionate-burden",
        ),
        (
            "audits:edit-twelve-week-disproportionate-burden",
            "save_continue",
            "audits:edit-audit-retest-statement-decision",
        ),
    ],
)
def test_twelve_week_audit_statement_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful twelve-week statement audit statement-content page update
    redirects based on the button pressed
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=twelve_week_statement_audit_pk),
        {
            "version": twelve_week_statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        expected_redirect_path_name, kwargs=twelve_week_statement_audit_pk
    )
    assert response.url == expected_path


def test_audit_edit_statement_overview_redirects_to_statement_website(
    admin_client,
):
    """
    Test that a successful audit statement overview update redirects to
    statement information if the overiew checks have passed
    """
    statement_audit: StatementAudit = create_initial_statement_audit()
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}
    for statement_check_result in StatementCheckResultRound.objects.filter(
        statement_audit=statement_audit, type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=statement_audit_pk),
        {
            "version": statement_audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-statement-website", kwargs=statement_audit_pk
    )
    assert response.url == expected_path


def test_audit_edit_statement_overview_updates_when_no_statement_exists(
    admin_client,
):
    """Test that audit statement overview update updates when no page exists"""
    statement_audit: StatementAudit = create_initial_statement_audit()
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=statement_audit_pk),
        {
            "version": statement_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "statement_overview_complete_date": "on",
        },
    )

    assert response.status_code == 302

    statement_audit_from_db: StatementAudit = StatementAudit.objects.get(
        id=statement_audit.id
    )

    assert statement_audit_from_db.statement_overview_complete_date == date.today()


def test_audit_edit_statement_overview_updates_case_status(
    admin_client,
):
    """
    Test that a successful audit statement overview update updates case
    status and check results
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = simplified_case.audit_overview.wcag_audit_initial
    wcag_audit.compliance_state = WcagAudit.WebsiteCompliance.COMPLIANT
    wcag_audit.save()
    statement_audit: StatementAudit = (
        simplified_case.audit_overview.statement_audit_initial
    )
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}
    # statement_audit.compliance_state = StatementAudit.StatementCompliance.COMPLIANT
    # statement_audit.save()
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.TEST_IN_PROGRESS

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=statement_audit_pk),
        {
            "version": statement_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-check_result_state": "yes",
            "form-0-public_comment": "",
            "form-1-id": "2",
            "form-1-check_result_state": "no",
            "form-1-public_comment": "",
        },
    )

    assert response.status_code == 302

    statement_audit_from_db: StatementAudit = StatementAudit.objects.get(
        id=statement_audit.id
    )
    assert (
        statement_audit_from_db.simplified_case.status
        == SimplifiedCase.Status.REPORT_IN_PROGRESS
    )

    statement_checkresult_1: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=1)
    )

    assert statement_checkresult_1.check_result_state == "yes"

    statement_checkresult_2: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=2)
    )

    assert statement_checkresult_2.check_result_state == "no"


def test_audit_retest_statement_overview_updates_when_no_statement_exists(
    admin_client,
):
    """
    Test that audit retest statement overview update updates when no page exists
    """
    statement_audit: StatementAudit = create_retest_statement_audit()
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-statement-overview", kwargs=statement_audit_pk),
        {
            "version": statement_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "statement_overview_complete_date": "on",
        },
    )

    assert response.status_code == 302

    statement_audit_from_db: StatementAudit = StatementAudit.objects.get(
        id=statement_audit.id
    )

    assert statement_audit_from_db.statement_overview_complete_date == date.today()


def test_audit_retest_statement_overview_no_statement(
    admin_client,
):
    """
    Test that the audit retest statement overview page shows checks
    even if there is no statement page.
    """
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-retest-statement-overview",
            kwargs=twelve_week_statement_audit_pk,
        ),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<label class="govuk-label"><b>Success criteria</b></label>""",
        html=True,
    )


def test_audit_retest_statement_overview_updates_statement_checkresult(
    admin_client,
):
    """
    Test that a successful audit retest statement overview update updates
    check results
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=simplified_case.audit_overview,
        added_stage=StatementPage.AddedStage.INITIAL,
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-statement-overview",
            kwargs=twelve_week_statement_audit_pk,
        ),
        {
            "version": twelve_week_statement_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": f"{FIRST_STATEMENT_CHECK_RESULT_ID}",
            "form-0-check_result_state": "yes",
            "form-0-auditor_information": f"{STATEMENT_CHECK_RESULT_COMMENT}",
            "form-1-id": f"{SECOND_STATEMENT_CHECK_RESULT_ID}",
            "form-1-check_result_state": "no",
            "form-1-auditor_information": "",
        },
    )

    assert response.status_code == 302

    statement_checkresult_1: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=FIRST_STATEMENT_CHECK_RESULT_ID)
    )

    assert (
        statement_checkresult_1.check_result_state
        == StatementCheckResultRound.Result.YES
    )
    assert statement_checkresult_1.auditor_information == STATEMENT_CHECK_RESULT_COMMENT

    statement_checkresult_2: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=SECOND_STATEMENT_CHECK_RESULT_ID)
    )

    assert (
        statement_checkresult_2.check_result_state
        == StatementCheckResultRound.Result.NO
    )


def test_audit_retest_statement_overview_updates_statement_checkresult_no_initial_statement(
    admin_client,
):
    """
    Test that a successful audit retest statement overview update updates
    check results when no initial statement was found
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()
    twelve_week_statement_audit: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    twelve_week_statement_audit_pk: dict[str, int] = {
        "pk": twelve_week_statement_audit.id
    }

    StatementPage.objects.create(
        simplified_case=simplified_case,
        audit_overview=simplified_case.audit_overview,
        added_stage=StatementPage.AddedStage.TWELVE_WEEK,
        url="https://www.website.com/statement",
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-statement-overview",
            kwargs=twelve_week_statement_audit_pk,
        ),
        {
            "version": twelve_week_statement_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": f"{FIRST_STATEMENT_CHECK_RESULT_ID}",
            "form-0-check_result_state": "yes",
            "form-0-auditor_information": f"{STATEMENT_CHECK_RESULT_COMMENT}",
            "form-1-id": f"{SECOND_STATEMENT_CHECK_RESULT_ID}",
            "form-1-check_result_state": "no",
            "form-1-auditor_information": "",
        },
    )

    assert response.status_code == 302

    statement_checkresult_1: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=FIRST_STATEMENT_CHECK_RESULT_ID)
    )

    assert (
        statement_checkresult_1.check_result_state
        == StatementCheckResultRound.Result.YES
    )
    assert statement_checkresult_1.auditor_information == STATEMENT_CHECK_RESULT_COMMENT

    statement_checkresult_2: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=SECOND_STATEMENT_CHECK_RESULT_ID)
    )

    assert (
        statement_checkresult_2.check_result_state
        == StatementCheckResultRound.Result.NO
    )


def test_retest_date_change_creates_case_event(admin_client):
    """Test that changing the retest date creates a case event"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    twelve_week_wcag_audit_pk: dict[str, int] = {"pk": twelve_week_wcag_audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-metadata", kwargs=twelve_week_wcag_audit_pk),
        {
            "date_of_test_0": 30,
            "date_of_test_1": 11,
            "date_of_test_2": 2022,
            "save": "Save",
            "version": twelve_week_wcag_audit.version,
        },
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=twelve_week_wcag_audit.simplified_case
    )
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.START_RETEST
    assert case_event.message == "Started retest (date set to 30 November 2022)"


def test_retest_metadata_skips_to_statement_when_no_psb_response(admin_client):
    """
    Test save and continue button causes user to skip to statement pages
    when no response was received from public sector body.
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    simplified_case.no_psb_contact = Boolean.YES
    simplified_case.save()
    twelve_week_wcag_audit: WcagAudit = (
        simplified_case.audit_overview.first_wcag_audit_12_week_retest
    )
    twelve_week_statement_audit: WcagAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-audit-retest-metadata",
            kwargs={"pk": twelve_week_wcag_audit.id},
        ),
        {
            "version": twelve_week_wcag_audit.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-audit-retest-statement-pages",
        kwargs={"pk": twelve_week_statement_audit.id},
    )
    assert response.url == expected_path


@pytest.mark.parametrize(
    "button_name, expected_redirect_path_name",
    [
        ("save", "audits:edit-audit-pages"),
        ("save_continue", "audits:edit-website-decision"),
    ],
)
def test_pages_redirects_based_on_button_pressed(
    button_name, expected_redirect_path_name, admin_client
):
    """Test that a successful audit update redirects based on the button pressed"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs=wcag_audit_pk),
        {
            "version": wcag_audit.version,
            button_name: "Button value",
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=wcag_audit_pk)
    assert response.url == expected_path


def test_standard_pages_appear_on_pages_page(admin_client):
    """
    Test that all the standard pages appear on the pages page.
    Also that the 'Form is on contact page' field appears.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
    )
    assert response.status_code == 200
    assertContains(
        response, """<h2 class="govuk-heading-m">Home page</h2>""", html=True
    )
    assertContains(
        response, """<h2 class="govuk-heading-m">Contact page</h2>""", html=True
    )
    assertContains(response, "Form is on contact page")
    assertContains(
        response,
        """<h2 class="govuk-heading-m">Accessibility statement page</h2>""",
        html=True,
    )
    assertContains(response, """<h2 class="govuk-heading-m">PDF</h2>""", html=True)
    assertContains(
        response, """<h2 class="govuk-heading-m">Form page</h2>""", html=True
    )


def test_two_extra_pages_appear_on_pages_page(admin_client):
    """
    Test that two extra pages appear on the pages page when no extra pages
    have yet been created.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.EXTRA
    )
    WcagCheckResultInitial.objects.filter(wcag_page_initial=wcag_page_initial).delete()
    wcag_page_initial.delete()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
    )
    assert response.status_code == 200
    assertContains(
        response,
        """<h2 id="extra-page-1" class="govuk-heading-m">Page 1</h2>""",
        html=True,
    )
    assertContains(
        response,
        """<h2 id="extra-page-2" class="govuk-heading-m">Page 2</h2>""",
        html=True,
    )

    WcagPageInitial.objects.create(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.EXTRA
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        """<h2 id="extra-page-2" class="govuk-heading-m">Page 2</h2>""",
        html=True,
    )


def test_add_extra_page_form_appears(admin_client):
    """
    Test that pressing the save and create additional page button adds an extra page form
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.EXTRA
    )
    WcagCheckResultInitial.objects.filter(wcag_page_initial=wcag_page_initial).delete()
    wcag_page_initial.delete()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": wcag_audit.version,
            "add_extra": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Page 1")
    assertNotContains(response, "Page 2")


def test_add_extra_page(admin_client):
    """Test adding an extra page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "1",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "extra-0-id": "",
            "extra-0-name": EXTRA_PAGE_NAME,
            "extra-0-url": EXTRA_PAGE_URL,
            "version": wcag_audit.version,
            "save_continue": "Save and continue",
        },
        follow=True,
    )
    assert response.status_code == 200

    extra_pages: list[WcagPageInitial] = list(
        WcagPageInitial.objects.filter(
            wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.EXTRA
        )
    )

    assert len(extra_pages) == 1
    assert extra_pages[0].name == EXTRA_PAGE_NAME
    assert extra_pages[0].url == EXTRA_PAGE_URL


def test_delete_extra_page(admin_client):
    """Test deleting an extra page"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    extra_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.EXTRA,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": wcag_audit.version,
            f"remove_extra_page_{extra_page.id}": "Remove page",
        },
        follow=True,
    )
    assert response.status_code == 200

    updated_extra_page: WcagPageInitial = WcagPageInitial.objects.get(id=extra_page.id)

    assert updated_extra_page.is_deleted


def test_initial_statement_page_url_creates_statement_page(admin_client):
    """
    Test that the first time a statement page url is saved a statement page
    is created with that url
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    for page_type in [
        WcagPageInitial.Type.EXTRA,
        WcagPageInitial.Type.HOME,
        WcagPageInitial.Type.CONTACT,
        WcagPageInitial.Type.STATEMENT,
        WcagPageInitial.Type.FORM,
    ]:
        WcagPageInitial.objects.create(
            wcag_audit=wcag_audit,
            page_type=page_type,
        )
    AuditOverview.objects.create(
        simplified_case=simplified_case,
    )
    wcag_page_initial: WcagPageInitial = (
        wcag_audit.accessibility_statement_wcag_page_initial
    )

    assert wcag_page_initial.url == ""

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
        {
            "version": wcag_audit.version,
            "save": "Save",
            "standard-TOTAL_FORMS": "1",
            "standard-INITIAL_FORMS": "1",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "standard-0-is_contact_page": "no",
            "standard-0-id": wcag_page_initial.id,
            "standard-0-name": "",
            "standard-0-url": STATEMENT_PAGE_URL,
        },
    )

    assert response.status_code == 302

    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.STATEMENT
    )

    assert wcag_page_initial.url == STATEMENT_PAGE_URL

    statement_page: StatementPage = StatementPage.objects.get(
        simplified_case=simplified_case
    )

    assert statement_page.url == STATEMENT_PAGE_URL


def test_page_url_changes_do_not_create_statement_page(admin_client):
    """
    Test that the changes to the Page of type statement URL do not
    create StatementPage rows if one already exists
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial_statement: WcagPageInitial = (
        wcag_audit.accessibility_statement_wcag_page_initial
    )
    wcag_page_initial_statement.url = ""
    wcag_page_initial_statement.save()
    StatementPage.objects.create(
        simplified_case=wcag_audit.simplified_case,
        audit_overview=wcag_audit.simplified_case.audit_overview,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": wcag_audit.id}),
        {
            "version": wcag_audit.version,
            "save": "Save",
            "standard-TOTAL_FORMS": "1",
            "standard-INITIAL_FORMS": "1",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "standard-0-is_contact_page": "no",
            "standard-0-id": wcag_page_initial_statement.id,
            "standard-0-name": "",
            "standard-0-url": STATEMENT_PAGE_URL,
        },
    )

    assert response.status_code == 302

    wcag_page_initial_statement: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.STATEMENT
    )

    assert wcag_page_initial_statement.url == STATEMENT_PAGE_URL

    statement_page: StatementPage = StatementPage.objects.get(
        simplified_case=wcag_audit.simplified_case
    )

    assert statement_page.url == ""


def test_page_checks_edit_page_loads(admin_client):
    """Test page checks edit view page loads and contains all WCAG definitions"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id})
    )

    assert response.status_code == 200

    assertContains(response, "Additional page test")
    assertContains(response, "Showing 79 errors")
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)


def test_page_checks_edit_adds_to_notes_history(admin_client):
    """
    Test page checks edit view adds to the notes history when the notes have changed
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    check_result_axe: WcagCheckResultInitial = WcagCheckResultInitial.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=wcag_page_initial,
        wcag_definition=wcag_definition_axe,
    )
    check_result_pdf: WcagCheckResultInitial = WcagCheckResultInitial.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=wcag_page_initial,
        wcag_definition=wcag_definition_pdf,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id}),
        {
            "version": wcag_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": check_result_axe.id,
            "form-0-wcag_definition": check_result_axe.wcag_definition.id,
            "form-0-check_result_state": WcagCheckResultInitial.Result.ERROR,
            "form-0-notes": "",
            "form-1-id": check_result_pdf.id,
            "form-1-wcag_definition": check_result_pdf.wcag_definition.id,
            "form-1-check_result_state": WcagCheckResultInitial.Result.ERROR,
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "no_errors_date": "off",
        },
        follow=True,
    )

    assert response.status_code == 200

    assert (
        WcagCheckResultInitialNotesHistory.objects.filter(
            wcag_check_result_initial=check_result_axe
        ).count()
        == 0
    )
    assert (
        WcagCheckResultInitialNotesHistory.objects.filter(
            wcag_check_result_initial=check_result_pdf
        ).count()
        == 1
    )

    check_result_notes_history: WcagCheckResultInitialNotesHistory = (
        WcagCheckResultInitialNotesHistory.objects.get(
            wcag_check_result_initial=check_result_pdf
        )
    )

    assert check_result_notes_history.notes == CHECK_RESULT_NOTES


def test_page_checks_shows_notes_history(admin_client):
    """Test page checks view shows the notes history"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit,
            wcag_page_initial=wcag_page_initial,
            wcag_definition=wcag_definition,
        )
    )
    user: User = User.objects.create()

    WcagCheckResultInitialNotesHistory.objects.create(
        wcag_check_result_initial=wcag_check_result_initial,
        notes=HISTORIC_CHECK_RESULT_NOTES,
        created_by=user,
    )
    WcagCheckResultInitialNotesHistory.objects.create(
        wcag_check_result_initial=wcag_check_result_initial,
        created_by=user,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id}),
    )

    assert response.status_code == 200

    assertContains(response, HISTORIC_CHECK_RESULT_NOTES)


def test_page_checks_edit_page_shows_location(admin_client):
    """Test page checks edit view page shows page location"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_page_initial.location = PAGE_LOCATION
    wcag_page_initial.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id})
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_page_checks_edit_page_contains_hint_text(admin_client):
    """
    Test page checks page loads and contains WCAG definition hint text
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    wcag_definition.hint = WCAG_DEFINITION_HINT
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id})
    )

    assert response.status_code == 200

    assertContains(response, WCAG_DEFINITION_HINT)


def test_data_filter_string_contains_issue_identifier_on_initial_check_result_pages(
    admin_client,
):
    """
    Test data-filter-string contains issue identifier on check results pages
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    wcag_definition.hint = "hint"
    wcag_definition.save()
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=wcag_audit,
            wcag_page_initial=wcag_page_initial,
            wcag_definition=wcag_definition,
        )
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id})
    )

    assert response.status_code == 200

    assertContains(
        response,
        f'data-filter-string="{wcag_definition} hint {wcag_check_result_initial.issue_identifier}"',
    )


def test_data_filter_string_contains_issue_identifier_on_retest_check_result_pages(
    admin_client,
):
    """
    Test data-filter-string contains issue identifier on check results pages
    """
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    wcag_definition.hint = "hint"
    wcag_definition.save()
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.create(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
            wcag_definition=wcag_definition,
            type=wcag_definition.type,
        )
    )
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_audit=twelve_week_wcag_audit,
        wcag_page_initial=wcag_page_initial,
    )
    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.create(
            wcag_audit=twelve_week_wcag_audit,
            wcag_page_retest=wcag_page_retest,
            wcag_check_result_initial=wcag_check_result_initial,
            wcag_definition=wcag_definition,
        )
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-wcag-page-retest-check-results",
            kwargs={"pk": wcag_page_retest.id},
        )
    )

    assert response.status_code == 200

    assertContains(
        response,
        f'data-filter-string="{wcag_definition} hint {wcag_check_result_retest.wcag_check_result_initial.issue_identifier}"',
    )


def test_page_checks_edit_hides_future_wcag_definitions(admin_client):
    """Test page checks edit view page loads and hides future WCAG definitions"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_definition: WcagDefinition = WcagDefinition.objects.all().first()
    page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, wcag_definition.name)

    wcag_definition.date_start = wcag_audit.date_of_test + timedelta(days=10)
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertNotContains(response, wcag_definition.name)


def test_page_checks_edit_hides_past_wcag_definitions(admin_client):
    """Test page checks edit view page loads and hides past WCAG definitions"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.all().first()
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, wcag_definition.name)

    wcag_definition.date_end = wcag_audit.date_of_test - timedelta(days=10)
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertNotContains(response, wcag_definition.name)


def test_page_checks_edit_saves_results(admin_client):
    """Test page checks edit view saves the entered results"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit, page_type=WcagPageInitial.Type.HOME
    )
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": wcag_page_initial.id}),
        {
            "version": wcag_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-wcag_definition": wcag_definition_axe.id,
            "form-0-check_result_state": CheckResult.Result.ERROR,
            "form-0-notes": CHECK_RESULT_NOTES,
            "form-1-wcag_definition": wcag_definition_pdf.id,
            "form-1-check_result_state": CheckResult.Result.ERROR,
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "no_errors_date": "on",
        },
        follow=True,
    )

    assert response.status_code == 200

    check_result_axe: WcagCheckResultInitial = WcagCheckResultInitial.objects.get(
        wcag_page_initial=wcag_page_initial, wcag_definition=wcag_definition_axe
    )
    assert check_result_axe.check_result_state == WcagCheckResultInitial.Result.ERROR
    assert check_result_axe.notes == CHECK_RESULT_NOTES

    check_result_pdf: WcagCheckResultInitial = WcagCheckResultInitial.objects.get(
        wcag_page_initial=wcag_page_initial, wcag_definition=wcag_definition_pdf
    )
    assert check_result_pdf.check_result_state == WcagCheckResultInitial.Result.ERROR
    assert check_result_pdf.notes == CHECK_RESULT_NOTES

    updated_page: WcagPageInitial = WcagPageInitial.objects.get(id=wcag_page_initial.id)

    assert updated_page.complete_date
    assert updated_page.no_errors_date

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 3
    assert events[0].parent == check_result_pdf
    assert events[0].event_type == SimplifiedEventHistory.Type.CREATE
    assert events[1].parent == check_result_axe
    assert events[1].event_type == SimplifiedEventHistory.Type.CREATE
    assert events[2].parent == wcag_page_initial
    assert events[2].event_type == SimplifiedEventHistory.Type.UPDATE
    assert (
        events[2].difference
        == f"""{{"no_errors_date": "None -> {TODAY}", "complete_date": "None -> {TODAY}"}}"""
    )


def test_page_checks_edit_stays_on_page(admin_client):
    """Test that a successful page checks edit stays on the page"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    url: str = reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id})

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": wcag_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-wcag_definition": 1,
            "form-0-check_result_state": CheckResult.Result.NOT_TESTED,
            "form-0-notes": "",
            "form-1-wcag_definition": 2,
            "form-1-check_result_state": CheckResult.Result.NOT_TESTED,
            "form-1-notes": "",
        },
    )

    assert response.status_code == 302

    assert response.url == url


@pytest.mark.parametrize(
    "field_name, new_value, report_content_update",
    [
        (
            "compliance_state",
            "partially-compliant",
            True,
        ),
        ("audit_website_decision_complete_date", timezone.now(), False),
    ],
)
def test_website_decision_field_updates_report_content(
    field_name, new_value, report_content_update, admin_client
):
    """
    Test that a report data updated time changes only when website compliance
    changes
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    audit_overview: AuditOverview = wcag_audit.simplified_case.audit_overview

    assert audit_overview.published_report_data_updated_time is None

    context: dict[str, str | int] = {
        "version": wcag_audit.version,
        "compliance_state": wcag_audit.compliance_state,
        "save": "Button value",
    }
    context[field_name] = new_value

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-website-decision", kwargs=audit_pk), context
    )

    assert response.status_code == 302

    updated_audit_overview: AuditOverview = AuditOverview.objects.get(
        id=audit_overview.id
    )

    if report_content_update:
        assert updated_audit_overview.published_report_data_updated_time is not None
    else:
        assert updated_audit_overview.published_report_data_updated_time is None


def test_add_custom_statement_check_result_form_appears(admin_client):
    """
    Test that pressing the create issue button adds a new custom statement issue form
    """
    statement_audit: StatementAudit = create_initial_statement_audit()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-custom", kwargs={"pk": statement_audit.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": statement_audit.version,
            "add_custom": "Create issue",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Custom issue")

    statement_audit_from_db: StatementAudit = StatementAudit.objects.get(
        id=statement_audit.id
    )
    custom_statment_check_result: StatementCheckResultRound | None = (
        statement_audit_from_db.custom_statement_check_results.first()
    )

    assert custom_statment_check_result is not None
    assertContains(response, custom_statment_check_result.issue_identifier)


def test_add_custom_statement_check_result(admin_client):
    """Test adding a custom statement issue"""
    statement_audit: StatementAudit = create_initial_statement_audit()
    StatementCheckResultRound.objects.filter(
        statement_audit=statement_audit, type=StatementCheck.Type.CUSTOM
    ).delete()

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-custom-issue-create",
            kwargs={"statement_audit_id": statement_audit.id},
        ),
        {
            "public_comment": CUSTOM_STATEMENT_ISSUE,
            "auditor_information": "",
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200

    custom_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            statement_audit=statement_audit, type=StatementCheck.Type.CUSTOM
        )
    )

    assert custom_statement_check_result.public_comment == CUSTOM_STATEMENT_ISSUE


def test_delete_custom_statement_check_result(admin_client):
    """
    Test that pressing the remove issue button deletes the custom statement issue
    """
    statement_audit: StatementAudit = create_initial_statement_audit()
    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.get(
        statement_audit=statement_audit, type=StatementCheck.Type.CUSTOM
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-custom-issue-delete",
            kwargs={"pk": custom_issue.id},
        ),
        {},
        follow=True,
    )
    assert response.status_code == 200

    assertContains(response, "No custom statement issues have been entered")

    result_on_database: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            statement_audit=statement_audit, type=StatementCheck.Type.CUSTOM
        )
    )
    assert result_on_database.is_deleted is True


def test_delete_custom_retest_statement_check_result_on_retest(admin_client):
    """
    Test that pressing the remove issue button deletes the custom statement issue
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )
    custom_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.filter(
            statement_audit=statement_audit, statement_check=None
        ).first()
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-custom",
            kwargs={"pk": statement_audit.id},
        ),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": statement_audit.version,
            f"remove_custom_{custom_statement_check_result.id}": "Remove issue",
        },
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "No custom statement issues have been entered")

    result_on_database: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(id=custom_statement_check_result.id)
    )

    assert result_on_database.is_deleted is True


def test_start_retest_redirects(admin_client):
    """Test that starting a retest redirects to audit retest metadata"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    create_initial_statement_audit(simplified_case=wcag_audit.simplified_case)
    audit_overview: AuditOverview = wcag_audit.simplified_case.audit_overview

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-retest-start", kwargs={"pk": audit_overview.id}),
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-audit-retest-metadata",
        kwargs={"pk": audit_overview.first_wcag_audit_12_week_retest.id},
    )


def test_start_retest_creates_case_event(admin_client):
    """Test that starting a retest creates case event"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    simplified_case: SimplifiedCase = wcag_audit.simplified_case
    create_initial_statement_audit(simplified_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:audit-retest-start",
            kwargs={"pk": simplified_case.audit_overview.id},
        ),
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=simplified_case
    )
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.START_RETEST
    assert case_event.message == "Started retest"


def test_retest_page_checks_edit_page_loads(admin_client):
    """Test retest page checks edit view page loads and contains errors"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    create_retest_wcag_audit(initial_wcag_audit=initial_wcag_audit)
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial=wcag_page_initial
    )
    wcag_page_retest.notes = PAGE_RETEST_NOTES
    wcag_page_retest.location = PAGE_LOCATION
    wcag_page_retest.save()
    wcag_check_result_initial_first: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).first()
    wcag_check_result_initial_first.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_first.save()
    wcag_check_result_initial_last: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).last()
    wcag_check_result_initial_last.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_last.save()

    assert wcag_check_result_initial_first is not None
    assert wcag_check_result_initial_last is not None

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-wcag-page-retest-check-results",
            kwargs={"pk": wcag_page_retest.id},
        )
    )

    assert response.status_code == 200

    assertContains(response, "Additional page retest")
    assertContains(response, PAGE_RETEST_NOTES)
    assertContains(response, wcag_check_result_initial_first.wcag_definition.name)
    assertContains(response, wcag_check_result_initial_last.wcag_definition.name)
    assertContains(response, PAGE_LOCATION)


def test_retest_page_checks_edit_saves_results(admin_client):
    """Test retest page checks edit view saves the entered results"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial=wcag_page_initial
    )
    wcag_check_result_initial_first: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).first()
    wcag_check_result_retest_first: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_first,
        )
    )
    wcag_check_result_initial_first.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_first.save()
    wcag_check_result_initial_last: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).last()
    wcag_check_result_retest_last: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_last,
        )
    )
    wcag_check_result_initial_last.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_last.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-wcag-page-retest-check-results",
            kwargs={"pk": wcag_page_retest.id},
        ),
        {
            "version": twelve_week_wcag_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": wcag_check_result_retest_first.id,
            "form-0-wcag_definition": wcag_check_result_retest_first.wcag_definition.id,
            "form-0-retest_state": "fixed",
            "form-0-notes": CHECK_RESULT_NOTES,
            "form-1-id": wcag_check_result_retest_last.id,
            "form-1-wcag_definition": wcag_check_result_retest_last.wcag_definition.id,
            "form-1-retest_state": "not-fixed",
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "page_missing_date": "on",
            "notes": PAGE_RETEST_NOTES,
        },
        follow=True,
    )

    assert response.status_code == 200

    updated_wcag_check_result_retest_first: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(id=wcag_check_result_retest_first.id)
    )
    assert updated_wcag_check_result_retest_first.retest_state == "fixed"
    assert updated_wcag_check_result_retest_first.notes == CHECK_RESULT_NOTES

    updated_wcag_check_result_retest_last: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(id=wcag_check_result_retest_last.id)
    )
    assert updated_wcag_check_result_retest_last.retest_state == "not-fixed"
    assert updated_wcag_check_result_retest_last.notes == CHECK_RESULT_NOTES

    updated_wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        id=wcag_page_retest.id
    )

    assert updated_wcag_page_retest.complete_date
    assert updated_wcag_page_retest.page_missing_date
    assert updated_wcag_page_retest.notes == PAGE_RETEST_NOTES

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 3
    assert events[0].parent == wcag_check_result_retest_last
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE
    assert events[1].parent == wcag_check_result_retest_first
    assert events[1].event_type == SimplifiedEventHistory.Type.UPDATE
    assert events[2].parent == wcag_page_retest
    assert events[2].event_type == SimplifiedEventHistory.Type.UPDATE
    assert (
        events[2].difference
        == f'{{"complete_date": "None -> {TODAY}", "page_missing_date": "None -> {TODAY}", "notes": " -> Retest notes"}}'
    )


def test_retest_page_checks_edit_adds_to_retest_notes_history(admin_client):
    """
    Test retest page checks edit view adds to the retest notes history when the
    retest notes have changed
    """
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial=wcag_page_initial
    )
    wcag_check_result_initial_first: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).first()
    wcag_check_result_retest_first: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_first,
        )
    )
    wcag_check_result_initial_first.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_first.save()
    wcag_check_result_initial_last: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).last()
    wcag_check_result_retest_last: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_last,
        )
    )
    wcag_check_result_initial_last.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_last.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-wcag-page-retest-check-results",
            kwargs={"pk": wcag_page_retest.id},
        ),
        {
            "version": twelve_week_wcag_audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": wcag_check_result_retest_first.id,
            "form-0-wcag_definition": wcag_check_result_retest_first.wcag_definition.id,
            "form-0-retest_state": WcagCheckResultRetest.RetestResult.FIXED,
            "form-0-notes": "",
            "form-1-id": wcag_check_result_retest_last.id,
            "form-1-wcag_definition": wcag_check_result_retest_last.wcag_definition.id,
            "form-1-retest_state": WcagCheckResultRetest.RetestResult.NOT_FIXED,
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "page_missing_date": "on",
        },
        follow=True,
    )

    assert response.status_code == 200

    assert (
        WcagCheckResultRetestNotesHistory.objects.filter(
            wcag_check_result_retest=wcag_check_result_retest_first
        ).count()
        == 0
    )
    assert (
        WcagCheckResultRetestNotesHistory.objects.filter(
            wcag_check_result_retest=wcag_check_result_retest_last
        ).count()
        == 1
    )

    check_result_retest_notes_history: WcagCheckResultRetestNotesHistory = (
        WcagCheckResultRetestNotesHistory.objects.get(
            wcag_check_result_retest=wcag_check_result_retest_last
        )
    )

    assert check_result_retest_notes_history.notes == CHECK_RESULT_NOTES
    assert (
        check_result_retest_notes_history.retest_state
        == CheckResult.RetestResult.NOT_FIXED
    )


def test_retest_page_checks_shows_retest_notes_history(admin_client):
    """Test retest page checks view shows the retest notes history"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    create_retest_wcag_audit(initial_wcag_audit=initial_wcag_audit)
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial=wcag_page_initial
    )
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=initial_wcag_audit,
            wcag_page_initial=wcag_page_initial,
        )
    ).first()
    wcag_check_result_retest: WcagCheckResultRetest = WcagCheckResultRetest.objects.get(
        wcag_check_result_initial=wcag_check_result_initial,
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    user: User = User.objects.create()

    WcagCheckResultRetestNotesHistory.objects.create(
        wcag_check_result_retest=wcag_check_result_retest,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        notes=HISTORIC_RETEST_NOTES,
        created_by=user,
    )
    WcagCheckResultRetestNotesHistory.objects.create(
        wcag_check_result_retest=wcag_check_result_retest,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        created_by=user,
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-wcag-page-retest-check-results",
            kwargs={"pk": wcag_page_retest.id},
        ),
    )

    assert response.status_code == 200

    assertContains(response, HISTORIC_RETEST_NOTES)


def test_retest_pages_shows_location(admin_client):
    """Test page location is shown"""
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    twelve_week_wcag_audit: WcagAudit = create_retest_wcag_audit(
        initial_wcag_audit=initial_wcag_audit
    )
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=initial_wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        wcag_page_initial=wcag_page_initial
    )
    wcag_page_retest.location = PAGE_LOCATION
    wcag_page_retest.save()

    url: str = reverse(
        "audits:edit-audit-retest-pages", kwargs={"pk": twelve_week_wcag_audit.id}
    )

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_retest_statement_custom_no_initial(admin_client):
    """Test that a retest statement custom with no initial failure shows placeholder"""
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )
    StatementCheckResultRound.objects.filter(
        statement_audit=twelve_week_statement_audit, type=StatementCheck.Type.CUSTOM
    ).delete()
    StatementCheckResultRound.objects.filter(
        statement_audit=initial_statement_audit, type=StatementCheck.Type.CUSTOM
    ).delete()

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": twelve_week_statement_audit.id},
        ),
    )

    assert response.status_code == 200
    assertContains(response, "No custom statement issues were initially entered")


def test_retest_statement_custom_with_initial(admin_client):
    """Test that a retest statement custom with an initial failure shows it"""
    initial_statement_audit: StatementAudit = create_initial_statement_audit()
    twelve_week_statement_audit: StatementAudit = create_retest_statement_audit(
        initial_statement_audit=initial_statement_audit
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": twelve_week_statement_audit.id},
        ),
    )

    assert response.status_code == 200
    assertNotContains(response, "No custom statement issues found in initial test.")
    assertContains(response, "Custom statement issue")


def test_wcag_definition_list_view_shows_all(admin_client):
    """Test WCAG definition list shows all rows"""
    response: HttpResponse = admin_client.get(reverse("audits:wcag-definition-list"))

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 76 WCAG errors.</p>', html=True
    )


@pytest.mark.parametrize(
    "fieldname",
    ["type", "name", "description", "hint", "url_on_w3", "report_boilerplate"],
)
def test_wcag_definition_list_view_filters(fieldname, admin_client):
    """Test WCAG definition list can be filtered by each field"""
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    setattr(wcag_definition, fieldname, "helcaraxe")
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        f"{reverse('audits:wcag-definition-list')}?wcag_definition_search=Helcaraxe"
    )

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 1 WCAG error.</p>', html=True
    )


def test_create_wcag_definition_works(admin_client):
    """
    Test that a successful WCAG definiton create creates the new
    WCAG definition and redirects to list.
    """
    response: HttpResponse = admin_client.post(
        reverse("audits:wcag-definition-create"),
        {
            "type": WCAG_DEFINITION_TYPE,
            "name": WCAG_DEFINITION_NAME,
            "url_on_w3": WCAG_DEFINITION_URL,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:wcag-definition-list")

    wcag_definition_from_db: WcagDefinition | None = WcagDefinition.objects.last()

    assert wcag_definition_from_db is not None
    assert wcag_definition_from_db.type == WCAG_DEFINITION_TYPE
    assert wcag_definition_from_db.name == WCAG_DEFINITION_NAME
    assert wcag_definition_from_db.url_on_w3 == WCAG_DEFINITION_URL


def test_update_wcag_definition_works(admin_client):
    """
    Test that a successful WCAG definiton update updates the
    WCAG definition and redirects to list.
    """
    wcag_definition: WcagDefinition | None = WcagDefinition.objects.first()

    wcag_definition_pk: int = wcag_definition.id  # type: ignore
    path_kwargs: dict[str, int] = {"pk": wcag_definition_pk}
    update_url: str = reverse("audits:wcag-definition-update", kwargs=path_kwargs)

    response: HttpResponse = admin_client.post(
        update_url,
        {
            "type": WCAG_DEFINITION_TYPE,
            "name": WCAG_DEFINITION_NAME,
            "url_on_w3": WCAG_DEFINITION_URL,
        },
    )

    assert response.status_code == 302
    assert response.url == update_url

    wcag_definition_from_db: WcagDefinition | None = WcagDefinition.objects.first()

    assert wcag_definition_from_db is not None
    assert wcag_definition_from_db.type == WCAG_DEFINITION_TYPE
    assert wcag_definition_from_db.name == WCAG_DEFINITION_NAME
    assert wcag_definition_from_db.url_on_w3 == WCAG_DEFINITION_URL


def test_clear_published_report_data_updated_time_view(admin_client):
    """Test that clear report data updated time view empties that field"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    audit_overview: AuditOverview = wcag_audit.simplified_case.audit_overview
    audit_overview.published_report_data_updated_time = timezone.now()
    audit_overview.save()

    admin_client.get(
        reverse(
            "audits:clear-outdated-published-report-warning",
            kwargs={"pk": audit_overview.id},
        )
    )

    audit_overview_from_db: AuditOverview = AuditOverview.objects.get(
        id=audit_overview.id
    )

    assert audit_overview_from_db.published_report_data_updated_time is None


def test_update_audit_checks_version(admin_client):
    """Test that updating an audit shows an error if the version of the audit has changed"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-metadata", kwargs={"pk": wcag_audit.id}),
        {
            "version": wcag_audit.version - 1,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {str(wcag_audit)} has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url_name, create_test_data_function",
    [
        ("audits:edit-audit-metadata", create_initial_wcag_audit),
        ("audits:edit-statement-overview", create_initial_statement_audit),
    ],
)
def test_frequently_used_links_displayed(
    url_name, create_test_data_function, admin_client
):
    """
    Test that the frequently used links are displayed
    """
    wcag_or_statement_audit: WcagAudit | StatementAudit = create_test_data_function()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": wcag_or_statement_audit.id}),
    )

    assert response.status_code == 200

    assertContains(response, "Outstanding issues")
    assertContains(response, "Email templates")
    assertContains(response, "PSB Zendesk tickets")


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("audits:statement-check-create", "Create statement issue"),
        ("audits:statement-check-list", "Statement issues editor"),
    ],
)
def test_statement_check_page_loads(path_name, expected_content, admin_client):
    """Test that the statement check-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200

    assertContains(response, expected_content)


def test_statement_check_update_page_loads(admin_client):
    """Test that the statement check update view page loads"""
    kwargs: dict[str, int] = {"pk": 1}

    response: HttpResponse = admin_client.get(
        reverse("audits:statement-check-update", kwargs=kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "Update statement issue")


def test_statement_check_list_renders(admin_client):
    """Test statement check list renders"""
    response: HttpResponse = admin_client.get(reverse("audits:statement-check-list"))

    assert response.status_code == 200

    assertContains(response, "Statement issues editor")
    assertContains(response, "Displaying 84 Statement checks.", html=True)
    assertContains(
        response,
        """<a href="/audits/1/edit-statement-check/"
            class="govuk-link govuk-link--no-visited-state">
            Edit</a>""",
        html=True,
    )


def test_statement_check_list_search(admin_client):
    """Test statement check list search"""
    url: str = reverse("audits:statement-check-list")
    response: HttpResponse = admin_client.get(f"{url}?statement_check_search=website")

    assert response.status_code == 200

    assertContains(response, "Displaying 23 Statement checks.", html=True)


def test_create_statement_check_works(admin_client):
    """
    Test that a successful statement check create creates the new
    statement check and redirects to list.
    """
    response: HttpResponse = admin_client.post(
        reverse("audits:statement-check-create"),
        {
            "label": STATEMENT_CHECK_LABEL,
            "type": STATEMENT_CHECK_TYPE,
            "success_criteria": STATEMENT_CHECK_SUCCESS_CRITERIA,
            "report_text": STATEMENT_CHECK_REPORT_TEXT,
            "save": "Save",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:statement-check-list")

    statement_check_from_db: StatementCheck = StatementCheck.objects.get(
        label=STATEMENT_CHECK_LABEL
    )

    assert statement_check_from_db.type == STATEMENT_CHECK_TYPE
    assert statement_check_from_db.success_criteria == STATEMENT_CHECK_SUCCESS_CRITERIA
    assert statement_check_from_db.report_text == STATEMENT_CHECK_REPORT_TEXT


def test_update_statement_check_works(admin_client):
    """
    Test that a successful statement check update updates the statement check
    and redirects to list.
    """
    statement_check: StatementCheck | None = StatementCheck.objects.first()

    assert statement_check is not None
    assert statement_check.label != STATEMENT_CHECK_LABEL
    assert statement_check.type != STATEMENT_CHECK_TYPE
    assert statement_check.success_criteria != STATEMENT_CHECK_SUCCESS_CRITERIA
    assert statement_check.report_text != STATEMENT_CHECK_REPORT_TEXT

    statement_check_id: int = statement_check.id
    path_kwargs: dict[str, int] = {"pk": statement_check_id}

    response: HttpResponse = admin_client.post(
        reverse("audits:statement-check-update", kwargs=path_kwargs),
        {
            "label": STATEMENT_CHECK_LABEL,
            "type": STATEMENT_CHECK_TYPE,
            "success_criteria": STATEMENT_CHECK_SUCCESS_CRITERIA,
            "report_text": STATEMENT_CHECK_REPORT_TEXT,
            "save": "Save",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("audits:statement-check-update", kwargs=path_kwargs)

    statement_check_from_db: StatementCheck = StatementCheck.objects.get(
        id=statement_check_id
    )

    assert statement_check_from_db.label == STATEMENT_CHECK_LABEL
    assert statement_check_from_db.type == STATEMENT_CHECK_TYPE
    assert statement_check_from_db.success_criteria == STATEMENT_CHECK_SUCCESS_CRITERIA
    assert statement_check_from_db.report_text == STATEMENT_CHECK_REPORT_TEXT


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-wcag-summary", "wcag_audit_initial"),
        ("audits:edit-audit-retest-wcag-summary", "first_wcag_audit_12_week_retest"),
    ],
)
def test_summary_page_view(url_name, audit_overview_attr, admin_client):
    """Test that summary page view renders with results grouped by page"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = getattr(simplified_case.audit_overview, audit_overview_attr)
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    response: HttpResponse = admin_client.get(
        f"{reverse(url_name, kwargs={"pk": wcag_audit.id})}?page-view=true",
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">WCAG issue</th>',
        html=True,
    )
    assertContains(response, "Group by WCAG issue")


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-wcag-summary", "wcag_audit_initial"),
        ("audits:edit-audit-retest-wcag-summary", "first_wcag_audit_12_week_retest"),
    ],
)
def test_summary_wcag_view(url_name, audit_overview_attr, admin_client):
    """Test that summary page view renders with results grouped by WCAG issue"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = getattr(simplified_case.audit_overview, audit_overview_attr)
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().first()
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": wcag_audit.id})
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">Page</th>',
        html=True,
    )
    assertContains(response, "Group by page")


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-wcag-summary", "wcag_audit_initial"),
        ("audits:edit-audit-retest-wcag-summary", "first_wcag_audit_12_week_retest"),
    ],
)
def test_summary_page_view_unfixed(url_name, audit_overview_attr, admin_client):
    """Test that summary page view renders with unfixed results only"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = getattr(simplified_case.audit_overview, audit_overview_attr)
    wcag_check_result_initial_fixed: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().first()
    )
    wcag_check_result_initial_fixed.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_fixed.save()
    wcag_check_result_retest_fixed: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_fixed
        )
    )
    wcag_check_result_retest_fixed.retest_state = (
        WcagCheckResultRetest.RetestResult.FIXED
    )
    wcag_check_result_retest_fixed.notes = FIXED_ERROR_NOTES
    wcag_check_result_retest_fixed.save()
    wcag_check_result_initial_unfixed: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().last()
    )
    wcag_check_result_initial_unfixed.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_unfixed.save()
    wcag_check_result_retest_unfixed: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_unfixed
        )
    )
    wcag_check_result_retest_unfixed.retest_state = (
        WcagCheckResultRetest.RetestResult.NOT_FIXED
    )
    wcag_check_result_retest_unfixed.notes = UNFIXED_ERROR_NOTES
    wcag_check_result_retest_unfixed.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": wcag_audit.id}),
    )

    assert response.status_code == 200

    assertNotContains(response, FIXED_ERROR_NOTES)
    assertContains(response, UNFIXED_ERROR_NOTES)
    assertContains(response, "View all issues")


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-wcag-summary", "wcag_audit_initial"),
        ("audits:edit-audit-retest-wcag-summary", "first_wcag_audit_12_week_retest"),
    ],
)
def test_summary_page_view_show_all(url_name, audit_overview_attr, admin_client):
    """Test that summary page view renders with all results"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = getattr(simplified_case.audit_overview, audit_overview_attr)
    wcag_check_result_initial_fixed: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().first()
    )
    wcag_check_result_initial_fixed.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_fixed.save()
    wcag_check_result_retest_fixed: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_fixed
        )
    )
    wcag_check_result_retest_fixed.retest_state = (
        WcagCheckResultRetest.RetestResult.FIXED
    )
    wcag_check_result_retest_fixed.notes = FIXED_ERROR_NOTES
    wcag_check_result_retest_fixed.save()
    wcag_check_result_initial_unfixed: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.all().last()
    )
    wcag_check_result_initial_unfixed.check_result_state = (
        WcagCheckResultInitial.Result.ERROR
    )
    wcag_check_result_initial_unfixed.save()
    wcag_check_result_retest_unfixed: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.get(
            wcag_check_result_initial=wcag_check_result_initial_unfixed
        )
    )
    wcag_check_result_retest_unfixed.retest_state = (
        WcagCheckResultRetest.RetestResult.NOT_FIXED
    )
    wcag_check_result_retest_unfixed.notes = UNFIXED_ERROR_NOTES
    wcag_check_result_retest_unfixed.save()

    response: HttpResponse = admin_client.get(
        f"{reverse(url_name, kwargs={"pk": wcag_audit.id})}?show-all=true",
    )

    assert response.status_code == 200

    assertContains(response, FIXED_ERROR_NOTES)
    assertContains(response, UNFIXED_ERROR_NOTES)
    assertContains(response, "View only unfixed issues")


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-statement-summary", "statement_audit_initial"),
        (
            "audits:edit-audit-retest-statement-summary",
            "first_statement_audit_12_week_retest",
        ),
    ],
)
def test_test_statement_summary_page_view(url_name, audit_overview_attr, admin_client):
    """Test that statement summary page views contain statement results"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    statement_audit_initial: StatementAudit = (
        simplified_case.audit_overview.statement_audit_initial
    )
    statement_audit_12_week: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    statement_audit_for_url: StatementAudit = getattr(
        simplified_case.audit_overview, audit_overview_attr
    )
    overview_statement_check: StatementCheck | None = (
        StatementCheck.objects.on_date(timezone.now().date())
        .filter(type=StatementCheck.Type.OVERVIEW)
        .first()
    )
    overview_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            statement_check=overview_statement_check,
            statement_audit=statement_audit_initial,
        )
    )
    overview_statement_check_result.type = StatementCheck.Type.OVERVIEW
    overview_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.YES
    )
    overview_statement_check_result.save()
    website_statement_check: StatementCheck = (
        StatementCheck.objects.on_date(timezone.now().date())
        .filter(type=StatementCheck.Type.WEBSITE)
        .first()
    )
    website_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            statement_check=website_statement_check,
            statement_audit=statement_audit_initial,
        )
    )
    website_statement_check_result.check_result_state = (
        StatementCheckResultRound.Result.NO
    )
    website_statement_check_result.public_comment = STATEMENT_CHECK_INITIAL_COMMENT
    website_statement_check_result.save()
    custom_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            type=StatementCheck.Type.CUSTOM,
            statement_audit=statement_audit_initial,
        )
    )
    custom_statement_check_result.public_comment = STATEMENT_CHECK_CUSTOM_COMMENT
    custom_statement_check_result.save()
    twelve_week_statement_check_result: StatementCheckResultRound = (
        StatementCheckResultRound.objects.get(
            type=StatementCheck.Type.RETEST,
            statement_audit=statement_audit_12_week,
        )
    )
    twelve_week_statement_check_result.public_comment = (
        NEW_12_WEEK_CUSTOM_RETEST_COMMENT
    )
    twelve_week_statement_check_result.save()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": statement_audit_for_url.id})
    )

    assert response.status_code == 200

    assertContains(response, STATEMENT_CHECK_INITIAL_COMMENT)
    assertContains(response, STATEMENT_CHECK_CUSTOM_COMMENT)
    assertContains(response, NEW_12_WEEK_CUSTOM_RETEST_COMMENT)


@pytest.mark.parametrize(
    "url_name, audit_overview_attr",
    [
        ("audits:edit-audit-statement-summary", "statement_audit_initial"),
        (
            "audits:edit-audit-retest-statement-summary",
            "first_statement_audit_12_week_retest",
        ),
    ],
)
def test_test_statement_summary_page_summary(
    url_name, audit_overview_attr, admin_client
):
    """
    Test that statement summary page shows initial compliance values before 12-week
    values are entered.
    """
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    statement_audit_12_week: StatementAudit = (
        simplified_case.audit_overview.first_statement_audit_12_week_retest
    )
    statement_audit_for_url: StatementAudit = getattr(
        simplified_case.audit_overview, audit_overview_attr
    )
    audit_pk: dict[str, int] = {"pk": statement_audit_for_url.id}

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200
    assertContains(response, "Initial statement compliance")
    assertContains(response, "Initial disproportionate burden")
    assertNotContains(response, "12-week statement compliance")
    assertNotContains(response, "12-week disproportionate burden")

    statement_audit_12_week.disproportionate_burden_claim = (
        StatementAudit.DisproportionateBurden.ASSESSMENT
    )
    statement_audit_12_week.compliance_state = (
        StatementAudit.StatementCompliance.COMPLIANT
    )
    statement_audit_12_week.save()

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200
    assertNotContains(response, "Initial statement compliance")
    assertNotContains(response, "Initial disproportionate burden")
    assertContains(response, "12-week statement compliance")
    assertContains(response, "12-week disproportionate burden")


def test_create_equality_body_retest_redirects(admin_client):
    """Test that equality body retest create redirects to retest metadata"""
    wcag_audit_initial: WcagAudit = create_initial_wcag_audit()
    simplified_case: SimplifiedCase = wcag_audit_initial.simplified_case
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:create-equality-body-retest", kwargs=path_kwargs)
    )

    assert response.status_code == 302

    wcag_audit: WcagAudit = WcagAudit.objects.get(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    assert response.url == reverse(
        "audits:retest-metadata-update", kwargs={"pk": wcag_audit.id}
    )


def test_delete_retest(admin_client):
    """
    Test that equality body retest deletion works
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    assert retest.is_deleted is False

    response: HttpResponse = admin_client.get(
        reverse("audits:delete-retest", kwargs={"pk": retest.id})
    )

    assert response.status_code == 302
    assert response.url == "/simplified/1/retest-overview/"

    retest_from_db: Retest = Retest.objects.get(id=retest.id)
    assert retest_from_db.is_deleted is True

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == retest
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE
    assert events[0].difference == '{"is_deleted": "False -> True"}'


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:retest-metadata-update", "save", "audits:retest-metadata-update"),
        ("audits:retest-comparison-update", "save", "audits:retest-comparison-update"),
        (
            "audits:retest-comparison-update",
            "save_continue",
            "audits:retest-compliance-update",
        ),
        ("audits:retest-compliance-update", "save", "audits:retest-compliance-update"),
    ],
)
def test_equality_body_wcag_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful equality body retest update redirects based on the button pressed
    """
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=wcag_audit_pk),
        {
            "version": wcag_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=wcag_audit_pk)
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        (
            "audits:edit-equality-body-statement-pages",
            "save",
            "audits:edit-equality-body-statement-pages",
        ),
        (
            "audits:edit-equality-body-statement-pages",
            "save_continue",
            "audits:edit-equality-body-statement-backup",
        ),
        (
            "audits:edit-equality-body-statement-backup",
            "save",
            "audits:edit-equality-body-statement-backup",
        ),
        (
            "audits:edit-equality-body-statement-backup",
            "save_continue",
            "audits:edit-equality-body-statement-overview",
        ),
        (
            "audits:edit-equality-body-statement-overview",
            "save",
            "audits:edit-equality-body-statement-overview",
        ),
        (
            "audits:edit-equality-body-statement-overview",
            "save_continue",
            "audits:edit-equality-body-statement-results",
        ),
        (
            "audits:edit-equality-body-statement-website",
            "save",
            "audits:edit-equality-body-statement-website",
        ),
        (
            "audits:edit-equality-body-statement-website",
            "save_continue",
            "audits:edit-equality-body-statement-compliance",
        ),
        (
            "audits:edit-equality-body-statement-compliance",
            "save",
            "audits:edit-equality-body-statement-compliance",
        ),
        (
            "audits:edit-equality-body-statement-compliance",
            "save_continue",
            "audits:edit-equality-body-statement-non-accessible",
        ),
        (
            "audits:edit-equality-body-statement-non-accessible",
            "save",
            "audits:edit-equality-body-statement-non-accessible",
        ),
        (
            "audits:edit-equality-body-statement-non-accessible",
            "save_continue",
            "audits:edit-equality-body-statement-preparation",
        ),
        (
            "audits:edit-equality-body-statement-preparation",
            "save",
            "audits:edit-equality-body-statement-preparation",
        ),
        (
            "audits:edit-equality-body-statement-preparation",
            "save_continue",
            "audits:edit-equality-body-statement-feedback",
        ),
        (
            "audits:edit-equality-body-statement-feedback",
            "save",
            "audits:edit-equality-body-statement-feedback",
        ),
        (
            "audits:edit-equality-body-statement-feedback",
            "save_continue",
            "audits:edit-equality-body-statement-disproportionate",
        ),
        (
            "audits:edit-equality-body-statement-disproportionate",
            "save",
            "audits:edit-equality-body-statement-disproportionate",
        ),
        (
            "audits:edit-equality-body-statement-disproportionate",
            "save_continue",
            "audits:edit-equality-body-statement-custom",
        ),
        (
            "audits:edit-equality-body-statement-custom",
            "save",
            "audits:edit-equality-body-statement-custom",
        ),
        (
            "audits:edit-equality-body-statement-custom",
            "save_continue",
            "audits:edit-equality-body-statement-results",
        ),
        (
            "audits:edit-equality-body-statement-results",
            "save",
            "audits:edit-equality-body-statement-results",
        ),
        (
            "audits:edit-equality-body-statement-results",
            "save_continue",
            "audits:edit-equality-body-disproportionate-burden",
        ),
        (
            "audits:edit-equality-body-disproportionate-burden",
            "save",
            "audits:edit-equality-body-disproportionate-burden",
        ),
        (
            "audits:edit-equality-body-disproportionate-burden",
            "save_continue",
            "audits:edit-equality-body-statement-decision",
        ),
        (
            "audits:edit-equality-body-statement-decision",
            "save",
            "audits:edit-equality-body-statement-decision",
        ),
    ],
)
def test_equality_body_statement_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful equality body retest update redirects based on the button pressed
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=statement_audit_pk),
        {
            "version": statement_audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=statement_audit_pk)
    assert response.url == expected_path


def test_equality_body_wcag_redirects_to_statement_audit(
    admin_client,
):
    """
    Test that the last WCAG audit page redirects to the first statement audit page
    """
    wcag_audit: WcagAudit = create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:retest-compliance-update", kwargs={"pk": wcag_audit.id}),
        {
            "version": wcag_audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-equality-body-statement-pages", kwargs={"pk": statement_audit.id}
    )
    assert response.url == expected_path


def test_equality_body_statement_audit_overview_redirects_to_website(
    admin_client,
):
    """
    Test that a successful equality body retest update to statement overview to
    statement website when all overview checks have passed
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}
    for statement_check_result in statement_audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResultRound.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-overview", kwargs=statement_audit_pk
        ),
        {
            "version": statement_audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-equality-body-statement-website", kwargs=statement_audit_pk
    )
    assert response.url == expected_path


def test_equality_body_statement_audit_redirects_to_case(
    admin_client,
):
    """
    Test that the last statement audit page redirects to the parent case
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-decision",
            kwargs={"pk": statement_audit.id},
        ),
        {
            "version": statement_audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "simplified:edit-retest-overview",
        kwargs={"pk": statement_audit.simplified_case.id},
    )
    assert response.url == expected_path


def test_equality_body_retest_add_statement_link(admin_client):
    """Test that add statement link views saves URL"""
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-pages",
            kwargs={"pk": statement_audit.id},
        ),
        {
            "version": statement_audit.version,
            "statement_url": STATEMENT_PAGE_URL,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    statement_page: StatementPage = StatementPage.objects.get(
        simplified_case=statement_audit.simplified_case
    )

    assert statement_page.url == STATEMENT_PAGE_URL


@mock_aws
def test_equality_body_retest_statement_backup(admin_client):
    """Test that equality body retest statement backup saves to s3"""
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )
    simplified_case: SimplifiedCase = statement_audit.simplified_case

    in_memory_file: InMemoryUploadedFile = InMemoryUploadedFile(
        io.BytesIO(CASE_FILE_CONTENT.encode()),
        field_name="name",
        name=CASE_FILE_NAME,
        content_type="text",
        size=len(CASE_FILE_CONTENT),
        charset=None,
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-backup",
            kwargs={"pk": statement_audit.id},
        ),
        {
            "version": statement_audit.version,
            "file_to_upload": in_memory_file,
            "type": CaseFile.Type.STATEMENT,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    case_file: CaseFile = CaseFile.objects.get(base_case=simplified_case)

    assert case_file.name == CASE_FILE_NAME

    s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
    data_s3: bytes | str = s3_read_write.read_case_file_from_s3(case_file=case_file)

    assert isinstance(data_s3, bytes)
    assert data_s3.decode() == CASE_FILE_CONTENT


def test_equality_body_retest_statement_overview_redirects_when_no(admin_client):
    """
    Test that an equality body retest statement overview redirects to statement
    results when one of the overview questions has been answered 'no'.
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )
    statement_audit_pk: dict[str, int] = {"pk": statement_audit.id}
    for statement_check_result in statement_audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResultRound.Result.NO
        statement_check_result.save()

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-overview", kwargs=statement_audit_pk
        ),
        {
            "version": statement_audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-equality-body-statement-results", kwargs=statement_audit_pk
    )


def test_equality_body_retest_metadata_update_redirects_to_retest_page_checks(
    admin_client,
):
    """
    Test that a equality body retest metadata update redirects to retest page checks when save
    and continue button is pressed.
    """
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    wcag_page_retest: WcagPageRetest = wcag_audit.wcag_page_retests.first()
    wcag_page_retest_pk: dict[str, int] = {"pk": wcag_page_retest.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:retest-metadata-update", kwargs=wcag_audit_pk),
        {
            "version": wcag_audit.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk
    )
    assert response.url == expected_path


def test_equality_body_page_checks_save(
    admin_client,
):
    """Test that a equality body retest page checks saves"""
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_page_retest: WcagPageRetest = wcag_audit.wcag_page_retests.first()
    wcag_page_retest_pk: dict[str, int] = {"pk": wcag_page_retest.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk
    )
    assert response.url == expected_path


def test_equality_body_page_location_shown(admin_client):
    """Test that a equality body retest page show the location"""
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_page_retest: WcagPageRetest = wcag_audit.wcag_page_retests.first()
    wcag_page_retest_pk: dict[str, int] = {"pk": wcag_page_retest.id}
    wcag_page_retest.location = PAGE_LOCATION
    wcag_page_retest.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_equality_body_page_checks_save_continue(
    admin_client,
):
    """Test that a equality body retest page checks redirects on save and continue"""
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    wcag_page_retest: WcagPageRetest = wcag_audit.wcag_page_retests.last()
    wcag_page_retest_pk: dict[str, int] = {"pk": wcag_page_retest.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:retest-comparison-update", kwargs=wcag_audit_pk
    )
    assert response.url == expected_path


def test_equality_body_retest_statement_compliance_update_redirects_to_retest_overview_based_on_button_pressed(
    admin_client,
):
    """
    Test that a equality body retest statement compliance update redirects
    to retest overview when save and continue button is pressed.
    """
    create_equality_body_audits()
    statement_audit: StatementAudit = StatementAudit.objects.get(
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-statement-decision",
            kwargs={"pk": statement_audit.id},
        ),
        {
            "version": statement_audit.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "simplified:edit-retest-overview",
        kwargs={"pk": statement_audit.simplified_case.id},
    )
    assert response.url == expected_path


def test_equality_body_page_checks_page_missing(
    admin_client,
):
    """
    Test that when equality body retest page is marked as missing the underling
    page is also so marked.
    """
    wcag_audit: WcagAudit = create_equality_body_audits()
    wcag_page_retest: WcagPageRetest = wcag_audit.wcag_page_retests.last()
    wcag_page_retest_pk: dict[str, int] = {"pk": wcag_page_retest.id}

    assert wcag_page_retest.page_missing_date is None
    assert wcag_page_retest.wcag_page_initial.not_found == Boolean.NO

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=wcag_page_retest_pk),
        {
            "page_missing_date": "on",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    updated_wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.get(
        id=wcag_page_retest.id
    )

    assert updated_wcag_page_retest.page_missing_date is not None
    assert updated_wcag_page_retest.wcag_page_initial.not_found == Boolean.YES


def test_retest_comparison_page_groups_by_page_or_wcag(admin_client):
    """
    Test that equality body retest comparison page groups content by page or
    WCAG based on URL parameter.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    create_checkresults_for_wcag_audit_retest(retest=retest)

    url: str = reverse("audits:retest-comparison-update", kwargs=retest_pk)

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "Test summary | Page view")

    response: HttpResponse = admin_client.get(f"{url}?view=WCAG view")

    assert response.status_code == 200

    assertContains(response, "Test summary | WCAG view")


def test_retest_comparison_page_shows_location(admin_client):
    """
    Test that equality body retest comparison page shows page location
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    create_checkresults_for_wcag_audit_retest(retest=retest)

    retest_page: RetestPage = retest.retestpage_set.first()
    page: Page = retest_page.page
    page.location = PAGE_LOCATION
    page.save()

    url: str = reverse("audits:retest-comparison-update", kwargs=retest_pk)

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_nav_details_page_renders(admin_client):
    """
    Test that the nav detail with current page renders as expected
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_audit_pk: dict[str, int] = {"pk": wcag_audit.id}
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs=wcag_audit_pk)
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<details class="amp-nav-details">
            <summary class="amp-nav-details__summary">
                Case details 0/1
            </summary>
            <div class="amp-nav-details__text">
                <ul class="govuk-list amp-margin-bottom-5">
                    <li>
                        <a href="/simplified/1/edit-case-metadata/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                            Case metadata</a>
                    </li>
                </ul>
            </div>
        </details>""",
        html=True,
    )

    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-5">
            Initial WCAG test 0/10
        </p>""",
        html=True,
    )
    assertContains(
        response,
        """<b>Add or remove pages</b>""",
        html=True,
    )
    assertContains(
        response,
        f"""<li class="amp-nav-list-subpages amp-margin-top-5">
                <a href="/audits/pages/{wcag_page_initial.id}/edit-audit-page-checks/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                    {wcag_page_initial.page_title} test</a>
            </li>""",
        html=True,
    )


def test_nav_details_subpage_renders(admin_client):
    """
    Test that the nav detail with current subpage renders as expected
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    wcag_page_initial_pk: dict[str, int] = {"pk": wcag_page_initial.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=wcag_page_initial_pk)
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<details class="amp-nav-details">
            <summary class="amp-nav-details__summary">
                Case details 0/1
            </summary>
            <div class="amp-nav-details__text">
                <ul class="govuk-list amp-margin-bottom-5">
                    <li>
                        <a href="/simplified/1/edit-case-metadata/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                            Case metadata</a>
                    </li>
                </ul>
            </div>
        </details>""",
        html=True,
    )
    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-5">
            Initial WCAG test 0/10
        </p>""",
        html=True,
    )
    assertContains(
        response,
        f"""<a href="/audits/{wcag_audit.id}/edit-audit-pages/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
            Add or remove pages</a>""",
        html=True,
    )
    assertContains(
        response,
        f"""<li class="amp-nav-list-subpages amp-margin-top-5"><b>{wcag_page_initial.page_title} test</b></li>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name",
    [
        "audits:edit-audit-page-checks",
        "audits:edit-wcag-page-retest-check-results",
    ],
)
def test_tall_results_page_has_back_to_top_link(path_name, admin_client):
    """Test that tall pages include a back to top link"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=simplified_case.audit_overview.wcag_audit_initial,
        page_type=WcagPageInitial.Type.HOME,
    )
    if path_name == "audits:edit-audit-page-checks":
        page: WcagPageInitial = wcag_page_initial
    else:
        page: WcagPageRetest = WcagPageRetest.objects.get(
            wcag_page_initial=wcag_page_initial
        )
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=page_pk))

    assert response.status_code == 200

    assertContains(
        response,
        '<a href="#" class="govuk-link govuk-link--no-visited-state">Back to top</a>',
        html=True,
    )


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-audit-metadata", "Initial WCAG test | Add or remove pages"),
        ("edit-audit-pages", "Initial WCAG test | Compliance decision"),
    ],
)
def test_initial_wcag_audit_next_page_name(path_name, expected_next_page, admin_client):
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": wcag_audit.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-statement-overview", "Initial statement | Statement information"),
        ("edit-statement-overview", "Initial statement | Custom issues"),
    ],
)
def test_initial_statement_audit_next_page_name(
    path_name, expected_next_page, admin_client
):
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": statement_audit.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-audit-retest-metadata", "12-week WCAG test | Update page links"),
        ("edit-audit-retest-pages", "12-week WCAG test | Compliance decision"),
    ],
)
def test_twelve_week_wcag_audit_next_page_name(
    path_name, expected_next_page, admin_client
):
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": wcag_audit.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("edit-retest-statement-overview", "12-week statement | Statement information"),
        (
            "edit-retest-statement-overview",
            "12-week statement | Custom issues",
        ),
    ],
)
def test_twelve_week_statement_audit_next_page_name(
    path_name, expected_next_page, admin_client
):
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": statement_audit.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


@pytest.mark.parametrize(
    "path_name, expected_next_page",
    [
        ("retest-metadata-update", "Post case | Retest #1 | Home"),
        ("edit-equality-body-statement-overview", "Post case | Statement information"),
        ("edit-equality-body-statement-overview", "Post case | Statement results"),
    ],
)
def test_retest_next_page_name(path_name, expected_next_page, admin_client):
    """
    Test next page shown for when Save and continue button pressed on equality
    body retest
    """
    retest: Retest = create_equality_body_retest()
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": retest.id})

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, f"<b>{expected_next_page}</b>", html=True)


def test_initial_statement_page_removal(admin_client):
    """Test statement page removal and redirect"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:initial-remove-statement-page", kwargs={"pk": statement_page.id}
        ),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-statement-pages", kwargs={"pk": statement_audit.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == statement_page
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_twelve_week_statement_page_removal(admin_client):
    """Test statement page removal and redirect"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    audit_overview: AuditOverview = AuditOverview.objects.create(
        simplified_case=simplified_case
    )
    statement_page: StatementPage = StatementPage.objects.create(
        simplified_case=simplified_case, audit_overview=audit_overview
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-audit-retest-remove-statement-page",
            kwargs={"pk": statement_page.id},
        ),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-audit-retest-statement-pages", kwargs={"pk": statement_audit.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == statement_page
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_equality_body_retest_statement_page_removal(admin_client):
    """Test equality body retest statement page removal and redirect"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_page: StatementPage = StatementPage.objects.create(audit=audit)
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-equality-body-remove-statement-page",
            kwargs={"retest_id": retest.id, "pk": statement_page.id},
        ),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-equality-body-statement-pages", kwargs={"pk": retest.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == statement_page
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_create_initial_custom_issue_redirects(admin_client):
    """
    Test that statement initial custom issue create redirects to initial statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-custom-issue-create",
            kwargs={"statement_audit_id": statement_audit.id},
        ),
        {
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.get(
        statement_audit=statement_audit
    )
    response_url: str = reverse(
        "audits:edit-statement-custom", kwargs={"pk": statement_audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.CREATE


def test_update_initial_custom_issue_redirects(admin_client):
    """
    Test that statement initial custom issue update redirects to initial statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.create(
        statement_audit=statement_audit
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-update", kwargs={"pk": custom_issue.id}),
        {
            "auditor_information": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse(
        "audits:edit-statement-custom", kwargs={"pk": statement_audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_delete_initial_custom_issue_redirects(admin_client):
    """
    Test that statement initial custom issue delete redirects to initial statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.create(
        statement_audit=statement_audit
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-delete", kwargs={"pk": custom_issue.id}),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-statement-custom", kwargs={"pk": statement_audit.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_update_at_12_week_initial_custom_issue_redirects(admin_client):
    """
    Test that statement initial custom issue update at 12-weeks redirects to 12-week
    statement custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    custom_issue_initial: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(statement_audit=statement_audit)
    )
    custom_issue_retest: StatementCheckResultRound = (
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            statement_check_result_initial=custom_issue_initial,
        )
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-initial-custom-issue-update",
            kwargs={"pk": custom_issue_retest.id},
        ),
        {
            "check_result_state": "yes",
            "auditor_information": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": statement_audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue_retest.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue_retest
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_create_new_12_week_custom_issue_redirects(admin_client):
    """
    Test that statement new 12-week custom issue create redirects to 12-week statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-12-week-custom-issue-create",
            kwargs={"statement_audit_id": statement_audit.id},
        ),
        {
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.get(
        statement_audit=statement_audit
    )
    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": statement_audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.CREATE


def test_update_new_12_week_custom_issue_redirects(admin_client):
    """
    Test that statement new 12-week custom issue update redirects to 12-week statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.create(
        statement_audit=statement_audit
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-new-12-week-custom-issue-update",
            kwargs={"pk": custom_issue.id},
        ),
        {
            "auditor_information": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": statement_audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_delete_new_12_week_custom_issue_redirects(admin_client):
    """
    Test that statement new 12-week custom issue delete redirects to 12-week statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    custom_issue: StatementCheckResultRound = StatementCheckResultRound.objects.create(
        statement_audit=statement_audit
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-12-week-custom-issue-delete",
            kwargs={"pk": custom_issue.id},
        ),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": statement_audit.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE
