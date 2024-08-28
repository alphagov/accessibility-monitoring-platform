"""
Test utility functions of cases app
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from ...audits.models import Audit, Page, Retest, RetestPage
from ...cases.models import Case, Contact
from ...common.models import EmailTemplate
from ..sitemap import HomePlatformPage, PlatformPage, get_current_platform_page

PLATFORM_PAGE_NAME: str = "Platform page name"
URL_NAME: str = "url-name"
ORGANISATION_NAME: str = "Organisation name"
EMAIL_TEMPLATE_NAME: str = "1c. Template name"


class MockRequest:
    def __init__(self, get_params=None):
        if get_params is None:
            self.GET = {}
        else:
            self.GET = get_params


def test_platform_page_url_kwarg_key():
    """
    Test PlatformPage url_kwarg_key defaults to "pk" if an object_class is set
    """
    assert PlatformPage(name=PLATFORM_PAGE_NAME).url_kwarg_key is None
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case).url_kwarg_key == "pk"
    )


def test_platform_page_repr():
    """Test PlatformPage.__repr__()"""
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME).__repr__()
        == f'PlatformPage(name="{PLATFORM_PAGE_NAME}", url_name="None")'
    )
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, url_name=URL_NAME).__repr__()
        == f'PlatformPage(name="{PLATFORM_PAGE_NAME}", url_name="{URL_NAME}")'
    )
    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME, url_name=URL_NAME, object_class=Case
        ).__repr__()
        == f'PlatformPage(name="{PLATFORM_PAGE_NAME}", url_name="{URL_NAME}", object_class="<class \'accessibility_monitoring_platform.apps.cases.models.Case\'>")'
    )


def test_platform_page_url():
    """Test PlatformPage.url"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).url is None
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, url_name="cases:case-list").url
        == "/cases/"
    )

    case: Case = Case(id=1)

    assert (
        PlatformPage(
            name="Case metadata",
            url_name="cases:edit-case-metadata",
            object_class=Case,
            object=case,
        ).url
        == "/cases/1/edit-case-metadata/"
    )


def test_platform_page_url_missing_object():
    """Test PlatformPage.url returns empty string when a required object is missing"""
    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME, url_name=URL_NAME, object_required=True
        ).url
        == ""
    )


def test_platform_page_show():
    """Test PlatformPage.show"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).show is True
    assert PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case).show is False

    case: Case = Case(organisation_name="Show flag")

    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME,
            object_class=Case,
            object=case,
            show_flag_name="organisation_name",
        ).show
        == "Show flag"
    )


def test_platform_page_complete():
    """Test PlatformPage.complete"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).complete is None

    case: Case = Case(organisation_name="complete flag")

    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME,
            object_class=Case,
            object=case,
            complete_flag_name="organisation_name",
        ).complete
        == "complete flag"
    )


def test_platform_page_populate_subpage_objects():
    """
    Test PlatformPage.populate_subpage_objects() populates subpages with objects
    """
    case: Case = Case()

    platform_page: PlatformPage = PlatformPage(
        name=PLATFORM_PAGE_NAME,
        object=case,
        object_class=Case,
        subpages=[
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case),
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case),
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Audit),
        ],
    )

    platform_page.populate_subpage_objects()

    assert len(platform_page.subpages) == 3
    assert platform_page.subpages[0].object == case
    assert platform_page.subpages[1].object == case
    assert platform_page.subpages[2].object is None


def test_platform_page_populate_from_case():
    """
    Test PlatformPage.populate_from_case() populates subpages with objects
    """
    case: Case = Case()

    platform_page: PlatformPage = PlatformPage(
        name=PLATFORM_PAGE_NAME,
        object=case,
        object_class=Case,
        subpages=[
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case),
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Case),
            PlatformPage(name=PLATFORM_PAGE_NAME, object_class=Audit),
        ],
    )

    platform_page.populate_from_case(case=case)

    assert len(platform_page.subpages) == 3
    assert platform_page.subpages[0].object == case
    assert platform_page.subpages[1].object == case
    assert platform_page.subpages[2].object is None


@pytest.mark.django_db
def test_populate_from_request(rf):
    """Test PlatformPage.populate_from_request sets the object"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case, name="Contact name")

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("cases:edit-contact-update", kwargs={"pk": contact.id}),
    )
    request.user = request_user

    platform_page: PlatformPage = PlatformPage(
        name="Edit contact {object}",
        url_name="cases:edit-contact-update",
        object_required=True,
        object_class=Contact,
    )

    platform_page.populate_from_request(request=request)

    assert platform_page.object == contact
    assert platform_page.get_name() == "Edit contact Contact name"
    assert platform_page.url == f"/cases/contacts/{contact.id}/edit-contact-update/"


def test_platform_page_get_name():
    """Test PlatformPage.get_name()"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).get_name() == PLATFORM_PAGE_NAME

    case: Case = Case(organisation_name=ORGANISATION_NAME)

    assert (
        PlatformPage(
            name="{object.organisation_name}",
            object=case,
        ).get_name()
        == ORGANISATION_NAME
    )


def test_platform_page_get_case():
    """Test PlatformPage.get_case()"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).get_case() == None

    case: Case = Case()

    assert PlatformPage(name=PLATFORM_PAGE_NAME, object=case).get_case() == case

    audit: Audit = Audit(case=case)

    assert PlatformPage(name=PLATFORM_PAGE_NAME, object=audit).get_case() == case
    page: Page = Page(audit=audit)

    assert PlatformPage(name=PLATFORM_PAGE_NAME, object=page).get_case() == case

    retest: Retest = Retest(case=case)
    retest_page: RetestPage = RetestPage(retest=retest)

    assert PlatformPage(name=PLATFORM_PAGE_NAME, object=retest_page).get_case() == case


def test_home_platform_page():
    """Test HomePlatformPage sets name based on GET parameters"""
    home_platform_page: HomePlatformPage = HomePlatformPage(name=PLATFORM_PAGE_NAME)

    mock_request: MockRequest = MockRequest()

    home_platform_page.populate_from_request(request=mock_request)

    assert home_platform_page.get_name() == "Your cases"

    mock_request: MockRequest = MockRequest({"view": "View all cases"})

    home_platform_page.populate_from_request(request=mock_request)

    assert home_platform_page.get_name() == "All cases"

    mock_request: MockRequest = MockRequest({"view": "View your cases"})

    home_platform_page.populate_from_request(request=mock_request)

    assert home_platform_page.get_name() == "Your cases"


@pytest.mark.django_db
def test_get_current_platform_page_for_case(rf):
    """Test get_current_platform_page returns expected Case-specific page"""
    case: Case = Case.objects.create()

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("cases:edit-case-metadata", kwargs={"pk": case.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == "Case metadata"
    assert current_platform_page.url_name == "cases:edit-case-metadata"


@pytest.mark.django_db
def test_get_current_platform_page_for_page(rf):
    """Test get_current_platform_page returns expected Page-specific page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == "Additional page test"
    assert current_platform_page.url_name == "audits:edit-audit-page-checks"


@pytest.mark.django_db
def test_get_current_platform_page_for_retest_page(rf):
    """Test get_current_platform_page returns expected RetestPage-specific page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    retest: Retest = Retest.objects.create(case=case)
    retest_page: RetestPage = RetestPage.objects.create(retest=retest, page=page)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-retest-page-checks", kwargs={"pk": retest_page.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == "Retest #1 | Additional"
    assert current_platform_page.url_name == "audits:edit-retest-page-checks"


@pytest.mark.django_db
def test_get_current_platform_page_for_email_template(rf):
    """Test get_current_platform_page returns expected EmailTemplate-specific name"""
    case: Case = Case.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.create(
        name=EMAIL_TEMPLATE_NAME
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse(
            "cases:email-template-preview",
            kwargs={"pk": email_template.id, "case_id": case.id},
        ),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == EMAIL_TEMPLATE_NAME
    assert current_platform_page.url_name == "cases:email-template-preview"


@pytest.mark.django_db
def test_get_current_platform_page_with_extra_context(rf):
    """Test get_current_platform_page returns expected name with extra context"""
    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("exports:export-list"),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == "EHRC CSV export manager"
    assert current_platform_page.url_name == "exports:export-list"

    request = rf.get(
        f'{reverse("exports:export-list")}?enforcement_body=ecni',
    )

    current_platform_page: PlatformPage = get_current_platform_page(request)

    assert current_platform_page.get_name() == "ECNI CSV export manager"
    assert current_platform_page.url_name == "exports:export-list"
