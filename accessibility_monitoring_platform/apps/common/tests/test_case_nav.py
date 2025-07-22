"""Test sitemap case navigation"""

# import pytest
# from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Audit, Page, StatementCheck, StatementCheckResult
from ...simplified.models import Contact, SimplifiedCase

CONTACT_EMAIL: str = "contact@email.com"
WCAG_PAGE_NAME: str = "WCAG Page Name"


def test_current_page_in_case_nav(admin_client):
    """Test current page is rendered in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<p class="govuk-body-s amp-margin-bottom-5">Case details (0/1)</p>""",
        html=True,
    )
    assertContains(response, """<li><b>Case metadata</b></li>""", html=True)


def test_other_page_in_case_nav(admin_client):
    """Test other page and group rendered in case nav"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<summary class="amp-nav-details__summary">Initial test</summary>""",
        html=True,
    )
    assertContains(
        response,
        """<li>
               <a href="/simplified/1/edit-test-results/"
                    class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                    Testing details</a>
           </li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Initial WCAG test (0/4)</p>""",
        html=True,
    )
    assertContains(
        response,
        """<li><b>Add or remove pages</b></li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Initial WCAG test (0/5)</p>""",
        html=True,
    )
    assertContains(
        response,
        f"""<li>
            <a href="/audits/1/edit-audit-pages/"
                class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                Add or remove pages</a>
                <ul class="amp-nav-list-subpages">
                    <li class="amp-nav-list-subpages amp-margin-top-5">
                        <b>{page.page_title} test</b>
                    </li>
                </ul>
            </li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Initial statement (0/6)</p>""",
        html=True,
    )
    assertContains(
        response,
        """<li><b>Statement overview</b><ul class="amp-nav-list-subpages"></ul></li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Initial statement (0/11)</p>""",
        html=True,
    )
    assertContains(response, "<b>Statement overview</b>", html=True)
    assertContains(
        response,
        """<li class="amp-nav-list-subpages amp-margin-top-5">
            <a href="/audits/1/edit-statement-website/"
                class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                Statement information</a>
        </li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Contact details (0/1)</p>""",
        html=True,
    )
    assertContains(
        response,
        """<li><b>Manage contact details</b><ul class="amp-nav-list-subpages"></ul></li>""",
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
        """<p class="govuk-body-s amp-margin-bottom-5">Contact details (0/1)</p>""",
        html=True,
    )
    assertContains(
        response,
        f"""<li>
               <a href="/simplified/1/manage-contact-details/"
                    class="govuk-link govuk-link--no-visited-state govuk-link--no-underline">
                    Manage contact details</a>
               <ul class="amp-nav-list-subpages">
                    <li class="amp-nav-list-subpages amp-margin-top-5">
                        <b>Edit contact {CONTACT_EMAIL}</b>
                    </li>
               </ul>
           </li>""",
        html=True,
    )
