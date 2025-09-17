"""
Tests for audits views
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from accessibility_monitoring_platform.apps.common.models import Boolean

from ...reports.models import Report
from ...simplified.models import (
    CaseCompliance,
    CaseEvent,
    SimplifiedCase,
    SimplifiedEventHistory,
)
from ..models import (
    Audit,
    CheckResult,
    CheckResultNotesHistory,
    CheckResultRetestNotesHistory,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)
from ..utils import create_checkresults_for_retest, create_mandatory_pages_for_new_audit

TODAY = date.today()
WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
WCAG_TYPE_MANUAL_NAME: str = "WCAG Manual name"
WCAG_TYPE_PDF_NAME: str = "WCAG PDF name"
EXTRA_PAGE_NAME: str = "Extra page name"
EXTRA_PAGE_URL: str = "https://extra-page.com"
CHECK_RESULT_NOTES: str = "Check result notes"
NEW_PAGE_NAME: str = "New page name"
NEW_PAGE_URL: str = "https://example.com/extra"
UPDATED_PAGE_NAME: str = "Updated page name"
UPDATED_PAGE_URL: str = "https://example.com/updated"
WEBSITE_COMPLIANCE_STATE: str = "partially-compliant"
WEBSITE_COMPLIANCE_NOTES: str = "Website decision notes"
STATEMENT_COMPLIANCE_STATE: str = "not-compliant"
STATEMENT_COMPLIANCE_NOTES: str = "Accessibility statement notes"
FIXED_ERROR_NOTES: str = "Fixed error notes"
UNFIXED_ERROR_NOTES: str = "Unfixed error notes"
WCAG_DEFINITION_TYPE: str = "axe"
WCAG_DEFINITION_NAME: str = "WCAG definiton name"
WCAG_DEFINITION_URL: str = "https://example.com"
PAGE_RETEST_NOTES: str = "Retest notes"
ACCESSIBILITY_STATEMENT_URL: str = "https://example.com/accessibility-statement"
NO_ACCESSIBILITY_STATEMENT: str = """<p class="govuk-body">
No statement added. Add a statement in
<a href="/audits/1/edit-statement-pages/" class="govuk-link govuk-link--no-visited-state" rel="noreferrer noopener">
    statement links</a>.
</p>"""
NO_RETEST_ACCESSIBILITY_STATEMENT: str = """<p class="govuk-body">
No statement added. Add a statement in
<a href="/audits/1/edit-audit-retest-statement-pages/" class="govuk-link govuk-link--no-visited-state" rel="noreferrer noopener">
    statement links</a>.
</p>"""
ACCESSIBILITY_STATEMENT_12_WEEK_URL: str = (
    "https://example.com/12-week-accessibility-statement"
)
MISSING_PAGE_ON_RETEST: str = "This page has been removed by the organisation."
ORGANISATION_NAME: str = "Organisation name"
CUSTOM_STATEMENT_ISSUE: str = "Custom statement issue"
STATEMENT_CHECK_LABEL: str = "Test statement check"
STATEMENT_CHECK_TYPE: str = "custom"
STATEMENT_CHECK_SUCCESS_CRITERIA: str = "Success criteria"
STATEMENT_CHECK_REPORT_TEXT: str = "Report text"
STATEMENT_PAGE_INITIAL_CHECKED: str = """<input class="govuk-radios__input"
type="radio" name="form-0-added_stage" value="initial"
id="id_form-0-added_stage_0" checked="">"""
STATEMENT_PAGE_TWELVE_WEEK_CHECKED: str = """<input class="govuk-radios__input"
type="radio" name="form-0-added_stage" value="12-week-retest"
id="id_form-0-added_stage_1" checked="">"""
STATEMENT_PAGE_EWUALITY_BODY_RETEST_CHECKED: str = """<input class="govuk-radios__input"
type="radio" name="form-0-added_stage" value="retest"
id="id_form-0-added_stage_2" checked="">"""
STATEMENT_PAGE_URL: str = "https://example.com/statement"
WCAG_DEFINITION_HINT: str = "WCAG definition hint text"
PAGE_LOCATION: str = "Press button then click on link"
STATEMENT_CHECK_INITIAL_COMMENT: str = "Statement check initial comment"
STATEMENT_CHECK_CUSTOM_COMMENT: str = "Statement check custom comment"
NEW_12_WEEK_CUSTOM_REPORT_COMMENT: str = "New 12-week custom report comment"
NEW_12_WEEK_CUSTOM_RETEST_COMMENT: str = "New 12-week custom retest comment"
NEW_12_WEEK_CUSTOM_AUDITOR_NOTES: str = "New 12-week custom auditor notes"
HISTORIC_RETEST_NOTES: str = "Historic retest notes"
HISTORIC_CHECK_RESULT_NOTES: str = "Historic check result notes"


def create_audit() -> Audit:
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    return audit


def create_audit_and_pages() -> Audit:
    audit: Audit = create_audit()
    create_mandatory_pages_for_new_audit(audit=audit)
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


def test_restore_page_view(admin_client):
    """Test that restore page view restores audit"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, is_deleted=True)
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse(
            "audits:restore-page",
            kwargs=page_pk,
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "audits:edit-audit-pages",
        kwargs=audit_pk,
    )

    page_from_db: Page = Page.objects.get(**page_pk)

    assert page_from_db.is_deleted is False


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
    audit: Audit = create_audit()
    path_kwargs: dict[str, int] = {"case_id": audit.simplified_case.id}

    assert Audit.objects.filter(simplified_case=audit.simplified_case).count() == 1

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-create", kwargs=path_kwargs),
        {
            "save_continue": "Create test",
        },
    )

    assert response.status_code == 302
    assert Audit.objects.filter(simplified_case=audit.simplified_case).count() == 1


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
        (
            "audits:edit-statement-decision",
            "Initial statement compliance decision",
        ),
        ("audits:edit-audit-wcag-summary", "WCAG summary"),
        ("audits:edit-audit-statement-summary", "Statement summary"),
        ("audits:edit-audit-retest-wcag-summary", "WCAG summary"),
        ("audits:edit-audit-retest-statement-summary", "Statement summary"),
        ("audits:edit-audit-retest-metadata", "12-week retest metadata"),
        (
            "audits:edit-audit-retest-website-decision",
            "Compliance decision",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "Compliance decision",
        ),
    ],
)
def test_audit_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the audit-specific view page loads"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=audit_pk))

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
def test_audit_statement_check_specific_page_loads(
    path_name, expected_content, admin_client
):
    """Test that the audit with statement checks-specific view page loads"""
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=audit_pk))

    assert response.status_code == 200

    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-audit-metadata", "save", "audits:edit-audit-metadata"),
        ("audits:edit-audit-metadata", "save_continue", "audits:edit-audit-pages"),
        ("audits:edit-audit-wcag-summary", "save", "audits:edit-audit-wcag-summary"),
        (
            "audits:edit-audit-wcag-summary",
            "save_continue",
            "audits:edit-statement-pages",
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
            "audits:edit-audit-retest-wcag-summary",
            "save",
            "audits:edit-audit-retest-wcag-summary",
        ),
        (
            "audits:edit-audit-retest-wcag-summary",
            "save_continue",
            "audits:edit-audit-retest-statement-pages",
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
def test_audit_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful audit update redirects based on the button pressed
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-website-decision", "save", "audits:edit-website-decision"),
        (
            "audits:edit-website-decision",
            "save_continue",
            "audits:edit-audit-wcag-summary",
        ),
        ("audits:edit-statement-decision", "save", "audits:edit-statement-decision"),
        (
            "audits:edit-statement-decision",
            "save_continue",
            "audits:edit-audit-statement-summary",
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
            "audits:edit-audit-retest-statement-decision",
            "save",
            "audits:edit-audit-retest-statement-decision",
        ),
        (
            "audits:edit-audit-retest-statement-decision",
            "save_continue",
            "audits:edit-audit-retest-statement-summary",
        ),
    ],
)
def test_audit_compliance_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful audit update redirects based on the button pressed
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_audit_statement_summary_page_redirect_when_report_exists(admin_client):
    """
    Test that audit statement summary page redirects to Report ready for QA
    when a report exists
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    case_pk: dict[str, int] = {"pk": simplified_case.id}
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    audit_pk: dict[str, int] = {"pk": audit.id}
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-statement-summary", kwargs=audit_pk),
        {
            "version": audit.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("simplified:edit-report-ready-for-qa", kwargs=case_pk)
    assert response.url == expected_path


@pytest.mark.parametrize(
    "path_name",
    [
        "edit-statement-pages",
        "edit-audit-retest-statement-pages",
    ],
)
def test_add_statement_page(path_name, admin_client):
    """
    Test pressing add statement page button redirects to page with add_extra parameter
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": audit.id})

    response: HttpResponse = admin_client.post(
        url,
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            "add_statement_page": "Save and add link to statement",
        },
    )

    assert response.status_code == 302

    expected_path: str = f"{url}?add_extra=true#statement-page-None"
    assert response.url == expected_path


def test_audit_statement_pages_default_added_stage(
    admin_client,
):
    """
    Test that added stage for new entries defaults to initial
    for initial and 12-week for 12-week retest pages.
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        f'{reverse("audits:edit-statement-pages", kwargs=audit_pk)}?add_extra=true#statement-page-None'
    )

    assert response.status_code == 200

    assertContains(response, STATEMENT_PAGE_INITIAL_CHECKED, html=True)
    assertNotContains(response, STATEMENT_PAGE_TWELVE_WEEK_CHECKED, html=True)
    response: HttpResponse = admin_client.get(
        f'{reverse("audits:edit-audit-retest-statement-pages", kwargs=audit_pk)}?add_extra=true#statement-page-None'
    )

    assert response.status_code == 200

    assertNotContains(response, STATEMENT_PAGE_INITIAL_CHECKED, html=True)
    assertContains(response, STATEMENT_PAGE_TWELVE_WEEK_CHECKED, html=True)


@pytest.mark.parametrize(
    "path_name",
    [
        "edit-statement-pages",
        "edit-audit-retest-statement-pages",
    ],
)
def test_delete_statement_page(path_name, admin_client):
    """Test deleting a statement page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    response: HttpResponse = admin_client.post(
        reverse(f"audits:{path_name}", kwargs={"pk": audit.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            f"remove_statement_page_{statement_page.id}": "Remove statement link",
        },
        follow=True,
    )

    assert response.status_code == 200

    updated_statement_page: StatementPage = StatementPage.objects.get(
        id=statement_page.id
    )

    assert updated_statement_page.is_deleted is True


def test_delete_statement_page_on_retest(admin_client):
    """Test deleting a statement page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    retest: Retest = Retest.objects.create(simplified_case=audit.simplified_case)
    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-equality-body-statement-pages", kwargs={"pk": retest.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            f"remove_statement_page_{statement_page.id}": "Remove statement link",
        },
        follow=True,
    )

    assert response.status_code == 200

    updated_statement_page: StatementPage = StatementPage.objects.get(
        id=statement_page.id
    )

    assert updated_statement_page.is_deleted is True


@pytest.mark.parametrize(
    "path_name, button_name, expected_redirect_path_name",
    [
        ("audits:edit-statement-pages", "save", "audits:edit-statement-pages"),
        (
            "audits:edit-statement-pages",
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
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


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
def test_audit_statement_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful audit statement update redirects based on the button
    pressed
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=audit_pk),
        {
            "version": audit.version,
            "case-compliance-version": audit.simplified_case.compliance.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_audit_edit_statement_overview_redirects_to_statement_website(
    admin_client,
):
    """
    Test that a successful audit statement overview update redirects to
    statement information if the overiew checks have passed
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}
    for statement_check_result in StatementCheckResult.objects.filter(
        audit=audit, type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("audits:edit-statement-website", kwargs=audit_pk)
    assert response.url == expected_path


def test_audit_edit_statement_overview_updates_when_no_statement_exists(
    admin_client,
):
    """
    Test that audit statement overview update updates when no page exists
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "audit_statement_overview_complete_date": "on",
        },
    )

    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.audit_statement_overview_complete_date == date.today()


def test_audit_edit_statement_overview_updates_case_status(
    admin_client,
):
    """
    Test that a successful audit statement overview update updates case
    status and check results
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    simplified_case: SimplifiedCase = audit.simplified_case
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()
    simplified_case.compliance.website_compliance_state_initial = (
        CaseCompliance.WebsiteCompliance.COMPLIANT
    )
    simplified_case.compliance.save()
    simplified_case.update_case_status()

    assert audit.simplified_case.status == SimplifiedCase.Status.TEST_IN_PROGRESS

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-check_result_state": "yes",
            "form-0-report_comment": "",
            "form-1-id": "2",
            "form-1-check_result_state": "no",
            "form-1-report_comment": "",
        },
    )

    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)
    assert (
        audit_from_db.simplified_case.status == SimplifiedCase.Status.REPORT_IN_PROGRESS
    )

    statement_checkresult_1: StatementCheckResult = StatementCheckResult.objects.get(
        id=1
    )

    assert statement_checkresult_1.check_result_state == "yes"

    statement_checkresult_2: StatementCheckResult = StatementCheckResult.objects.get(
        id=2
    )

    assert statement_checkresult_2.check_result_state == "no"


def test_audit_retest_statement_overview_updates_when_no_statement_exists(
    admin_client,
):
    """
    Test that audit retest statement overview update updates when no page exists
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "audit_retest_statement_overview_complete_date": "on",
        },
    )

    assert response.status_code == 302

    audit_from_db: Audit = Audit.objects.get(id=audit.id)

    assert audit_from_db.audit_retest_statement_overview_complete_date == date.today()


def test_audit_retest_statement_overview_no_statement(
    admin_client,
):
    """
    Test that the audit retest statement overview page shows checks
    even if there is no statement page.
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}
    Page.objects.filter(page_type=Page.Type.STATEMENT).delete()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-retest-statement-overview", kwargs=audit_pk),
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
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    StatementPage.objects.create(
        audit=audit, added_stage=StatementPage.AddedStage.TWELVE_WEEK
    )

    simplified_case: SimplifiedCase = audit.simplified_case
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-retest_state": "yes",
            "form-0-report_comment": "",
            "form-1-id": "2",
            "form-1-retest_state": "no",
            "form-1-report_comment": "",
        },
    )

    assert response.status_code == 302

    statement_checkresult_1: StatementCheckResult = StatementCheckResult.objects.get(
        id=1
    )

    assert statement_checkresult_1.retest_state == "yes"

    statement_checkresult_2: StatementCheckResult = StatementCheckResult.objects.get(
        id=2
    )

    assert statement_checkresult_2.retest_state == "no"


def test_audit_retest_statement_overview_updates_statement_checkresult_no_initial_statement(
    admin_client,
):
    """
    Test that a successful audit retest statement overview update updates
    check results when no initial statement was found
    """
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    StatementPage.objects.create(
        audit=audit,
        added_stage=StatementPage.AddedStage.TWELVE_WEEK,
        url="https://www.website.com/statement",
    )

    simplified_case: SimplifiedCase = audit.simplified_case
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    user: User = User.objects.create()
    simplified_case.auditor = user
    simplified_case.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-statement-overview", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-retest_state": "yes",
            "form-0-report_comment": "",
            "form-1-id": "2",
            "form-1-retest_state": "no",
            "form-1-report_comment": "",
        },
    )

    assert response.status_code == 302

    statement_checkresult_1: StatementCheckResult = StatementCheckResult.objects.get(
        id=1
    )

    assert statement_checkresult_1.retest_state == "yes"

    statement_checkresult_2: StatementCheckResult = StatementCheckResult.objects.get(
        id=2
    )

    assert statement_checkresult_2.retest_state == "no"


def test_retest_date_change_creates_case_event(admin_client):
    """Test that changing the retest date creates a case event"""
    audit: Audit = create_audit()
    path_kwargs: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-metadata", kwargs=path_kwargs),
        {
            "retest_date_0": 30,
            "retest_date_1": 11,
            "retest_date_2": 2022,
            "save": "Save",
            "version": audit.version,
        },
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=audit.simplified_case
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
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}
    simplified_case: SimplifiedCase = audit.simplified_case
    simplified_case.no_psb_contact = Boolean.YES
    simplified_case.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-metadata", kwargs=audit_pk),
        {
            "version": audit.version,
            "save_continue": "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-audit-retest-statement-pages", kwargs=audit_pk
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
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs=audit_pk),
        {
            "version": audit.version,
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

    expected_path: str = reverse(expected_redirect_path_name, kwargs=audit_pk)
    assert response.url == expected_path


def test_standard_pages_appear_on_pages_page(admin_client):
    """
    Test that all the standard pages appear on the pages page.
    Also that the 'Form is on contact page' field appears.
    """
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
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
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
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

    Page.objects.create(audit=audit, page_type=Page.Type.EXTRA)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
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
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            "add_extra": "Button value",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Page 1")


def test_add_extra_page(admin_client):
    """Test adding an extra page"""
    audit: Audit = create_audit_and_pages()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
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
            "version": audit.version,
            "save_continue": "Save and continue",
        },
        follow=True,
    )
    assert response.status_code == 200

    extra_pages: list[Page] = list(
        Page.objects.filter(audit=audit, page_type=Page.Type.EXTRA)
    )

    assert len(extra_pages) == 1
    assert extra_pages[0].name == EXTRA_PAGE_NAME
    assert extra_pages[0].url == EXTRA_PAGE_URL


def test_delete_extra_page(admin_client):
    """Test deleting an extra page"""
    audit: Audit = create_audit_and_pages()
    extra_page: Page = Page.objects.create(
        audit=audit,
        page_type=Page.Type.EXTRA,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
        {
            "standard-TOTAL_FORMS": "0",
            "standard-INITIAL_FORMS": "0",
            "standard-MIN_NUM_FORMS": "0",
            "standard-MAX_NUM_FORMS": "1000",
            "extra-TOTAL_FORMS": "0",
            "extra-INITIAL_FORMS": "0",
            "extra-MIN_NUM_FORMS": "0",
            "extra-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            f"remove_extra_page_{extra_page.id}": "Remove page",
        },
        follow=True,
    )
    assert response.status_code == 200

    updated_extra_page: Page = Page.objects.get(id=extra_page.id)

    assert updated_extra_page.is_deleted


def test_initial_statement_page_url_creates_statement_page(admin_client):
    """
    Test that the first time a statement page url is saved a statement page
    is created with that url
    """
    audit: Audit = create_audit_and_pages()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = audit.accessibility_statement_page

    assert page.url == ""

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs=audit_pk),
        {
            "version": audit.version,
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
            "standard-0-id": page.id,
            "standard-0-name": "",
            "standard-0-url": STATEMENT_PAGE_URL,
        },
    )

    assert response.status_code == 302

    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.STATEMENT)

    assert page.url == STATEMENT_PAGE_URL

    statement_page: StatementPage = StatementPage.objects.get(audit=audit)

    assert statement_page.url == STATEMENT_PAGE_URL


def test_page_url_changes_do_not_create_statement_page(admin_client):
    """
    Test that the changes to the Page of type statement URL do not
    create StatementPage rows if one already exists
    """
    audit: Audit = create_audit_and_pages()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = audit.accessibility_statement_page
    StatementPage.objects.create(audit=audit)

    assert page.url == ""

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-pages", kwargs=audit_pk),
        {
            "version": audit.version,
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
            "standard-0-id": page.id,
            "standard-0-name": "",
            "standard-0-url": STATEMENT_PAGE_URL,
        },
    )

    assert response.status_code == 302

    page: Page = Page.objects.get(audit=audit, page_type=Page.Type.STATEMENT)

    assert page.url == STATEMENT_PAGE_URL

    statement_page: StatementPage = StatementPage.objects.get(audit=audit)

    assert statement_page.url == ""


def test_page_checks_edit_page_loads(admin_client):
    """Test page checks edit view page loads and contains all WCAG definitions"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Additional page test")
    assertContains(response, "Showing 2 errors")
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)


def test_page_checks_edit_adds_to_notes_history(admin_client):
    """
    Test page checks edit view adds to the notes history when the notes have changed
    """
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    check_result_axe: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
    )
    check_result_pdf: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": check_result_axe.id,
            "form-0-wcag_definition": check_result_axe.wcag_definition.id,
            "form-0-check_result_state": CheckResult.Result.ERROR,
            "form-0-notes": "",
            "form-1-id": check_result_pdf.id,
            "form-1-wcag_definition": check_result_pdf.wcag_definition.id,
            "form-1-check_result_state": CheckResult.Result.ERROR,
            "form-1-notes": CHECK_RESULT_NOTES,
            "complete_date": "on",
            "no_errors_date": "off",
        },
        follow=True,
    )

    assert response.status_code == 200

    assert (
        CheckResultNotesHistory.objects.filter(check_result=check_result_axe).count()
        == 0
    )
    assert (
        CheckResultNotesHistory.objects.filter(check_result=check_result_pdf).count()
        == 1
    )

    check_result_notes_history: CheckResultNotesHistory = (
        CheckResultNotesHistory.objects.get(check_result=check_result_pdf)
    )

    assert check_result_notes_history.notes == CHECK_RESULT_NOTES


def test_page_checks_shows_notes_history(admin_client):
    """Test page checks view shows the notes history"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )
    user: User = User.objects.create()

    CheckResultNotesHistory.objects.create(
        check_result=check_result,
        notes=HISTORIC_CHECK_RESULT_NOTES,
        created_by=user,
    )
    CheckResultNotesHistory.objects.create(
        check_result=check_result,
        created_by=user,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk),
    )

    assert response.status_code == 200

    assertContains(response, HISTORIC_CHECK_RESULT_NOTES)


def test_page_checks_edit_page_shows_location(admin_client):
    """Test page checks edit view page shows page location"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit, location=PAGE_LOCATION)
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_page_checks_edit_page_contains_hint_text(admin_client):
    """
    Test page checks page loads and contains WCAG definitoon hint text
    """
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    wcag_definition.hint = WCAG_DEFINITION_HINT
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, WCAG_DEFINITION_HINT)


@pytest.mark.parametrize(
    "url_name",
    ["audits:edit-audit-page-checks", "audits:edit-audit-retest-page-checks"],
)
def test_data_filter_string_contains_issue_identifier_on_check_result_pages(
    url_name, admin_client
):
    """
    Test data-filter-string contains issue identifier on check results pages
    """
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    wcag_definition.hint = "hint"
    wcag_definition.save()
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=page_pk))

    assert response.status_code == 200

    assertContains(
        response,
        f'data-filter-string="{wcag_definition} hint {check_result.issue_identifier}"',
    )


def test_page_checks_edit_hides_future_wcag_definitions(admin_client):
    """Test page checks edit view page loads and hides future WCAG definitions"""
    audit: Audit = create_audit_and_wcag()
    wcag_definition: WcagDefinition = WcagDefinition.objects.all().first()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, wcag_definition.name)

    wcag_definition.date_start = audit.date_of_test + timedelta(days=10)
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertNotContains(response, wcag_definition.name)


def test_page_checks_edit_hides_past_wcag_definitions(admin_client):
    """Test page checks edit view page loads and hides past WCAG definitions"""
    audit: Audit = create_audit_and_wcag()
    wcag_definition: WcagDefinition = WcagDefinition.objects.all().first()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, wcag_definition.name)

    wcag_definition.date_end = audit.date_of_test - timedelta(days=10)
    wcag_definition.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertNotContains(response, wcag_definition.name)


def test_page_checks_edit_saves_results(admin_client):
    """Test page checks edit view saves the entered results"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
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

    check_result_axe: CheckResult = CheckResult.objects.get(
        page=page, wcag_definition=wcag_definition_axe
    )
    assert check_result_axe.check_result_state == CheckResult.Result.ERROR
    assert check_result_axe.notes == CHECK_RESULT_NOTES

    check_result_pdf: CheckResult = CheckResult.objects.get(
        page=page, wcag_definition=wcag_definition_pdf
    )
    assert check_result_pdf.check_result_state == CheckResult.Result.ERROR
    assert check_result_pdf.notes == CHECK_RESULT_NOTES

    updated_page: Page = Page.objects.get(id=page.id)

    assert updated_page.complete_date
    assert updated_page.no_errors_date

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 3
    assert events[0].parent == check_result_pdf
    assert events[0].event_type == SimplifiedEventHistory.Type.CREATE
    assert events[1].parent == check_result_axe
    assert events[1].event_type == SimplifiedEventHistory.Type.CREATE
    assert events[2].parent == page
    assert events[2].event_type == SimplifiedEventHistory.Type.UPDATE
    assert (
        events[2].difference
        == f"""{{"complete_date": "None -> {TODAY}", "no_errors_date": "None -> {TODAY}"}}"""
    )


def test_page_checks_edit_stays_on_page(admin_client):
    """Test that a successful page checks edit stays on the page"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    url: str = reverse("audits:edit-audit-page-checks", kwargs=page_pk)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": audit.version,
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


def test_website_decision_saved_on_case(admin_client):
    """Test that a website decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-website-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
            "case-compliance-website_compliance_state_initial": WEBSITE_COMPLIANCE_STATE,
            "case-compliance-website_compliance_notes_initial": WEBSITE_COMPLIANCE_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: SimplifiedCase = SimplifiedCase.objects.get(
        id=audit.simplified_case.id
    )

    assert (
        updated_case.compliance.website_compliance_state_initial
        == WEBSITE_COMPLIANCE_STATE
    )
    assert (
        updated_case.compliance.website_compliance_notes_initial
        == WEBSITE_COMPLIANCE_NOTES
    )


@pytest.mark.parametrize(
    "field_name, new_value, report_content_update",
    [
        (
            "case-compliance-website_compliance_state_initial",
            "partially-compliant",
            True,
        ),
        ("case-compliance-website_compliance_notes_initial", "blah", False),
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
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    assert audit.published_report_data_updated_time is None
    context: dict[str, str | int] = {
        "version": audit.version,
        "case-compliance-version": audit.simplified_case.compliance.version,
        "case-compliance-website_compliance_state_initial": audit.simplified_case.compliance.website_compliance_state_initial,
        "save": "Button value",
    }
    context[field_name] = new_value

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-website-decision", kwargs=audit_pk), context
    )

    assert response.status_code == 302

    updated_audit: Audit = Audit.objects.get(id=audit.id)

    if report_content_update:
        assert updated_audit.published_report_data_updated_time is not None
    else:
        assert updated_audit.published_report_data_updated_time is None


def test_add_custom_statement_check_result_form_appears(admin_client):
    """
    Test that pressing the create issue button adds a new custom statement issue form
    """
    audit: Audit = create_audit_and_statement_check_results()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-custom", kwargs={"pk": audit.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            "add_custom": "Create issue",
        },
        follow=True,
    )
    assert response.status_code == 200
    assertContains(response, "Custom issue")

    audit_from_db: Audit = Audit.objects.get(id=audit.id)
    custom_statment_check_result: StatementCheckResult | None = (
        audit_from_db.custom_statement_check_results.first()
    )

    assert custom_statment_check_result is not None
    assertContains(response, custom_statment_check_result.issue_identifier)


def test_add_custom_statement_check_result(admin_client):
    """Test adding a custom statement issue"""
    audit: Audit = create_audit_and_statement_check_results()
    StatementCheckResult.objects.filter(
        audit=audit, type=StatementCheck.Type.CUSTOM
    ).delete()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-create", kwargs={"audit_id": audit.id}),
        {
            "report_comment": CUSTOM_STATEMENT_ISSUE,
            "auditor_notes": "",
            "save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200

    custom_statement_check_result: StatementCheckResult = (
        StatementCheckResult.objects.get(audit=audit, type=StatementCheck.Type.CUSTOM)
    )

    assert custom_statement_check_result.report_comment == CUSTOM_STATEMENT_ISSUE


def test_delete_custom_statement_check_result(admin_client):
    """
    Test that pressing the remove issue button deletes the custom statement issue
    """
    audit: Audit = create_audit_and_statement_check_results()
    custom_issue: StatementCheckResult = StatementCheckResult.objects.get(
        audit=audit, type=StatementCheck.Type.CUSTOM
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

    result_on_database: StatementCheckResult = StatementCheckResult.objects.get(
        audit=audit, type=StatementCheck.Type.CUSTOM
    )
    assert result_on_database.is_deleted is True


def test_delete_custom_retest_statement_check_result_on_retest(admin_client):
    """
    Test that pressing the remove issue button deletes the custom statement issue
    """
    audit: Audit = create_audit_and_statement_check_results()
    retest: Retest = Retest.objects.create(simplified_case=audit.simplified_case)
    custom_retest_statement_check_result: StatementCheckResult = (
        RetestStatementCheckResult.objects.create(retest=retest)
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-equality-body-statement-custom", kwargs={"pk": retest.id}),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "version": audit.version,
            f"remove_custom_{custom_retest_statement_check_result.id}": "Remove issue",
        },
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "No custom statement issues have been entered")

    result_on_database: RetestStatementCheckResult = (
        RetestStatementCheckResult.objects.get(
            id=custom_retest_statement_check_result.id
        )
    )

    assert result_on_database.is_deleted is True


def test_statement_decision_saved_on_case(admin_client):
    """Test that a statement decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-statement-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
            "case-compliance-statement_compliance_state_initial": STATEMENT_COMPLIANCE_STATE,
            "case-compliance-statement_compliance_notes_initial": STATEMENT_COMPLIANCE_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: SimplifiedCase = SimplifiedCase.objects.get(
        id=audit.simplified_case.id
    )

    assert (
        updated_case.compliance.statement_compliance_state_initial
        == STATEMENT_COMPLIANCE_STATE
    )
    assert (
        updated_case.compliance.statement_compliance_notes_initial
        == STATEMENT_COMPLIANCE_NOTES
    )


def test_start_retest_redirects(admin_client):
    """Test that starting a retest redirects to audit retest metadata"""
    audit: Audit = create_audit()
    audit_pk: int = audit.id
    path_kwargs: dict[str, int] = {"pk": audit_pk}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-retest-start", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-audit-retest-metadata", kwargs={"pk": audit_pk}
    )


def test_start_retest_creates_case_event(admin_client):
    """Test that starting a retest creates case event"""
    audit: Audit = create_audit()
    audit_pk: int = audit.id
    path_kwargs: dict[str, int] = {"pk": audit_pk}

    response: HttpResponse = admin_client.post(
        reverse("audits:audit-retest-start", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=audit.simplified_case
    )
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.START_RETEST
    assert case_event.message == "Started retest"


def test_retest_page_checks_edit_page_loads(admin_client):
    """Test retest page checks edit view page loads and contains errors"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(
        audit=audit, retest_notes=PAGE_RETEST_NOTES, location=PAGE_LOCATION
    )
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(response, "Additional page retest")
    assertContains(response, PAGE_RETEST_NOTES)
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, WCAG_TYPE_PDF_NAME)
    assertContains(response, PAGE_LOCATION)


def test_retest_page_checks_edit_saves_results(admin_client):
    """Test retest page checks edit view saves the entered results"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    check_result_axe: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CheckResult.Result.ERROR,
    )
    check_result_pdf: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": check_result_axe.id,
            "form-0-wcag_definition": check_result_axe.wcag_definition.id,
            "form-0-retest_state": "fixed",
            "form-0-retest_notes": CHECK_RESULT_NOTES,
            "form-1-id": check_result_pdf.id,
            "form-1-wcag_definition": check_result_pdf.wcag_definition.id,
            "form-1-retest_state": "not-fixed",
            "form-1-retest_notes": CHECK_RESULT_NOTES,
            "retest_complete_date": "on",
            "retest_page_missing_date": "on",
            "retest_notes": PAGE_RETEST_NOTES,
        },
        follow=True,
    )

    assert response.status_code == 200

    updated_check_result_axe: CheckResult = CheckResult.objects.get(
        id=check_result_axe.id
    )
    assert updated_check_result_axe.retest_state == "fixed"
    assert updated_check_result_axe.retest_notes == CHECK_RESULT_NOTES

    updated_check_result_pdf: CheckResult = CheckResult.objects.get(
        id=check_result_pdf.id
    )
    assert updated_check_result_pdf.retest_state == "not-fixed"
    assert updated_check_result_pdf.retest_notes == CHECK_RESULT_NOTES

    updated_page: Page = Page.objects.get(id=page.id)

    assert updated_page.retest_complete_date
    assert updated_page.retest_page_missing_date
    assert updated_page.retest_notes == PAGE_RETEST_NOTES

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 3
    assert events[0].parent == check_result_pdf
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE
    assert events[1].parent == check_result_axe
    assert events[1].event_type == SimplifiedEventHistory.Type.UPDATE
    assert events[2].parent == page
    assert events[2].event_type == SimplifiedEventHistory.Type.UPDATE
    assert (
        events[2].difference
        == f'{{"retest_complete_date": "None -> {TODAY}", "retest_page_missing_date": "None -> {TODAY}", "retest_notes": " -> Retest notes"}}'
    )


def test_retest_page_checks_edit_adds_to_retest_notes_history(admin_client):
    """
    Test retest page checks edit view adds to the retest notes history when the
    retest notes have changed
    """
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    check_result_axe: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CheckResult.Result.ERROR,
    )
    check_result_pdf: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": check_result_axe.id,
            "form-0-wcag_definition": check_result_axe.wcag_definition.id,
            "form-0-retest_state": CheckResult.RetestResult.FIXED,
            "form-0-retest_notes": "",
            "form-1-id": check_result_pdf.id,
            "form-1-wcag_definition": check_result_pdf.wcag_definition.id,
            "form-1-retest_state": CheckResult.RetestResult.NOT_FIXED,
            "form-1-retest_notes": CHECK_RESULT_NOTES,
            "retest_complete_date": "on",
            "retest_page_missing_date": "on",
        },
        follow=True,
    )

    assert response.status_code == 200

    assert (
        CheckResultRetestNotesHistory.objects.filter(
            check_result=check_result_axe
        ).count()
        == 0
    )
    assert (
        CheckResultRetestNotesHistory.objects.filter(
            check_result=check_result_pdf
        ).count()
        == 1
    )

    check_result_retest_notes_history: CheckResultRetestNotesHistory = (
        CheckResultRetestNotesHistory.objects.get(check_result=check_result_pdf)
    )

    assert check_result_retest_notes_history.retest_notes == CHECK_RESULT_NOTES
    assert (
        check_result_retest_notes_history.retest_state
        == CheckResult.RetestResult.NOT_FIXED
    )


def test_retest_page_checks_shows_retest_notes_history(admin_client):
    """Test retest page checks view shows the retest notes history"""
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit)
    page_pk: dict[str, int] = {"pk": page.id}
    wcag_definition: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )
    user: User = User.objects.create()

    CheckResultRetestNotesHistory.objects.create(
        check_result=check_result,
        retest_notes=HISTORIC_RETEST_NOTES,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        created_by=user,
    )
    CheckResultRetestNotesHistory.objects.create(
        check_result=check_result,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        created_by=user,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-page-checks", kwargs=page_pk),
    )

    assert response.status_code == 200

    assertContains(response, HISTORIC_RETEST_NOTES)


def test_retest_pages_shows_location(admin_client):
    """Test page location is shown"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(
        audit=audit, url="https://example.com", location=PAGE_LOCATION
    )
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.PDF
    )
    wcag_definition_axe: WcagDefinition = WcagDefinition.objects.get(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        notes=FIXED_ERROR_NOTES,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_axe,
        check_result_state=CheckResult.Result.ERROR,
    )

    url: str = reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)

    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_retest_website_decision_saved_on_case(admin_client):
    """Test that a retest website decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-website-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
            "case-compliance-website_compliance_state_12_week": WEBSITE_COMPLIANCE_STATE,
            "case-compliance-website_compliance_notes_12_week": WEBSITE_COMPLIANCE_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: SimplifiedCase = SimplifiedCase.objects.get(
        id=audit.simplified_case.id
    )

    assert (
        updated_case.compliance.website_compliance_state_12_week
        == WEBSITE_COMPLIANCE_STATE
    )
    assert (
        updated_case.compliance.website_compliance_notes_12_week
        == WEBSITE_COMPLIANCE_NOTES
    )


def test_retest_statement_decision_saved_on_case(admin_client):
    """Test that a retest statement decision is saved on case"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk),
        {
            "version": audit.version,
            "save": "Button value",
            "case-compliance-version": audit.simplified_case.compliance.version,
            "case-compliance-statement_compliance_state_12_week": STATEMENT_COMPLIANCE_STATE,
            "case-compliance-statement_compliance_notes_12_week": STATEMENT_COMPLIANCE_NOTES,
        },
    )

    assert response.status_code == 302

    updated_case: SimplifiedCase = SimplifiedCase.objects.get(
        id=audit.simplified_case.id
    )

    assert (
        updated_case.compliance.statement_compliance_state_12_week
        == STATEMENT_COMPLIANCE_STATE
    )
    assert (
        updated_case.compliance.statement_compliance_notes_12_week
        == STATEMENT_COMPLIANCE_NOTES
    )


def test_retest_statement_decision_hides_initial_decision(admin_client):
    """
    Test that retest statement decision hides initial decision if none
    was entered.
    """
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}
    statement_page: StatementPage = StatementPage.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, "View initial decision")

    statement_page.added_stage = (StatementPage.AddedStage.TWELVE_WEEK,)
    statement_page.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-retest-statement-decision", kwargs=audit_pk)
    )

    assert response.status_code == 200
    assertContains(response, "Statement missing during initial test")


def test_retest_statement_custom_no_initial(admin_client):
    """Test that a retest statement custom with no initial failure shows placeholder"""
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-retest-statement-custom", kwargs=audit_pk),
    )

    assert response.status_code == 200
    assertContains(response, "No custom statement issues were initially entered")


def test_retest_statement_custom_with_initial(admin_client):
    """Test that a retest statement custom with an initial failure shows it"""
    audit: Audit = create_audit_and_statement_check_results()
    audit_pk: dict[str, int] = {"pk": audit.id}

    StatementPage.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-retest-statement-custom", kwargs=audit_pk),
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
    """Test WCAG definition list cab be filtered by each field"""
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
    audit: Audit = create_audit()
    audit.published_report_data_updated_time = timezone.now()
    audit.save()
    audit_pk: dict[str, int] = {"pk": audit.id}

    admin_client.get(
        reverse("audits:clear-outdated-published-report-warning", kwargs=audit_pk)
    )

    audit_from_db: Audit = Audit.objects.get(**audit_pk)

    assert audit_from_db.published_report_data_updated_time is None


def test_update_audit_checks_version(admin_client):
    """Test that updating an audit shows an error if the version of the audit has changed"""
    audit: Audit = create_audit()
    simplified_case: SimplifiedCase = audit.simplified_case

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id}),
        {
            "version": audit.version - 1,
            "case-compliance-version": simplified_case.compliance.version,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {str(audit)} has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-website-decision",
        "audits:edit-statement-decision",
        "audits:edit-audit-retest-website-decision",
        "audits:edit-audit-retest-statement-decision",
    ],
)
def test_update_audit_checks_case_version(url_name, admin_client):
    """
    Test that updating a case shows an error if the version of the case compliance has changed
    """
    audit: Audit = create_audit()
    simplified_case: SimplifiedCase = audit.simplified_case

    response: HttpResponse = admin_client.post(
        reverse(url_name, kwargs={"pk": audit.id}),
        {
            "version": audit.version,
            "case-compliance-version": simplified_case.compliance.version - 1,
            "save": "Button value",
        },
    )
    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-error-summary__body">
            <ul class="govuk-list govuk-error-summary__list">
                <li class="govuk-error-message">
                    {str(simplified_case.compliance)} has changed since this page loaded
                </li>
            </ul>
        </div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-metadata",
        "audits:edit-statement-overview",
    ],
)
def test_frequently_used_links_displayed(url_name, admin_client):
    """
    Test that the frequently used links are displayed
    """
    audit: Audit = create_audit()

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs={"pk": audit.id}),
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
    "url_name",
    [
        "audits:edit-audit-wcag-summary",
        "audits:edit-audit-retest-wcag-summary",
    ],
)
def test_summary_page_view(url_name, admin_client):
    """Test that summary page view renders with results grouped by page"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.get(
        f"{reverse(url_name, kwargs=audit_pk)}?page-view=true",
    )

    assert response.status_code == 200
    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">WCAG issue</th>',
        html=True,
    )
    assertContains(response, "Group by WCAG issue")


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-wcag-summary",
        "audits:edit-audit-retest-wcag-summary",
    ],
)
def test_summary_wcag_view(url_name, admin_client):
    """Test that summary page view renders with results grouped by WCAG issue"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
    )

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200
    assertContains(
        response,
        '<th scope="col" class="govuk-table__header amp-width-one-third">Page</th>',
        html=True,
    )
    assertContains(response, "Group by page")


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-wcag-summary",
        "audits:edit-audit-retest-wcag-summary",
    ],
)
def test_summary_page_view_unfixed(url_name, admin_client):
    """Test that summary page view renders with unfixed results only"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        retest_notes=FIXED_ERROR_NOTES,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        retest_notes=UNFIXED_ERROR_NOTES,
    )

    response: HttpResponse = admin_client.get(
        reverse(url_name, kwargs=audit_pk),
    )

    assert response.status_code == 200

    assertNotContains(response, FIXED_ERROR_NOTES)
    assertContains(response, UNFIXED_ERROR_NOTES)
    assertContains(response, "View all issues")


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-wcag-summary",
        "audits:edit-audit-retest-wcag-summary",
    ],
)
def test_summary_page_view_show_all(url_name, admin_client):
    """Test that summary page view renders with all results"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        retest_notes=FIXED_ERROR_NOTES,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition_pdf,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        retest_notes=UNFIXED_ERROR_NOTES,
    )

    response: HttpResponse = admin_client.get(
        f"{reverse(url_name, kwargs=audit_pk)}?show-all=true",
    )

    assert response.status_code == 200

    assertContains(response, FIXED_ERROR_NOTES)
    assertContains(response, UNFIXED_ERROR_NOTES)
    assertContains(response, "View only unfixed issues")


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-statement-summary",
        "audits:edit-audit-retest-statement-summary",
    ],
)
def test_test_statement_summary_page_view(url_name, admin_client):
    """Test that statement summary page views contain statement results"""
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}
    StatementPage.objects.create(audit=audit, url="https://example.com")
    overview_statement_check: StatementCheck | None = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).first()
    StatementCheckResult.objects.create(
        statement_check=overview_statement_check,
        audit=audit,
        type=StatementCheck.Type.OVERVIEW,
        check_result_state=StatementCheckResult.Result.YES,
    )
    statement_check: StatementCheck = StatementCheck.objects.filter(
        type=StatementCheck.Type.WEBSITE
    ).first()
    StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
        check_result_state=StatementCheckResult.Result.NO,
        report_comment=STATEMENT_CHECK_INITIAL_COMMENT,
    )
    StatementCheckResult.objects.create(
        audit=audit,
        type=StatementCheck.Type.CUSTOM,
        report_comment=STATEMENT_CHECK_CUSTOM_COMMENT,
    )
    StatementCheckResult.objects.create(
        audit=audit,
        type=StatementCheck.Type.TWELVE_WEEK,
        retest_comment=NEW_12_WEEK_CUSTOM_RETEST_COMMENT,
    )

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200

    assertContains(response, STATEMENT_CHECK_INITIAL_COMMENT)
    assertContains(response, STATEMENT_CHECK_CUSTOM_COMMENT)
    assertContains(response, NEW_12_WEEK_CUSTOM_RETEST_COMMENT)


@pytest.mark.parametrize(
    "url_name",
    [
        "audits:edit-audit-statement-summary",
        "audits:edit-audit-retest-statement-summary",
    ],
)
def test_test_statement_summary_page_summary(url_name, admin_client):
    """
    Test that statement summary page shows initial compliance values before 12-week
    values are entered.
    """
    audit: Audit = create_audit()
    audit_pk: dict[str, int] = {"pk": audit.id}

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200
    assertContains(response, "<li>Initial statement compliance: <b>")
    assertContains(response, "<li>Initial disproportionate burden: <b>")
    assertNotContains(response, "<li>12-week statement compliance: <b>")
    assertNotContains(response, "<li>12-week disproportionate burden: <b>")

    audit.twelve_week_disproportionate_burden_claim = (
        Audit.DisproportionateBurden.ASSESSMENT
    )
    audit.save()
    audit.simplified_case.compliance.statement_compliance_state_12_week = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    audit.simplified_case.compliance.save()

    response: HttpResponse = admin_client.get(reverse(url_name, kwargs=audit_pk))

    assert response.status_code == 200
    assertNotContains(response, "<li>Initial statement compliance: <b>")
    assertNotContains(response, "<li>Initial disproportionate burden: <b>")
    assertContains(response, "<li>12-week statement compliance: <b>")
    assertContains(response, "<li>12-week disproportionate burden: <b>")


def test_create_equality_body_retest_redirects(admin_client):
    """Test that equality body retest create redirects to retest metadata"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:create-equality-body-retest", kwargs=path_kwargs)
    )

    assert response.status_code == 302

    retest: Retest = Retest.objects.filter(simplified_case=simplified_case).first()
    assert response.url == reverse(
        "audits:retest-metadata-update", kwargs={"pk": retest.id}
    )


def test_create_equality_body_retest_creates_retest_0(admin_client):
    """
    Test that equality body retest create creates an extra retest (with
    id_within_case set to zero) the first time only.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:create-equality-body-retest", kwargs=path_kwargs)
    )

    assert response.status_code == 302

    assert Retest.objects.filter(simplified_case=simplified_case).count() == 2

    retest_1: Retest = Retest.objects.filter(simplified_case=simplified_case).first()
    retest_0: Retest = Retest.objects.filter(simplified_case=simplified_case).last()

    assert retest_1.id_within_case == 1
    assert retest_0.id_within_case == 0

    response: HttpResponse = admin_client.get(
        reverse("audits:create-equality-body-retest", kwargs=path_kwargs)
    )

    assert response.status_code == 302

    assert Retest.objects.filter(simplified_case=simplified_case).count() == 3

    retest_2: Retest = Retest.objects.filter(simplified_case=simplified_case).first()

    assert retest_2.id_within_case == 2


def test_delete_retest(admin_client):
    """
    Test that equality body retest deletion works
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    # Audit.objects.create(simplified_case=simplified_case)
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
        (
            "audits:retest-compliance-update",
            "save_continue",
            "audits:edit-equality-body-statement-pages",
        ),
        (
            "audits:edit-equality-body-statement-pages",
            "save",
            "audits:edit-equality-body-statement-pages",
        ),
        (
            "audits:edit-equality-body-statement-pages",
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
            "audits:edit-equality-body-statement-website",
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
        (
            "audits:edit-equality-body-statement-decision",
            "save_continue",
            "simplified:edit-retest-overview",
        ),
    ],
)
def test_equality_body_retest_edit_redirects_based_on_button_pressed(
    path_name,
    button_name,
    expected_redirect_path_name,
    admin_client,
):
    """
    Test that a successful equality body retest update redirects based on the button pressed
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}

    response: HttpResponse = admin_client.post(
        reverse(path_name, kwargs=retest_pk),
        {
            "version": retest.version,
            button_name: "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(expected_redirect_path_name, kwargs=retest_pk)
    assert response.url == expected_path


def test_equality_body_retest_statement_overview_redirects_when_no(admin_client):
    """
    Test that an equality body retest statement overview redirects to statement
    results when one of the overview questions has been answered 'no'.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    statement_check: StatementCheck = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).first()
    RetestStatementCheckResult.objects.create(
        retest=retest,
        statement_check=statement_check,
        type=StatementCheck.Type.OVERVIEW,
        check_result_state=RetestStatementCheckResult.Result.NO,
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-equality-body-statement-overview", kwargs=retest_pk),
        {
            "version": retest.version,
            "save_continue": "Button value",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-equality-body-statement-results", kwargs=retest_pk
    )


def test_equality_body_retest_metadata_update_redirects_to_retest_page_checks(
    admin_client,
):
    """
    Test that a equality body retest metadata update redirects to retest page checks when save
    and continue button is pressed.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    retest_page: RetestPage = retest.retestpage_set.first()
    retest_page_pk: dict[str, int] = {"pk": retest_page.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:retest-metadata-update", kwargs=retest_pk),
        {
            "version": retest.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse(
        "audits:edit-retest-page-checks", kwargs=retest_page_pk
    )
    assert response.url == expected_path


def test_equality_body_page_checks_save(
    admin_client,
):
    """Test that a equality body retest page checks saves"""
    retest: Retest = create_equality_body_retest()
    retest_page: RetestPage = retest.retestpage_set.first()
    retest_page_pk: dict[str, int] = {"pk": retest_page.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=retest_page_pk),
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
        "audits:edit-retest-page-checks", kwargs=retest_page_pk
    )
    assert response.url == expected_path


def test_equality_body_page_location_shown(admin_client):
    """Test that a equality body retest page show the location"""
    retest: Retest = create_equality_body_retest()
    retest_page: RetestPage = retest.retestpage_set.first()
    retest_page_pk: dict[str, int] = {"pk": retest_page.id}
    page: Page = retest_page.page
    page.location = PAGE_LOCATION
    page.save()

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-retest-page-checks", kwargs=retest_page_pk),
    )

    assert response.status_code == 200

    assertContains(response, PAGE_LOCATION)


def test_equality_body_page_checks_save_continue(
    admin_client,
):
    """Test that a equality body retest page checks redirects on save and continue"""
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    retest_page: RetestPage = retest.retestpage_set.first()
    retest_page_pk: dict[str, int] = {"pk": retest_page.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=retest_page_pk),
        {
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("audits:retest-comparison-update", kwargs=retest_pk)
    assert response.url == expected_path


def test_equality_body_retest_statement_pages_default_added_stage(
    admin_client,
):
    """
    Test that added stage for new entries defaults to retest
    for equality body-requested retests.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}

    response: HttpResponse = admin_client.get(
        f'{reverse("audits:edit-equality-body-statement-pages", kwargs=retest_pk)}?add_extra=true#statement-page-None'
    )

    assert response.status_code == 200

    assertContains(response, STATEMENT_PAGE_EWUALITY_BODY_RETEST_CHECKED, html=True)


def test_equality_body_retest_statement_compliance_update_redirects_to_retest_overview_based_on_button_pressed(
    admin_client,
):
    """
    Test that a equality body retest statement compliance update redirects
    to retest overview when save and continue button is pressed.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    case_pk: dict[str, int] = {"pk": retest.simplified_case.id}

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-equality-body-statement-decision", kwargs=retest_pk),
        {
            "version": retest.version,
            "save_continue": "Button value",
        },
    )

    assert response.status_code == 302

    expected_path: str = reverse("simplified:edit-retest-overview", kwargs=case_pk)
    assert response.url == expected_path


def test_equality_body_page_checks_page_missing(
    admin_client,
):
    """
    Test that when equality body retest page is marked as missing the underling
    page is also so marked.
    """
    retest: Retest = create_equality_body_retest()
    retest_page: RetestPage = retest.retestpage_set.first()
    retest_page_pk: dict[str, int] = {"pk": retest_page.id}

    assert retest_page.missing_date is None
    assert retest_page.page.not_found == "no"

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-retest-page-checks", kwargs=retest_page_pk),
        {
            "missing_date": "on",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "save": "Button value",
        },
    )

    assert response.status_code == 302

    updated_retest_page: RetestPage = RetestPage.objects.get(id=retest_page.id)

    assert updated_retest_page.missing_date is not None
    assert updated_retest_page.page.not_found == "yes"


def test_retest_comparison_page_groups_by_page_or_wcag(admin_client):
    """
    Test that equality body retest comparison page groups content by page or
    WCAG based on URL parameter.
    """
    retest: Retest = create_equality_body_retest()
    retest_pk: dict[str, int] = {"pk": retest.id}
    create_checkresults_for_retest(retest=retest)

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
    create_checkresults_for_retest(retest=retest)

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
    audit: Audit = create_audit_and_wcag()
    audit_pk: dict[str, int] = {"pk": audit.id}
    Page.objects.create(audit=audit, url="https://example.com")

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs=audit_pk)
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<details class="amp-nav-details">
            <summary class="amp-nav-details__summary">
                Case details (0/1)
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
            Initial WCAG test (0/5)
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
        """<ul class="amp-nav-list-subpages">
            <li class="amp-nav-list-subpages amp-margin-top-5">
                <a href="/audits/pages/6/edit-audit-page-checks/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                    Additional page test</a>
            </li>
        </ul>""",
        html=True,
    )


def test_nav_details_subpage_renders(admin_client):
    """
    Test that the nav detail with current subpage renders as expected
    """
    audit: Audit = create_audit_and_wcag()
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    page_pk: dict[str, int] = {"pk": page.id}

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs=page_pk)
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<details class="amp-nav-details">
            <summary class="amp-nav-details__summary">
                Case details (0/1)
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
            Initial WCAG test (0/5)
        </p>""",
        html=True,
    )
    assertContains(
        response,
        """<a href="/audits/1/edit-audit-pages/" class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
            Add or remove pages</a>""",
        html=True,
    )
    assertContains(
        response,
        """<ul class="amp-nav-list-subpages">
            <li class="amp-nav-list-subpages amp-margin-top-5"><b>Additional page test</b></li>
        </ul>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name",
    [
        "audits:edit-audit-page-checks",
        "audits:edit-audit-retest-page-checks",
    ],
)
def test_tall_results_page_has_back_to_top_link(path_name, admin_client):
    """Test that tall pages include a back to top link"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit)
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
        ("edit-statement-overview", "Initial statement | Statement information"),
        ("edit-statement-overview", "Initial statement | Custom issues"),
        ("edit-audit-retest-metadata", "12-week WCAG test | Update page links"),
        ("edit-audit-retest-pages", "12-week WCAG test | Compliance decision"),
        ("edit-retest-statement-overview", "12-week statement | Statement information"),
        (
            "edit-retest-statement-overview",
            "12-week statement | Custom issues",
        ),
    ],
)
def test_audit_next_page_name(path_name, expected_next_page, admin_client):
    """
    Test next page shown for when Save and continue button pressed on audit
    """
    audit: Audit = create_audit_and_statement_check_results()
    url: str = reverse(f"audits:{path_name}", kwargs={"pk": audit.id})

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


def test_create_initial_custom_issue_redirects(admin_client):
    """
    Test that statement initial custom issue create redirects to initial statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-create", kwargs={"audit_id": audit.id}),
        {
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    custom_issue: StatementCheckResult = StatementCheckResult.objects.get(audit=audit)
    response_url: str = reverse("audits:edit-statement-custom", kwargs={"pk": audit.id})

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
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    custom_issue: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-update", kwargs={"pk": custom_issue.id}),
        {
            "auditor_notes": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse("audits:edit-statement-custom", kwargs={"pk": audit.id})

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
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    custom_issue: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit
    )

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-delete", kwargs={"pk": custom_issue.id}),
        {},
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "audits:edit-statement-custom", kwargs={"pk": audit.id}
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
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    custom_issue: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-initial-custom-issue-update",
            kwargs={"pk": custom_issue.id},
        ),
        {
            "retest_state": "yes",
            "auditor_notes": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": audit.id}
    )

    assert response.url == f"{response_url}#{custom_issue.issue_identifier}"

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE


def test_create_new_12_week_custom_issue_redirects(admin_client):
    """
    Test that statement new 12-week custom issue create redirects to 12-week statement
    custom issues page.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-12-week-custom-issue-create",
            kwargs={"audit_id": audit.id},
        ),
        {
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    custom_issue: StatementCheckResult = StatementCheckResult.objects.get(audit=audit)
    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": audit.id}
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
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    custom_issue: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "audits:edit-retest-new-12-week-custom-issue-update",
            kwargs={"pk": custom_issue.id},
        ),
        {
            "auditor_notes": "Made a change",
            "save": "Save and return",
        },
    )

    assert response.status_code == 302

    response_url: str = reverse(
        "audits:edit-retest-statement-custom", kwargs={"pk": audit.id}
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
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    custom_issue: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit
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
        "audits:edit-retest-statement-custom", kwargs={"pk": audit.id}
    )

    events: QuerySet[SimplifiedEventHistory] = SimplifiedEventHistory.objects.all()

    assert events.count() == 1
    assert events[0].parent == custom_issue
    assert events[0].event_type == SimplifiedEventHistory.Type.UPDATE
