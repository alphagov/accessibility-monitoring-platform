"""Test sitemap"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestPage,
    WcagDefinition,
)
from ...cases.models import BaseCase
from ...comments.models import Comment
from ...common.models import EmailTemplate
from ...detailed.models import DetailedCase
from ...exports.models import Export
from ...mobile.models import MobileCase
from ...notifications.models import Task
from ...reports.models import Report
from ...simplified.models import (
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    ZendeskTicket,
)
from ..sitemap import (
    SITE_MAP,
    SITEMAP_BY_URL_NAME,
    AuditPagesPlatformPage,
    AuditPlatformPage,
    AuditRetestPagesPlatformPage,
    BaseCaseCommentsPlatformPage,
    CaseContactsPlatformPage,
    DetailedCasePlatformPage,
    DetailedCasePlatformPageGroup,
    EqualityBodyRetestPagesPlatformPage,
    EqualityBodyRetestPlatformPage,
    ExportPlatformPage,
    MobileCasePlatformPage,
    MobileCasePlatformPageGroup,
    PlatformPage,
    PlatformPageGroup,
    ReportPlatformPage,
    RetestOverviewPlatformPage,
    SimplifiedCasePlatformPage,
    SimplifiedCasePlatformPageGroup,
    Sitemap,
    build_sitemap_by_url_name,
    build_sitemap_for_current_page,
    get_platform_page_by_url_name,
    get_requested_platform_page,
    populate_subpages_with_instance,
)

PLATFORM_PAGE_NAME: str = "Platform page name"
URL_NAME: str = "url-name"
ORGANISATION_NAME: str = "Organisation name"
EMAIL_TEMPLATE_NAME: str = "4. 12-week update request"
EMAIL_TEMPLATE_TEMPLATE_NAME: str = "4-12-week-update-request"
FIRST_SEPTEMBER_2024 = date(2024, 9, 1)


class MockRequest:
    def __init__(self, get_params=None):
        if get_params is None:
            self.GET = {}
        else:
            self.GET = get_params


class MockInstance:
    complete_flag: bool = False


def test_platform_page_url_kwarg_key():
    """
    Test PlatformPage url_kwarg_key defaults to "pk" if an instance_class is set
    """
    assert PlatformPage(name=PLATFORM_PAGE_NAME).url_kwarg_key is None
    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME, instance_class=SimplifiedCase
        ).url_kwarg_key
        == "pk"
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
            name=PLATFORM_PAGE_NAME, url_name=URL_NAME, instance_class=SimplifiedCase
        ).__repr__()
        == f'PlatformPage(name="{PLATFORM_PAGE_NAME}", url_name="{URL_NAME}", instance_class="<class \'accessibility_monitoring_platform.apps.simplified.models.SimplifiedCase\'>")'
    )


def test_platform_page_url():
    """Test PlatformPage.url"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).url is None
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, url_name="cases:case-list").url
        == "/cases/"
    )

    simplified_case: SimplifiedCase = SimplifiedCase(id=1)

    assert (
        PlatformPage(
            name="Case metadata",
            url_name="simplified:edit-case-metadata",
            instance_class=SimplifiedCase,
            instance=simplified_case,
        ).url
        == "/simplified/1/edit-case-metadata/"
    )


def test_platform_page_url_missing_instance():
    """Test PlatformPage.url returns empty string when a required instance is missing"""
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, url_name=URL_NAME, url_kwarg_key="pk").url
        == ""
    )


def test_platform_page_show():
    """Test PlatformPage.show"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).show is True
    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, instance_class=SimplifiedCase).show
        is False
    )

    simplified_case: SimplifiedCase = SimplifiedCase(organisation_name="Show flag")

    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME,
            instance_class=SimplifiedCase,
            instance=simplified_case,
        ).show
        is True
    )
    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME,
            instance_class=SimplifiedCase,
            instance=simplified_case,
            show_flag_name="organisation_name",
        ).show
        == "Show flag"
    )


def test_platform_page_complete():
    """Test PlatformPage.complete"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).complete is None

    simplified_case: SimplifiedCase = SimplifiedCase(organisation_name="complete flag")

    assert (
        PlatformPage(
            name=PLATFORM_PAGE_NAME,
            instance_class=SimplifiedCase,
            instance=simplified_case,
            complete_flag_name="organisation_name",
        ).complete
        == "complete flag"
    )


def test_platform_page_populate_subpage_instances():
    """
    Test PlatformPage.populate_subpage_instances() populates subpages with instances
    """
    simplified_case: SimplifiedCase = SimplifiedCase()

    platform_page: PlatformPage = PlatformPage(
        name=PLATFORM_PAGE_NAME,
        instance=simplified_case,
        instance_class=SimplifiedCase,
        subpages=[
            PlatformPage(name=PLATFORM_PAGE_NAME, instance_class=SimplifiedCase),
            PlatformPage(name=PLATFORM_PAGE_NAME, instance_class=SimplifiedCase),
            PlatformPage(name=PLATFORM_PAGE_NAME, instance_class=Audit),
        ],
    )

    platform_page.populate_subpage_instances()

    assert len(platform_page.subpages) == 3
    assert platform_page.subpages[0].instance == simplified_case
    assert platform_page.subpages[1].instance == simplified_case
    assert platform_page.subpages[2].instance is None


def test_platform_page_populate_from_case():
    """
    Test PlatformPage.populate_from_case() populates subpages with instances
    """
    simplified_case: SimplifiedCase = SimplifiedCase()

    platform_page: PlatformPage = PlatformPage(
        name=PLATFORM_PAGE_NAME,
        instance=simplified_case,
        instance_class=SimplifiedCase,
        subpages=[
            SimplifiedCasePlatformPage(name=PLATFORM_PAGE_NAME),
            SimplifiedCasePlatformPage(name=PLATFORM_PAGE_NAME),
            AuditPlatformPage(name=PLATFORM_PAGE_NAME),
        ],
    )

    platform_page.populate_from_case(case=simplified_case)

    assert len(platform_page.subpages) == 3
    assert platform_page.subpages[0].instance == simplified_case
    assert platform_page.subpages[1].instance == simplified_case
    assert platform_page.subpages[2].instance is None


@pytest.mark.django_db
def test_populate_from_request(rf):
    """Test PlatformPage.populate_from_request sets the instance"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(
        simplified_case=simplified_case, name="Contact name"
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("simplified:edit-contact-update", kwargs={"pk": contact.id}),
    )
    request.user = request_user

    platform_page: PlatformPage = PlatformPage(
        name="Edit contact {instance}",
        url_name="simplified:edit-contact-update",
        url_kwarg_key="pk",
        instance_class=Contact,
    )

    platform_page.populate_from_request(request=request)

    assert platform_page.instance == contact
    assert platform_page.get_name() == "Edit contact Contact name"
    assert (
        platform_page.url == f"/simplified/contacts/{contact.id}/edit-contact-update/"
    )


def test_platform_page_get_name():
    """Test PlatformPage.get_name()"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).get_name() == PLATFORM_PAGE_NAME

    simplified_case: SimplifiedCase = SimplifiedCase(
        organisation_name=ORGANISATION_NAME
    )

    assert (
        PlatformPage(
            name="{instance.organisation_name}",
            instance=simplified_case,
        ).get_name()
        == ORGANISATION_NAME
    )


@pytest.mark.django_db
def test_platform_page_get_case():
    """Test PlatformPage.get_case()"""
    assert PlatformPage(name=PLATFORM_PAGE_NAME).get_case() is None

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, instance=simplified_case).get_case()
        == simplified_case
    )

    audit: Audit = Audit(simplified_case=simplified_case)

    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, instance=audit).get_case()
        == simplified_case
    )
    page: Page = Page(audit=audit)

    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, instance=page).get_case()
        == simplified_case
    )

    retest: Retest = Retest(simplified_case=simplified_case)
    retest_page: RetestPage = RetestPage(retest=retest)

    assert (
        PlatformPage(name=PLATFORM_PAGE_NAME, instance=retest_page).get_case()
        == simplified_case
    )


def test_export_platform_page():
    """Test ExportPlatformPage sets name based on GET parameters"""
    export_platform_page: ExportPlatformPage = ExportPlatformPage(
        name="{enforcement_body} CSV export manager"
    )

    mock_request: MockRequest = MockRequest()

    export_platform_page.populate_from_request(request=mock_request)

    assert export_platform_page.get_name() == "EHRC CSV export manager"

    mock_request: MockRequest = MockRequest({"enforcement_body": "ecni"})

    export_platform_page.populate_from_request(request=mock_request)

    assert export_platform_page.get_name() == "ECNI CSV export manager"

    mock_request: MockRequest = MockRequest({"enforcement_body": "ehrc"})

    export_platform_page.populate_from_request(request=mock_request)

    assert export_platform_page.get_name() == "EHRC CSV export manager"


def test_simplified_case_platform_page():
    """Test SimplifiedCasePlatformPage"""
    simplified_case_platform_page: SimplifiedCasePlatformPage = (
        SimplifiedCasePlatformPage(name=PLATFORM_PAGE_NAME)
    )

    assert simplified_case_platform_page.instance_class == SimplifiedCase
    assert simplified_case_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase()

    simplified_case_platform_page.populate_from_case(case=simplified_case)

    assert simplified_case_platform_page.instance == simplified_case


def test_detailed_case_platform_page():
    """Test DetailedCasePlatformPage"""
    detailed_case_platform_page: DetailedCasePlatformPage = DetailedCasePlatformPage(
        name=PLATFORM_PAGE_NAME
    )

    assert detailed_case_platform_page.instance_class == DetailedCase
    assert detailed_case_platform_page.url_kwarg_key == "pk"

    detailed_case: DetailedCase = DetailedCase()

    detailed_case_platform_page.populate_from_case(case=detailed_case)

    assert detailed_case_platform_page.instance == detailed_case


def test_mobile_case_platform_page():
    """Test MobileCasePlatformPage"""
    mobile_case_platform_page: MobileCasePlatformPage = MobileCasePlatformPage(
        name=PLATFORM_PAGE_NAME
    )

    assert mobile_case_platform_page.instance_class == MobileCase
    assert mobile_case_platform_page.url_kwarg_key == "pk"

    mobile_case: MobileCase = MobileCase()

    mobile_case_platform_page.populate_from_case(case=mobile_case)

    assert mobile_case_platform_page.instance == mobile_case


@pytest.mark.django_db
def test_case_comments_platform_page():
    """Test CaseCommentsPlatformPage"""
    case_comments_platform_page: BaseCaseCommentsPlatformPage = (
        get_platform_page_by_url_name(url_name="simplified:edit-qa-comments")
    )

    assert isinstance(case_comments_platform_page, BaseCaseCommentsPlatformPage)
    assert case_comments_platform_page.instance_class == BaseCase
    assert case_comments_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    Comment.objects.create(base_case=simplified_case, user=user, body="Comment One")
    Comment.objects.create(base_case=simplified_case, user=user, body="Comment Two")

    case_comments_platform_page.populate_from_case(case=simplified_case)

    assert case_comments_platform_page.instance == simplified_case
    assert len(case_comments_platform_page.subpages) == 2
    assert (
        case_comments_platform_page.subpages[0].get_name() == "Edit or delete comment"
    )
    assert (
        case_comments_platform_page.subpages[1].get_name() == "Edit or delete comment"
    )


@pytest.mark.django_db
def test_case_contacts_platform_page():
    """Test CaseContactsPlatformPage"""
    case_contacts_platform_page: CaseContactsPlatformPage = (
        get_platform_page_by_url_name(url_name="simplified:manage-contact-details")
    )

    assert isinstance(case_contacts_platform_page, CaseContactsPlatformPage)
    assert case_contacts_platform_page.instance_class == SimplifiedCase
    assert case_contacts_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Contact.objects.create(simplified_case=simplified_case, name="Contact One")
    Contact.objects.create(simplified_case=simplified_case, name="Contact Two")

    case_contacts_platform_page.populate_from_case(case=simplified_case)

    assert case_contacts_platform_page.instance == simplified_case
    assert len(case_contacts_platform_page.subpages) == 3
    assert case_contacts_platform_page.subpages[0].get_name() == "Add contact"
    assert (
        case_contacts_platform_page.subpages[1].get_name() == "Edit contact Contact Two"
    )
    assert (
        case_contacts_platform_page.subpages[2].get_name() == "Edit contact Contact One"
    )


@pytest.mark.django_db
def test_audit_platform_page():
    """Test AuditPlatformPage"""
    audit_platform_page: AuditPlatformPage = AuditPlatformPage(name=PLATFORM_PAGE_NAME)

    assert audit_platform_page.instance_class == Audit
    assert audit_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    audit_platform_page.populate_from_case(case=simplified_case)

    assert audit_platform_page.instance == audit


@pytest.mark.django_db
def test_audit_pages_platform_page():
    """Test AuditPagesPlatformPage"""
    audit_pages_platform_page: AuditPagesPlatformPage = get_platform_page_by_url_name(
        url_name="audits:edit-audit-pages",
    )

    assert isinstance(audit_pages_platform_page, AuditPagesPlatformPage)
    assert audit_pages_platform_page.instance_class == Audit
    assert audit_pages_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    Page.objects.create(audit=audit, name="Page one", url="url")
    Page.objects.create(audit=audit, name="Page two", url="url")

    audit_pages_platform_page.populate_from_case(case=simplified_case)

    assert audit_pages_platform_page.instance == audit
    assert len(audit_pages_platform_page.subpages) == 2
    assert audit_pages_platform_page.subpages[0].get_name() == "Page one page test"
    assert audit_pages_platform_page.subpages[1].get_name() == "Page two page test"


@pytest.mark.django_db
def test_report_platform_page():
    """Test ReportPlatformPage"""
    report_platform_page: ReportPlatformPage = ReportPlatformPage(
        name=PLATFORM_PAGE_NAME
    )

    assert report_platform_page.instance_class == Report
    assert report_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    report: Report = Report.objects.create(base_case=simplified_case)

    report_platform_page.populate_from_case(case=simplified_case)

    assert report_platform_page.instance == report


@pytest.mark.django_db
def test_audit_retest_pages_platform_page():
    """Test AuditRetestPagesPlatformPage"""
    audit_retest_pages_platform_page: AuditRetestPagesPlatformPage = (
        get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-pages",
        )
    )

    assert isinstance(audit_retest_pages_platform_page, AuditRetestPagesPlatformPage)
    assert audit_retest_pages_platform_page.instance_class == Audit
    assert audit_retest_pages_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page_1: Page = Page.objects.create(audit=audit, name="Page one", url="url")
    page_2: Page = Page.objects.create(audit=audit, name="Page two", url="url")
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_1,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page_2,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )

    audit_retest_pages_platform_page.populate_from_case(case=simplified_case)

    assert audit_retest_pages_platform_page.instance == audit
    assert len(audit_retest_pages_platform_page.subpages) == 2
    assert (
        audit_retest_pages_platform_page.subpages[0].get_name()
        == "Page one page retest"
    )
    assert (
        audit_retest_pages_platform_page.subpages[1].get_name()
        == "Page two page retest"
    )


def test_equality_body_retest_platform_page():
    """Test EqualityBodyRetestPlatformPage"""
    equality_body_retest_platform_page: EqualityBodyRetestPlatformPage = (
        EqualityBodyRetestPlatformPage(name=PLATFORM_PAGE_NAME)
    )

    assert equality_body_retest_platform_page.instance_class == Retest
    assert equality_body_retest_platform_page.url_kwarg_key == "pk"


@pytest.mark.django_db
def test_retest_overview_platform_page():
    """Test RetestOverviewPlatformPage"""
    retest_overview_platform_page: RetestOverviewPlatformPage = (
        get_platform_page_by_url_name(
            url_name="simplified:edit-retest-overview",
        )
    )

    assert isinstance(retest_overview_platform_page, RetestOverviewPlatformPage)
    assert retest_overview_platform_page.instance_class == SimplifiedCase
    assert retest_overview_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Retest.objects.create(simplified_case=simplified_case, id_within_case=0)
    Retest.objects.create(simplified_case=simplified_case, id_within_case=1)
    Retest.objects.create(simplified_case=simplified_case, id_within_case=2)

    retest_overview_platform_page.populate_from_case(case=simplified_case)

    assert retest_overview_platform_page.instance == simplified_case
    assert len(retest_overview_platform_page.subpages) == 2
    assert retest_overview_platform_page.subpages[0].get_name() == "Retest #2"
    assert retest_overview_platform_page.subpages[1].get_name() == "Retest #1"


@pytest.mark.django_db
def test_equality_body_retest_pages_platform_page():
    """Test EqualityBodyRetestPagesPlatformPage"""
    equality_body_retest_pages_platform_page: EqualityBodyRetestPagesPlatformPage = (
        EqualityBodyRetestPagesPlatformPage(
            name="Pages",
            subpages=[
                PlatformPage(
                    name="{instance.retest} | {instance}",
                    url_name="audits:edit-retest-page-checks",
                    instance_class=RetestPage,
                    complete_flag_name="complete_date",
                )
            ],
        )
    )

    assert equality_body_retest_pages_platform_page.instance_class == Retest
    assert equality_body_retest_pages_platform_page.url_kwarg_key == "pk"

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit, name="Test Page")
    retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=1
    )
    RetestPage.objects.create(retest=retest, page=page)
    RetestPage.objects.create(retest=retest, page=page)

    equality_body_retest_pages_platform_page.instance = retest
    equality_body_retest_pages_platform_page.populate_subpage_instances()

    assert len(equality_body_retest_pages_platform_page.subpages) == 2
    assert (
        equality_body_retest_pages_platform_page.subpages[0].get_name()
        == f"{retest} | {page}"
    )
    assert (
        equality_body_retest_pages_platform_page.subpages[1].get_name()
        == f"{retest} | {page}"
    )


@pytest.mark.django_db
def test_retest_overview_platform_page_populates_subpages():
    """Test RetestOverviewPlatformPage populates subpages from case"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page_1: Page = Page.objects.create(audit=audit, name="Test page one")
    page_2: Page = Page.objects.create(audit=audit, name="Test page two")
    retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=1
    )
    RetestPage.objects.create(retest=retest, page=page_1)
    RetestPage.objects.create(retest=retest, page=page_2)

    retest_overview_platform_page: RetestOverviewPlatformPage = (
        get_platform_page_by_url_name(
            url_name="simplified:edit-retest-overview",
        )
    )
    retest_overview_platform_page.populate_from_case(case=simplified_case)

    assert isinstance(retest_overview_platform_page, RetestOverviewPlatformPage)
    assert retest_overview_platform_page.instance == simplified_case
    assert len(retest_overview_platform_page.subpages) == 1
    assert retest_overview_platform_page.subpages[0].get_name() == "Retest #1"

    retest_1: PlatformPage = retest_overview_platform_page.subpages[0]

    assert len(retest_1.subpages) > 2
    assert retest_1.subpages[1].get_name() == "Pages"

    retest_1_pages: PlatformPage = retest_1.subpages[1]

    assert len(retest_1_pages.subpages) == 2
    assert retest_1_pages.subpages[0].get_name() == f"{retest} | {page_1}"
    assert retest_1_pages.subpages[1].get_name() == f"{retest} | {page_2}"


@pytest.mark.django_db
def test_get_requested_platform_page_for_case(rf):
    """Test get_requested_platform_page returns expected SimplifiedCase-specific page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("simplified:edit-case-metadata", kwargs={"pk": simplified_case.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == "Case metadata"
    assert current_platform_page.url_name == "simplified:edit-case-metadata"


@pytest.mark.django_db
def test_get_requested_platform_page_for_page(rf):
    """Test get_requested_platform_page returns expected Page-specific page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-audit-page-checks", kwargs={"pk": page.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == "Additional page test"
    assert current_platform_page.url_name == "audits:edit-audit-page-checks"


@pytest.mark.django_db
def test_get_requested_platform_page_for_retest_page(rf):
    """Test get_requested_platform_page returns expected RetestPage-specific page"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit)
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    retest_page: RetestPage = RetestPage.objects.create(retest=retest, page=page)

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("audits:edit-retest-page-checks", kwargs={"pk": retest_page.id}),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == "Retest #1 | Additional"
    assert current_platform_page.url_name == "audits:edit-retest-page-checks"


@pytest.mark.django_db
def test_get_requested_platform_page_for_email_template(rf):
    """Test get_requested_platform_page returns expected EmailTemplate-specific name"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    email_template: EmailTemplate = EmailTemplate.objects.create(
        name=EMAIL_TEMPLATE_NAME, template_name=EMAIL_TEMPLATE_TEMPLATE_NAME
    )

    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse(
            "simplified:email-template-preview",
            kwargs={"pk": email_template.id, "case_id": simplified_case.id},
        ),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == EMAIL_TEMPLATE_NAME
    assert current_platform_page.url_name == "simplified:email-template-preview"


@pytest.mark.django_db
def test_get_requested_platform_page_with_extra_context(rf):
    """Test get_requested_platform_page returns expected name with extra context"""
    request_user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    request = rf.get(
        reverse("exports:export-list"),
    )
    request.user = request_user

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == "EHRC CSV export manager"
    assert current_platform_page.url_name == "exports:export-list"

    request = rf.get(
        f'{reverse("exports:export-list")}?enforcement_body=ecni',
    )

    current_platform_page: PlatformPage = get_requested_platform_page(request)

    assert current_platform_page.get_name() == "ECNI CSV export manager"
    assert current_platform_page.url_name == "exports:export-list"


def test_sitemap_by_url_name():
    """Test SITEMAP_BY_URL_NAME has been built correctly"""
    assert isinstance(SITEMAP_BY_URL_NAME, dict) is True

    assert "simplified:edit-case-metadata" in SITEMAP_BY_URL_NAME
    assert (
        SITEMAP_BY_URL_NAME["simplified:edit-case-metadata"].get_name()
        == "Case metadata"
    )


def test_build_sitemap_by_url_name():
    """Test build_sitemap_by_url_name turns list into dictionary"""
    platform_page_1: PlatformPage = PlatformPage(
        name="First page",
        url_name="test:page-one",
    )
    platform_page_2: PlatformPage = PlatformPage(
        name="Second page",
        url_name="test:page-two",
    )
    site_map: list[PlatformPageGroup] = [
        PlatformPageGroup(
            name="Group name",
            pages=[platform_page_1, platform_page_2],
        ),
    ]

    assert build_sitemap_by_url_name(site_map=site_map) == {
        "test:page-one": platform_page_1,
        "test:page-two": platform_page_2,
    }


def test_build_sitemap_for_non_case_current_page():
    """Test build_sitemap_for_current_page when current page is not SimplifiedCase-related"""
    platform_page: PlatformPage = PlatformPage(
        name="Test", url_name="common:platform-checking"
    )
    platform_page_groups: list[PlatformPageGroup] = build_sitemap_for_current_page(
        current_platform_page=platform_page
    )

    assert platform_page_groups == SITE_MAP


@pytest.mark.django_db
def test_build_sitemap_for_case_related_current_page():
    """Test build_sitemap_for_current_page when current page is SimplifiedCase-related"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    platform_page: PlatformPage = get_platform_page_by_url_name(
        url_name="simplified:edit-case-metadata", instance=simplified_case
    )
    platform_page_groups: list[PlatformPageGroup] = build_sitemap_for_current_page(
        current_platform_page=platform_page
    )

    assert len(platform_page_groups) < len(SITE_MAP)
    assert len(platform_page_groups) > 0

    platform_page_group: PlatformPageGroup = platform_page_groups[0]

    assert platform_page_group.pages is not None
    assert len(platform_page_group.pages) > 0

    platform_page: PlatformPage = platform_page_group.pages[0]

    assert platform_page.get_case() == simplified_case


def test_non_case_sitemap(rf):
    """Test non-SimplifiedCase sitemap creation"""
    request: HttpRequest = rf.get("/")
    sitemap: Sitemap = Sitemap(request=request)

    assert sitemap.current_platform_page is not None
    assert sitemap.platform_page_groups is not None

    assert sitemap.current_platform_page.get_case() is None
    assert len(sitemap.platform_page_groups) == len(SITE_MAP)


@pytest.mark.django_db
def test_case_sitemap(rf):
    """Test SimplifiedCase-specific sitemap creation"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    request: HttpRequest = rf.get("/simplified/1/view/")
    sitemap: Sitemap = Sitemap(request=request)

    assert sitemap.current_platform_page is not None
    assert sitemap.platform_page_groups is not None

    assert sitemap.current_platform_page.get_case() == simplified_case
    assert len(sitemap.platform_page_groups) < len(SITE_MAP)


@pytest.mark.parametrize(
    "url, expected_page_name",
    [
        ("/", "Dashboard"),
        ("/simplified/1/edit-case-metadata/", "Case metadata"),
        ("/audits/1/edit-audit-metadata/", "Initial test metadata"),
        ("/audits/pages/1/edit-audit-page-checks/", "Pagename page test"),
        (
            "/simplified/contacts/1/edit-contact-update/",
            "Edit contact Contact Name a.b@example.com",
        ),
        ("/audits/retests/1/retest-metadata-update/", "Retest #1 | Retest metadata"),
        ("/audits/retest-pages/1/retest-page-checks/", "Retest #1 | Pagename"),
        ("/notifications/cases/1/reminder-task-create/", "Reminder"),
        ("/notifications/1/edit-reminder-task/", "Reminder"),
        ("/simplified/1/edit-equality-body-correspondence/", "Edit Zendesk ticket"),
        ("/simplified/1/update-zendesk-ticket/", "Edit PSB Zendesk ticket"),
        ("/comments/1/edit-qa-comment-simplified/", "Edit or delete comment"),
        ("/comments/1/edit-qa-comment-detailed/", "Edit or delete comment"),
        ("/comments/1/edit-qa-comment-mobile/", "Edit or delete comment"),
        ("/exports/export-create/?enforcement_body=ecni", "New ECNI CSV export"),
        ("/exports/1/export-detail/", "EHRC CSV export 1 September 2024"),
        ("/user/1/edit-user/", "Account details"),
        ("/common/edit-active-qa-auditor/", "Active QA auditor"),
        ("/audits/1/edit-wcag-definition/", "Update WCAG definition"),
        ("/audits/1/edit-statement-check/", "Update statement issue"),
    ],
)
def test_page_name(url, expected_page_name, admin_client):
    """
    Test that the page renders and its name is as expected.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    page: Page = Page.objects.create(audit=audit, name="Pagename")
    Report.objects.create(base_case=simplified_case)
    Contact.objects.create(
        simplified_case=simplified_case, name="Contact Name", email="a.b@example.com"
    )
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    RetestPage.objects.create(retest=retest, page=page)
    user: User = User.objects.create()
    Task.objects.create(base_case=simplified_case, date=FIRST_SEPTEMBER_2024, user=user)
    EqualityBodyCorrespondence.objects.create(simplified_case=simplified_case)
    ZendeskTicket.objects.create(simplified_case=simplified_case)
    Comment.objects.create(base_case=simplified_case, user=user)
    Export.objects.create(cutoff_date=FIRST_SEPTEMBER_2024, exporter=user)

    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200

    assertContains(response, expected_page_name)


def test_populate_subpage_instances():
    """Test populate_subpage_instances"""
    simplified_case: SimplifiedCase = SimplifiedCase()
    case_platform_page: PlatformPage = PlatformPage(
        name="Simplified case page",
        url_name="url_name_2",
        instance_class=SimplifiedCase,
    )
    platform_page: PlatformPage = PlatformPage(
        name="Page without instance class",
        url_name="url_name_1",
        subpages=[
            case_platform_page,
            PlatformPage(
                name="Subpage without instance class",
                url_name="url_name_3",
            ),
        ],
    )

    bound_subpages: list[PlatformPage] = populate_subpages_with_instance(
        platform_page=platform_page, instance=simplified_case
    )

    assert len(bound_subpages) == 1
    assert bound_subpages[0].name == case_platform_page.name
    assert bound_subpages[0].instance == simplified_case


def test_simplified_case_platform_page_group():
    """Test SimplifiedCasePlatformPageGroup"""
    simplified_case_platform_page_group: SimplifiedCasePlatformPageGroup = (
        SimplifiedCasePlatformPageGroup(name="Example page group name")
    )

    assert (
        simplified_case_platform_page_group.type
        == PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV
    )

    simplified_case: SimplifiedCase = SimplifiedCase()

    simplified_case_platform_page_group.populate_from_case(case=simplified_case)

    assert simplified_case_platform_page_group.case == simplified_case


def test_detailed_case_platform_page_group():
    """Test DetailedCasePlatformPageGroup"""
    detailed_case_platform_page_group: DetailedCasePlatformPageGroup = (
        DetailedCasePlatformPageGroup(name="Example page group name")
    )

    assert (
        detailed_case_platform_page_group.type
        == PlatformPageGroup.Type.DETAILED_CASE_NAV
    )

    detailed_case: DetailedCase = DetailedCase()

    detailed_case_platform_page_group.populate_from_case(case=detailed_case)

    assert detailed_case_platform_page_group.case == detailed_case


def test_mobile_case_platform_page_group():
    """Test MobileCasePlatformPageGroup"""
    mobile_case_platform_page_group: MobileCasePlatformPageGroup = (
        MobileCasePlatformPageGroup(name="Example page group name")
    )

    assert (
        mobile_case_platform_page_group.type == PlatformPageGroup.Type.MOBILE_CASE_NAV
    )

    mobile_case: MobileCase = MobileCase()

    mobile_case_platform_page_group.populate_from_case(case=mobile_case)

    assert mobile_case_platform_page_group.case == mobile_case


def test_completable_pages_and_subpages():
    """Count number of pages in a group"""
    platform_subpage: PlatformPage = PlatformPage(
        name="Sub page",
        url_name="test:page-two",
        complete_flag_name="complete_flag",
    )
    platform_page: PlatformPage = PlatformPage(
        name="First page",
        url_name="test:page-one",
        complete_flag_name="complete_flag",
        subpages=[platform_subpage],
    )
    platform_page_group: PlatformPageGroup = PlatformPageGroup(
        name="Group name",
        pages=[platform_page],
    )

    assert platform_page_group.completable_pages_and_subpages() == [
        platform_page,
        platform_subpage,
    ]


def test_number_pages_and_subpages():
    """Count number of pages in a group"""
    platform_page: PlatformPage = PlatformPage(
        name="First page",
        url_name="test:page-one",
        complete_flag_name="complete_flag",
        subpages=[
            PlatformPage(
                name="Sub page",
                url_name="test:page-two",
                complete_flag_name="complete_flag",
            )
        ],
    )
    platform_page_group: PlatformPageGroup = PlatformPageGroup(
        name="Group name",
        pages=[platform_page],
    )

    assert platform_page_group.number_pages_and_subpages() == 2


def test_number_complete():
    """Count number of pages in a group marked as complete"""
    mock_instance_1 = MockInstance()
    platform_page_1: PlatformPage = PlatformPage(
        name="First page",
        url_name="test:page-one",
        instance=mock_instance_1,
        complete_flag_name="complete_flag",
    )
    platform_page_2: PlatformPage = PlatformPage(
        name="Second page",
        url_name="test:page-two",
    )
    platform_page_group: PlatformPageGroup = PlatformPageGroup(
        name="Group name",
        pages=[platform_page_1, platform_page_2],
    )

    assert platform_page_group.number_complete() == 0

    mock_instance_1.complete_flag = True

    assert platform_page_group.number_complete() == 1
