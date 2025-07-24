"""Test sitemap case navigation"""

from datetime import date

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...audits.models import Audit, Page, StatementCheck, StatementCheckResult
from ...common.models import FrequentlyUsedLink
from ...reports.models import Report
from ...simplified.models import Contact, SimplifiedCase

CURRENT_PAGE_GROUP: str = '<p class="govuk-body-s amp-margin-bottom-5">{name}</p>'
CURRENT_PAGE_STANDALONE: str = "<li><b>{name}</b></li>"
CURRENT_PAGE_NO_SUBPAGES: str = (
    '<li><b>{name}</b><ul class="amp-nav-list-subpages"></ul></li>'
)
OTHER_PAGE_GROUP: str = '<summary class="amp-nav-details__summary">{name}</summary>'
OTHER_PAGE_STANDALONE: str = """<li>
   <a href="{url}"
        class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
        {name}</a>
</li>"""
OTHER_PAGE_NO_SUBPAGES: str = """<li class="amp-nav-list-subpages amp-margin-top-5">
   <a href="{url}"
       class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
       {name}</a>
</li>"""
OTHER_PAGE_SUBPAGE: str = """<li>
   <a href="{url}"
       class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
       {name}</a>
       <ul class="amp-nav-list-subpages">
           <li class="amp-nav-list-subpages amp-margin-top-5">
               <b>{subpage_name}</b>
           </li>
       </ul>
</li>"""
CONTACT_EMAIL: str = "contact@email.com"
WCAG_PAGE_NAME: str = "WCAG Page Name"
CASE_TOOL: str = """<li>
   <a href="{url}"
       rel="noreferrer noopener"
       class="govuk-link govuk-link--no-visited-state">
       {name}</a>
</li>"""
FREQUENTLY_USED_LINK_NAME: str = "Frequently used link"
FREQUENTLY_USED_LINK_URL: str = "https://example.com/frequently-used-link"
FREQUENTLY_USED_LINK: str = """<li>
   <a href="{url}"
       target="_blank"
       class="govuk-link govuk-link--no-visited-state">
       {name}</a>
</li>"""


def test_current_page_in_case_nav(admin_client):
    """Test current page is rendered in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Case details (0/1)"),
        html=True,
    )
    assertContains(
        response, CURRENT_PAGE_STANDALONE.format(name="Case metadata"), html=True
    )


def test_other_page_in_case_nav(admin_client):
    """Test other page and group rendered in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial test"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="Testing details", url="/simplified/1/edit-test-results/"
        ),
        html=True,
    )


def test_start_initial_test_page_shown(admin_client):
    """Test page to start initial test shown and initial test pages not shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial test"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial WCAG test (0/4)"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial statement (0/6)"),
        html=True,
    )


def test_start_initial_test_page_hidden(admin_client):
    """Test page to start initial test hidden and initial test pages shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial test"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial WCAG test (0/4)"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Initial statement (0/6)"),
        html=True,
    )


def test_dynamic_wcag_pages_hidden(admin_client):
    """Test WCAG-specific pages are hidden in case nav on other pages"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-pages", kwargs={"pk": audit.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Initial WCAG test (0/4)"),
        html=True,
    )
    assertContains(
        response,
        CURRENT_PAGE_STANDALONE.format(name="Add or remove pages"),
        html=True,
    )


def test_dynamic_wcag_pages_shown(admin_client):
    """Test WCAG-specific pages are shown in case nav on that page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(
        audit=audit, name=WCAG_PAGE_NAME, url="https:example.com"
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Initial WCAG test (0/5)"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_SUBPAGE.format(
            name="Add or remove pages",
            url="/audits/1/edit-audit-pages/",
            subpage_name=f"{page.page_title} test",
        ),
        html=True,
    )


def test_dynamic_statement_pages_hidden(admin_client):
    """Test statement subpages are hidden in case nav on other pages"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-statement-overview", kwargs={"pk": audit.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Initial statement (0/6)"),
        html=True,
    )
    assertContains(
        response,
        CURRENT_PAGE_NO_SUBPAGES.format(name="Statement overview"),
        html=True,
    )


def test_dynamic_statement_pages_shown(admin_client):
    """Test statement-specific pages are shown in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    statement_check: StatementCheck | None = StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ).first()
    StatementCheckResult.objects.create(
        statement_check=statement_check,
        audit=audit,
        type=StatementCheck.Type.OVERVIEW,
        check_result_state=StatementCheckResult.Result.YES,
    )

    response: HttpResponse = admin_client.get(
        reverse("audits:edit-statement-overview", kwargs={"pk": audit.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Initial statement (0/11)"),
        html=True,
    )
    assertContains(response, "<b>Statement overview</b>", html=True)
    assertContains(
        response,
        OTHER_PAGE_NO_SUBPAGES.format(
            name="Statement information", url="/audits/1/edit-statement-website/"
        ),
        html=True,
    )


def test_start_report_test_page_shown(admin_client):
    """Test page to start report shown and report pages not shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Start report"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Report QA (0/4)"),
        html=True,
    )


def test_start_report_test_page_hidden(admin_client):
    """Test page to start report hidden and report pages shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Start report"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Report QA (0/4)"),
        html=True,
    )


def test_dynamic_contact_pages_hidden(admin_client):
    """Test contact-specific pages are hidden in case nav on other pages"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Contact details (0/1)"),
        html=True,
    )
    assertContains(
        response,
        CURRENT_PAGE_NO_SUBPAGES.format(name="Manage contact details"),
        html=True,
    )


def test_dynamic_contact_pages_shown(admin_client):
    """Test contact-specific pages are shown in case nav on that page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(
        simplified_case=simplified_case, email=CONTACT_EMAIL
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-contact-update", kwargs={"pk": contact.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Contact details (0/1)"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_SUBPAGE.format(
            name="Manage contact details",
            url="/simplified/1/manage-contact-details/",
            subpage_name=f"Edit contact {CONTACT_EMAIL}",
        ),
        html=True,
    )


def test_dynamic_contact_correspondence_pages_hidden(admin_client):
    """Test contact correspondence-specific pages are hidden in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Contact details (0/1)"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="Request contact details",
            url="/simplified/1/edit-request-contact-details/",
        ),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="One-week follow-up",
            url="/simplified/1/edit-one-week-contact-details/",
        ),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="Four-week follow-up",
            url="/simplified/1/edit-four-week-contact-details/",
        ),
        html=True,
    )


def test_dynamic_contact_correspondence_pages_shown(admin_client):
    """Test contact-specific pages are shown in case nav on that page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        enable_correspondence_process=True
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:manage-contact-details", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        CURRENT_PAGE_GROUP.format(name="Contact details (0/4)"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="Request contact details",
            url="/simplified/1/edit-request-contact-details/",
        ),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="One-week follow-up",
            url="/simplified/1/edit-one-week-contact-details/",
        ),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_STANDALONE.format(
            name="Four-week follow-up",
            url="/simplified/1/edit-four-week-contact-details/",
        ),
        html=True,
    )


def test_start_12_week_retest_page_shown(admin_client):
    """Test page to start 12-week retest shown and 12-week retest pages not shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="Start 12-week retest"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="12-week WCAG test (0/4)"),
        html=True,
    )
    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="12-week statement (0/6)"),
        html=True,
    )


def test_start_12_week_retest_page_hidden(admin_client):
    """Test page to start 12-week retest hidden and 12-week retest pages shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case, retest_date=date.today())

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertNotContains(
        response,
        OTHER_PAGE_GROUP.format(name="Start 12-week retest"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="12-week WCAG test (0/4)"),
        html=True,
    )
    assertContains(
        response,
        OTHER_PAGE_GROUP.format(name="12-week statement (0/6)"),
        html=True,
    )


@pytest.mark.parametrize(
    "tool_name, tool_url",
    [
        ("View and search all case data", "/simplified/1/case-view-and-search/"),
        ("Outstanding issues", "/simplified/1/outstanding-issues/"),
        ("Email templates", "/simplified/1/email-template-list/"),
        ("PSB Zendesk tickets", "/simplified/1/zendesk-tickets/"),
        (
            "Equality body Zendesk tickets",
            "/simplified/1/list-equality-body-correspondence/",
        ),
        ("Unresponsive PSB", "/simplified/1/edit-no-psb-response/"),
    ],
)
def test_case_tool_shown_for_simplified_case(tool_name, tool_url, admin_client):
    """Test simplified case tools shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h2 class="govuk-heading-s amp-margin-bottom-10">Case tools</h2>',
        html=True,
    )
    assertContains(
        response,
        CASE_TOOL.format(name=tool_name, url=tool_url),
        html=True,
    )


def test_frequently_used_links_shown_for_simplified_case(admin_client):
    """Test simplified case links shown"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    FrequentlyUsedLink.objects.create(
        label=FREQUENTLY_USED_LINK_NAME, url=FREQUENTLY_USED_LINK_URL
    )

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        '<h2 class="govuk-heading-s amp-margin-bottom-10">Links</h2>',
        html=True,
    )
    assertContains(
        response,
        FREQUENTLY_USED_LINK.format(
            name=FREQUENTLY_USED_LINK_NAME, url=FREQUENTLY_USED_LINK_URL
        ),
        html=True,
    )
