"""Module with all page names to be placed in context"""

import copy
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Type, Union

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import Resolver404, URLResolver, resolve, reverse

from ..audits.models import Audit, Page, Retest, RetestPage
from ..cases.models import Case, Contact
from ..exports.models import Export
from ..notifications.models import Task
from ..reports.models import Report
from .models import EmailTemplate


class PlatformPage:
    name: str
    url_name: Optional[str] = None
    url_kwarg_key: Optional[str] = None
    object_class: Optional[Union[Type[Audit], Type[Case], Type[Retest]]] = None
    object: Optional[Union[Audit, Case]] = None
    object_required_for_url: bool = False
    complete_flag_name: Optional[str] = None
    show_flag_name: Optional[str] = None
    visible_only_when_current: bool = False
    subpages: Optional[List["PlatformPage"]] = None

    def __init__(
        self,
        name: str,
        url_name: Optional[str] = None,
        url_kwarg_key: Optional[str] = None,
        object_class: Optional[Union[Type[Audit], Type[Case], Type[Retest]]] = None,
        object: Optional[Union[Audit, Case, Page]] = None,
        object_required_for_url: bool = False,
        complete_flag_name: Optional[str] = None,
        show_flag_name: Optional[str] = None,
        subpages: Optional[List["PlatformPage"]] = None,
    ):
        self.name = name
        self.url_name = url_name
        if url_kwarg_key is None and object_class is not None:
            self.url_kwarg_key = "pk"
        else:
            self.url_kwarg_key = url_kwarg_key
        self.object_class = object_class
        self.object = object
        self.object_required_for_url = object_required_for_url
        self.complete_flag_name = complete_flag_name
        self.show_flag_name = show_flag_name
        self.subpages = subpages

    def __repr__(self):
        repr: str = f'PlatformPage(name="{self.name}", url_name="{self.url_name}"'
        if self.object_class is not None:
            repr += f', object_class="{self.object_class}")'
        else:
            repr += ")"
        return repr

    @property
    def url(self) -> Optional[str]:
        if self.url_name is None:
            return None
        if self.object is not None and self.url_kwarg_key is not None:
            return reverse(self.url_name, kwargs={self.url_kwarg_key: self.object.id})
        if self.object_required_for_url and self.object is None:
            print(f"No object for {self} ({self.url_name})")
            return ""
        return reverse(self.url_name)

    @property
    def show(self):
        if self.object is not None and self.show_flag_name is not None:
            return getattr(self.object, self.show_flag_name)
        if self.object_class is not None and self.object is None:
            return False
        return True

    @property
    def complete(self):
        if self.object is not None and self.complete_flag_name is not None:
            return getattr(self.object, self.complete_flag_name)

    def populate_subpage_objects(self):
        if self.object is not None:
            if self.subpages is not None:
                for subpage in self.subpages:
                    if (
                        subpage.object is None
                        and subpage.object_class == self.object_class
                    ):
                        subpage.object = self.object
                        subpage.populate_subpage_objects()
                # subpage_instances: List[PlatformPage] = []
                # for subpage in self.subpages:
                #     new_subpage: PlatformPage = copy.copy(subpage)
                #     if (
                #         new_subpage.object is None
                #         and new_subpage.object_class == self.object_class
                #     ):
                #         new_subpage.object = self.object
                #         new_subpage.populate_subpage_objects()
                #         subpage_instances.append(new_subpage)
                # self.subpages = subpage_instances

    def populate_from_case(self, case: Case):
        self.populate_subpage_objects()

    def populate_from_request(self, request: HttpRequest):
        """Set page object from request"""
        if self.object_class is not None:
            url_resolver: URLResolver = resolve(request.path_info)
            if self.url_kwarg_key in url_resolver.captured_kwargs:
                self.object = self.object_class.objects.get(
                    id=url_resolver.captured_kwargs[self.url_kwarg_key]
                )
                self.populate_subpage_objects()

    def get_name(self) -> str:
        if self.object is None:
            return self.name
        return self.name.format(object=self.object)

    def get_case(self) -> Optional[Case]:
        if self.object is not None:
            if isinstance(self.object, Case):
                return self.object
            if hasattr(self.object, "case"):
                return self.object.case
            if hasattr(self.object, "audit"):
                return self.object.audit.case
            if hasattr(self.object, "retest"):
                return self.object.retest.case


class HomePlatformPage(PlatformPage):
    def populate_from_request(self, request: HttpRequest):
        """Set get name from parameters"""
        view_param: str = request.GET.get("view", "View your cases")
        self.name: str = "All cases" if view_param == "View all cases" else "Your cases"


class ExportPlatformPage(PlatformPage):
    def populate_from_request(self, request: HttpRequest):
        """Set name from parameters"""
        enforcement_body_param: str = request.GET.get("enforcement_body", "ehrc")
        self.enforcement_body = enforcement_body_param.upper()

    def get_name(self) -> str:
        if not hasattr(self, "enforcement_body") or self.enforcement_body is None:
            return self.name
        return self.name.format(enforcement_body=self.enforcement_body)


class CasePlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: Type[Case] = Case
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case
        super().populate_from_case(case=case)


class CaseContactsPlatformPage(CasePlatformPage):
    def populate_from_case(self, case: Case):
        if case is not None:
            self.object = case
            self.subpages = [
                CasePlatformPage(
                    name="Add contact",
                    url_name="cases:edit-contact-create",
                    url_kwarg_key="case_id",
                    object_required_for_url=True,
                ),
            ] + [
                PlatformPage(
                    name="Edit contact {object}",
                    url_name="cases:edit-contact-update",
                    url_kwarg_key="pk",
                    object=contact,
                    object_required_for_url=True,
                    object_class=Contact,
                )
                for contact in case.contacts
            ]
        super().populate_from_case(case=case)


class AuditPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: Type[Audit] = Audit
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case.audit
        super().populate_from_case(case=case)


class AuditPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: Case):
        if case.audit is not None:
            self.object = case.audit
            self.subpages = [
                PlatformPage(
                    name="{object.page_title} test",
                    url_name="audits:edit-audit-page-checks",
                    url_kwarg_key="pk",
                    object=page,
                    object_required_for_url=True,
                    object_class=Page,
                    complete_flag_name="complete_date",
                )
                for page in case.audit.testable_pages
            ]
        super().populate_from_case(case=case)


class ReportPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: Type[Report] = Report
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case.report
        super().populate_from_case(case=case)


class AuditRetestPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: Case):
        if case.audit is not None:
            self.object = case.audit
            self.subpages = [
                PlatformPage(
                    name="Retesting {object.page_title}",
                    url_name="audits:edit-audit-retest-page-checks",
                    url_kwarg_key="pk",
                    object=page,
                    object_required_for_url=True,
                    object_class=Page,
                    complete_flag_name="retest_complete_date",
                )
                for page in case.audit.testable_pages
            ]
        super().populate_from_case(case=case)


class EqualityBodyRetestPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: Type[Retest] = Retest
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"


class RetestOverviewPlatformPage(CasePlatformPage):
    def populate_from_case(self, case: Case):
        self.object = case
        if self.url_name and self.url_name in sitemap_by_url_name:
            self.subpages = copy.deepcopy(
                sitemap_by_url_name.get(self.url_name).subpages
            )
        if self.subpages is not None:
            subpage_instances: List[PlatformPage] = []
            for retest in case.retests:
                if retest.id_within_case > 0:
                    for subpage in self.subpages:
                        if subpage.object_class == Retest:
                            new_subpage: PlatformPage = copy.copy(subpage)
                            new_subpage.object = retest
                            new_subpage.populate_subpage_objects()
                            subpage_instances.append(new_subpage)
            self.subpages = subpage_instances
        super().populate_from_case(case=case)


class EqualityBodyRetestPagesPlatformPage(EqualityBodyRetestPlatformPage):
    def populate_subpage_objects(self):
        if self.subpages is not None and self.object is not None:
            subpage_instances: List[PlatformPage] = []
            for retest_page in self.object.retestpage_set.all():
                for subpage in self.subpages:
                    if subpage.object_class == RetestPage:
                        new_subpage: PlatformPage = copy.copy(subpage)
                        new_subpage.object = retest_page
                        subpage_instances.append(new_subpage)
            self.subpages = subpage_instances


# Page group types
CASE_NAV: str = "case-nav"
FUTURE_CASE_NAV: str = "future-case-nav"
PREVIOUS_CASE_NAV: str = "previous-case-nav"
DEFAULT: str = ""


@dataclass
class PlatformPageGroup:
    name: str
    type: Literal[DEFAULT, CASE_NAV, FUTURE_CASE_NAV, PREVIOUS_CASE_NAV] = DEFAULT
    show_flag_name: Optional[str] = None
    pages: Optional[List[PlatformPage]] = None

    @property
    def show(self):
        return True

    def populate_from_case(self, case: Case):
        for page in self.pages:
            page.populate_from_case(case=case)

    def number_pages_and_subpages(self) -> int:
        if self.pages is not None:
            count: int = len(self.pages)
            for page in self.pages:
                if page.subpages is not None:
                    count += len(
                        [
                            page
                            for page in page.subpages
                            if page.visible_only_when_current is False
                        ]
                    )
            return count
        return 0

    def number_complete(self) -> int:
        if self.pages is not None:
            count: int = 0
            for page in self.pages:
                if page.complete:
                    count += 1
                if page.subpages is not None:
                    count += len(
                        [subpage for subpage in page.subpages if subpage.complete]
                    )
            return count
        return 0


class CasePlatformPageGroup(PlatformPageGroup):
    def __init__(self, type=CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: Literal[DEFAULT, CASE_NAV, FUTURE_CASE_NAV, PREVIOUS_CASE_NAV] = type
        self.case: Optional[Case] = None

    @property
    def show(self):
        if self.case is not None and self.show_flag_name is not None:
            return getattr(self.case, self.show_flag_name)
        return True

    def populate_from_case(self, case: Case):
        self.case = case
        super().populate_from_case(case=case)


SITE_MAP: List[PlatformPageGroup] = [
    CasePlatformPageGroup(
        name="Case details",
        pages=[
            CasePlatformPage(
                name="Case metadata",
                url_name="cases:edit-case-metadata",
                complete_flag_name="case_details_complete_date",
            )
        ],
    ),
    CasePlatformPageGroup(
        name="",
        show_flag_name="no_audit",
        pages=[
            CasePlatformPage(
                name="Testing details",
                url_name="cases:edit-test-results",
            ),
            # AuditPlatformPage(name="View test", url_name="audits:audit-detail"),
        ],
    ),
    CasePlatformPageGroup(
        name="Initial WCAG test",
        show_flag_name="has_audit",
        pages=[
            AuditPlatformPage(
                name="Initial test metadata",
                url_name="audits:edit-audit-metadata",
                complete_flag_name="audit_metadata_complete_date",
            ),
            AuditPagesPlatformPage(
                name="Add or remove pages",
                url_name="audits:edit-audit-pages",
                complete_flag_name="audit_pages_complete_date",
                subpages=[
                    PlatformPage(
                        name="{object.page_title} test",
                        url_name="audits:edit-audit-page-checks",
                        url_kwarg_key="pk",
                        object_class=Page,
                        complete_flag_name="complete_date",
                    )
                ],
            ),
            AuditPlatformPage(
                name="Website compliance decision",
                url_name="audits:edit-website-decision",
                complete_flag_name="audit_website_decision_complete_date",
            ),
            AuditPlatformPage(
                name="Test summary",
                url_name="audits:edit-audit-wcag-summary",
                complete_flag_name="audit_wcag_summary_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Initial statement",
        show_flag_name="has_audit",
        pages=[
            AuditPlatformPage(
                name="Initial statement links",
                url_name="audits:edit-statement-pages",
                complete_flag_name="audit_statement_pages_complete_date",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 1",
                url_name="audits:edit-audit-statement-1",
                show_flag_name="uses_old_statement_checks",
                complete_flag_name="archive_audit_statement_1_complete_date",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 2",
                url_name="audits:edit-audit-statement-2",
                show_flag_name="uses_old_statement_checks",
                complete_flag_name="archive_audit_statement_2_complete_date",
            ),
            AuditPlatformPage(
                name="Report options",
                url_name="audits:edit-audit-report-options",
                show_flag_name="uses_old_statement_checks",
                complete_flag_name="archive_audit_report_options_complete_date",
            ),
            AuditPlatformPage(
                name="Statement overview",
                url_name="audits:edit-statement-overview",
                show_flag_name="uses_statement_checks",
                complete_flag_name="audit_statement_overview_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="Statement information",
                        url_name="audits:edit-statement-website",
                        complete_flag_name="audit_statement_website_complete_date",
                    ),
                    AuditPlatformPage(
                        name="Compliance status",
                        url_name="audits:edit-statement-compliance",
                        complete_flag_name="audit_statement_compliance_complete_date",
                    ),
                    AuditPlatformPage(
                        name="Non-accessible content",
                        url_name="audits:edit-statement-non-accessible",
                        complete_flag_name="audit_statement_non_accessible_complete_date",
                    ),
                    AuditPlatformPage(
                        name="Statement preparation",
                        url_name="audits:edit-statement-preparation",
                        complete_flag_name="audit_statement_preparation_complete_date",
                    ),
                    AuditPlatformPage(
                        name="Feedback and enforcement procedure",
                        url_name="audits:edit-statement-feedback",
                        complete_flag_name="audit_statement_feedback_complete_date",
                    ),
                    AuditPlatformPage(
                        name="Custom statement issues",
                        url_name="audits:edit-statement-custom",
                        complete_flag_name="audit_statement_custom_complete_date",
                    ),
                ],
            ),
            AuditPlatformPage(
                name="Initial disproportionate burden claim",
                url_name="audits:edit-initial-disproportionate-burden",
                complete_flag_name="initial_disproportionate_burden_complete_date",
            ),
            AuditPlatformPage(
                name="Initial statement compliance decision",
                url_name="audits:edit-statement-decision",
                complete_flag_name="audit_statement_decision_complete_date",
            ),
            AuditPlatformPage(
                name="Test summary",
                url_name="audits:edit-audit-statement-summary",
                complete_flag_name="audit_statement_summary_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="",
        type=PREVIOUS_CASE_NAV,
        pages=[
            CasePlatformPage(
                name="Report details",
                url_name="cases:edit-report-details",
                complete_flag_name="reporting_details_complete_date",
                subpages=[
                    ReportPlatformPage(
                        name="Report publisher",
                        url_name="reports:report-publisher",
                        object_class=Report,
                    ),
                    ReportPlatformPage(
                        name="Report notes",
                        url_name="reports:edit-report-notes",
                        object_class=Report,
                    ),
                    ReportPlatformPage(
                        name="Publish report",
                        url_name="reports:report-confirm-publish",
                        object_class=Report,
                    ),
                    ReportPlatformPage(
                        name="Report visit logs",
                        url_name="reports:report-metrics-view",
                        object_class=Report,
                    ),
                ],
            ),
            CasePlatformPage(name="QA comments", url_name="cases:edit-qa-comments"),
            CasePlatformPage(
                name="Report approved",
                url_name="cases:edit-report-approved",
                complete_flag_name="qa_auditor_complete_date",
            ),
            CasePlatformPage(
                name="Publish report",
                url_name="cases:edit-publish-report",
                complete_flag_name="publish_report_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Contact details",
        pages=[
            CaseContactsPlatformPage(
                name="Manage contact details",
                url_name="cases:manage-contact-details",
                complete_flag_name="manage_contact_details_complete_date",
                subpages=[
                    CasePlatformPage(
                        name="Add contact",
                        url_name="cases:edit-contact-create",
                        url_kwarg_key="case_id",
                    ),
                    PlatformPage(
                        name="Edit contact {object}",
                        url_name="cases:edit-contact-update",
                        url_kwarg_key="pk",
                        object_required_for_url=True,
                        object_class=Contact,
                    ),
                ],
            ),
            CasePlatformPage(
                name="Request contact details",
                url_name="cases:edit-request-contact-details",
                complete_flag_name="request_contact_details_complete_date",
            ),
            CasePlatformPage(
                name="One-week follow-up",
                url_name="cases:edit-one-week-contact-details",
                complete_flag_name="one_week_contact_details_complete_date",
            ),
            CasePlatformPage(
                name="Four-week follow-up",
                url_name="cases:edit-four-week-contact-details",
                complete_flag_name="four_week_contact_details_complete_date",
            ),
            CasePlatformPage(
                name="Unresponsive PSB",
                url_name="cases:edit-no-psb-response",
                complete_flag_name="no_psb_contact_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Report correspondence",
        pages=[
            CasePlatformPage(
                name="Report sent on",
                url_name="cases:edit-report-sent-on",
                complete_flag_name="report_sent_on_complete_date",
            ),
            CasePlatformPage(
                name="One week follow-up",
                url_name="cases:edit-report-one-week-followup",
                complete_flag_name="one_week_followup_complete_date",
            ),
            CasePlatformPage(
                name="Four week follow-up",
                url_name="cases:edit-report-four-week-followup",
                complete_flag_name="four_week_followup_complete_date",
            ),
            CasePlatformPage(
                name="Report acknowledged",
                url_name="cases:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="12-week correspondence",
        pages=[
            CasePlatformPage(
                name="12-week update requested",
                url_name="cases:edit-12-week-update-requested",
                complete_flag_name="twelve_week_update_requested_complete_date",
            ),
            CasePlatformPage(
                name="One week follow-up for final update",
                url_name="cases:edit-12-week-one-week-followup-final",
                complete_flag_name="one_week_followup_final_complete_date",
            ),
            CasePlatformPage(
                name="12-week update request acknowledged",
                url_name="cases:edit-12-week-update-request-ack",
                complete_flag_name="twelve_week_update_request_ack_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="",
        type=PREVIOUS_CASE_NAV,
        pages=[
            CasePlatformPage(
                name="12-week retest",
                url_name="cases:edit-twelve-week-retest",
                complete_flag_name="twelve_week_retest_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="12-week-retest",
        type=FUTURE_CASE_NAV,
        pages=[
            AuditPlatformPage(
                name="View 12-week retest", url_name="audits:audit-retest-detail"
            ),
            AuditPlatformPage(
                name="12-week retest metadata",
                url_name="audits:edit-audit-retest-metadata",
                complete_flag_name="audit_retest_metadata_complete_date",
            ),
            AuditRetestPagesPlatformPage(
                name="Pages",
                subpages=[
                    PlatformPage(
                        name="Retesting {object.page_title}",
                        url_name="audits:edit-audit-retest-page-checks",
                        url_kwarg_key="pk",
                        object_class=Page,
                        complete_flag_name="retest_complete_date",
                    )
                ],
            ),
            AuditPlatformPage(
                name="12-week pages comparison",
                url_name="audits:edit-audit-retest-pages-comparison",
                complete_flag_name="audit_retest_pages_complete_date",
            ),
            AuditPlatformPage(
                name="12-week pages comparison",
                url_name="audits:edit-audit-retest-pages-comparison-by-wcag",
                complete_flag_name="audit_retest_pages_complete_date",
            ),
            AuditPlatformPage(
                name="12-week website compliance decision",
                url_name="audits:edit-audit-retest-website-decision",
                complete_flag_name="audit_retest_website_decision_complete_date",
            ),
            AuditPlatformPage(
                name="12-week statement links",
                url_name="audits:edit-audit-retest-statement-pages",
                complete_flag_name="audit_retest_statement_pages_complete_date",
            ),
            AuditPlatformPage(
                name="12-week accessibility statement Pt. 1",
                url_name="audits:edit-audit-retest-statement-1",
                complete_flag_name="archive_audit_retest_statement_1_complete_date",
            ),
            AuditPlatformPage(
                name="12-week accessibility statement Pt. 2",
                url_name="audits:edit-audit-retest-statement-2",
                complete_flag_name="archive_audit_retest_statement_2_complete_date",
            ),
            AuditPlatformPage(
                name="12-week statement overview",
                url_name="audits:edit-retest-statement-overview",
                complete_flag_name="audit_retest_statement_overview_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="12-week statement information",
                        url_name="audits:edit-retest-statement-website",
                        complete_flag_name="audit_retest_statement_website_complete_date",
                    ),
                    AuditPlatformPage(
                        name="12-week compliance status",
                        url_name="audits:edit-retest-statement-compliance",
                        complete_flag_name="audit_retest_statement_compliance_complete_date",
                    ),
                    AuditPlatformPage(
                        name="12-week non-accessible content",
                        url_name="audits:edit-retest-statement-non-accessible",
                        complete_flag_name="audit_retest_statement_non_accessible_complete_date",
                    ),
                    AuditPlatformPage(
                        name="12-week statement preparation",
                        url_name="audits:edit-retest-statement-preparation",
                        complete_flag_name="audit_retest_statement_preparation_complete_date",
                    ),
                    AuditPlatformPage(
                        name="12-week feedback and enforcement procedure",
                        url_name="audits:edit-retest-statement-feedback",
                        complete_flag_name="audit_retest_statement_feedback_complete_date",
                    ),
                    AuditPlatformPage(
                        name="12-week custom statement issues",
                        url_name="audits:edit-retest-statement-custom",
                        complete_flag_name="audit_retest_statement_custom_complete_date",
                    ),
                ],
            ),
            AuditPlatformPage(
                name="12-week disproportionate burden claim",
                url_name="audits:edit-twelve-week-disproportionate-burden",
                complete_flag_name="twelve_week_disproportionate_burden_complete_date",
            ),
            AuditPlatformPage(
                name="12-week statement compliance decision",
                url_name="audits:edit-audit-retest-statement-decision",
                complete_flag_name="audit_retest_statement_decision_complete_date",
            ),
            AuditPlatformPage(
                name="12-week accessibility statement comparison",
                url_name="audits:edit-audit-retest-statement-comparison",
                complete_flag_name="audit_retest_statement_comparison_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Closing the case",
        pages=[
            CasePlatformPage(
                name="Reviewing changes",
                url_name="cases:edit-review-changes",
                complete_flag_name="review_changes_complete_date",
            ),
            CasePlatformPage(
                name="Enforcement recommendation",
                url_name="cases:edit-enforcement-recommendation",
                complete_flag_name="enforcement_recommendation_complete_date",
            ),
            CasePlatformPage(
                name="Closing the case",
                url_name="cases:edit-case-close",
                complete_flag_name="case_close_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="",
        type=PREVIOUS_CASE_NAV,
        pages=[
            CasePlatformPage(
                name="Statement enforcement",
                url_name="cases:edit-statement-enforcement",
            ),
            CasePlatformPage(
                name="Equality body metadata",
                url_name="cases:edit-equality-body-metadata",
            ),
            CasePlatformPage(
                name="All equality body correspondence",
                url_name="cases:list-equality-body-correspondence",
            ),
            RetestOverviewPlatformPage(
                name="Retest overview",
                url_name="cases:edit-retest-overview",
                subpages=[
                    EqualityBodyRetestPlatformPage(
                        name="Retest #{object.id_within_case}",
                        subpages=[
                            EqualityBodyRetestPlatformPage(
                                name="Retest metadata",
                                url_name="audits:retest-metadata-update",
                                complete_flag_name="complete_date",
                            ),
                            EqualityBodyRetestPagesPlatformPage(
                                name="Pages",
                                subpages=[
                                    PlatformPage(
                                        name="{object.retest} | {object}",
                                        url_name="audits:edit-retest-page-checks",
                                        object_class=RetestPage,
                                        complete_flag_name="complete_date",
                                    )
                                ],
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Comparison",
                                url_name="audits:retest-comparison-update",
                                complete_flag_name="comparison_complete_date",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Compliance decision",
                                url_name="audits:retest-compliance-update",
                                complete_flag_name="compliance_complete_date",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement links",
                                url_name="audits:edit-equality-body-statement-pages",
                                complete_flag_name="statement_pages_complete_date",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement overview",
                                url_name="audits:edit-equality-body-statement-overview",
                                complete_flag_name="statement_overview_complete_date",
                                subpages=[
                                    EqualityBodyRetestPlatformPage(
                                        name="Statement information",
                                        url_name="audits:edit-equality-body-statement-website",
                                        complete_flag_name="statement_website_complete_date",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Compliance status",
                                        url_name="audits:edit-equality-body-statement-compliance",
                                        complete_flag_name="statement_compliance_complete_date",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Non-accessible content",
                                        url_name="audits:edit-equality-body-statement-non-accessible",
                                        complete_flag_name="statement_non_accessible_complete_date",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Statement preparation",
                                        url_name="audits:edit-equality-body-statement-preparation",
                                        complete_flag_name="statement_preparation_complete_date",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Feedback and enforcement procedure",
                                        url_name="audits:edit-equality-body-statement-feedback",
                                        complete_flag_name="statement_feedback_complete_date",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Custom statement issues",
                                        url_name="audits:edit-equality-body-statement-custom",
                                        complete_flag_name="statement_custom_complete_date",
                                    ),
                                ],
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement results",
                                url_name="audits:edit-equality-body-statement-results",
                                complete_flag_name="statement_results_complete_date",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Disproportionate burden",
                                url_name="audits:edit-equality-body-disproportionate-burden",
                                complete_flag_name="disproportionate_burden_complete_date",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement decision",
                                url_name="audits:edit-equality-body-statement-decision",
                                complete_flag_name="statement_decision_complete_date",
                            ),
                        ],
                    )
                ],
            ),
            CasePlatformPage(
                name="Legacy end of case data",
                url_name="cases:legacy-end-of-case",
                show_flag_name="archive",
            ),
        ],
    ),
    # Misc Case
    PlatformPageGroup(
        name="",
        pages=[
            CasePlatformPage(name="View case", url_name="cases:case-detail"),
            CasePlatformPage(name="Reminder", url_name="notifications:reminder-create"),
            CasePlatformPage(
                name="Add Zendesk ticket",
                url_name="cases:create-equality-body-correspondence",
            ),
            CasePlatformPage(
                name="Add PSB Zendesk ticket", url_name="cases:create-zendesk-ticket"
            ),
            CasePlatformPage(name="Deactivate case", url_name="cases:deactivate-case"),
            CasePlatformPage(
                name="Edit Zendesk ticket",
                url_name="cases:edit-equality-body-correspondence",
            ),
            CasePlatformPage(name="Post case summary", url_name="cases:edit-post-case"),
            CasePlatformPage(
                name="Email templates", url_name="cases:email-template-list"
            ),
            PlatformPage(
                name="{object.name}",
                url_name="cases:email-template-preview",
                object_class=EmailTemplate,
            ),
            CasePlatformPage(
                name="Outstanding issues", url_name="cases:outstanding-issues"
            ),
            CasePlatformPage(name="Reactivate case", url_name="cases:reactivate-case"),
            CasePlatformPage(
                name="Cannot start new retest", url_name="cases:retest-create-error"
            ),
            CasePlatformPage(name="Status workflow", url_name="cases:status-workflow"),
            CasePlatformPage(
                name="Edit PSB Zendesk ticket", url_name="cases:update-zendesk-ticket"
            ),
            PlatformPage(name="PSB Zendesk tickets", url_name="cases:zendesk-tickets"),
            PlatformPage(
                name="Edit or delete comment",
                url_name="comments:edit-qa-comment",
                object_required_for_url=True,
            ),
        ],
    ),
    # Exports
    PlatformPageGroup(
        name="",
        pages=[
            ExportPlatformPage(
                name="{enforcement_body} CSV export manager",
                url_name="exports:export-list",
            ),
            PlatformPage(
                name="Delete {object}",
                url_name="exports:export-confirm-delete",
                object_required_for_url=True,
                object_class=Export,
            ),
            PlatformPage(
                name="Confirm {object}",
                url_name="exports:export-confirm-export",
                object_required_for_url=True,
                object_class=Export,
            ),
            ExportPlatformPage(
                name="New {enforcement_body} CSV export",
                url_name="exports:export-create",
            ),
            PlatformPage(
                name="{object}",
                url_name="exports:export-detail",
                object_required_for_url=True,
                object_class=Export,
            ),
        ],
    ),
    # Settings
    PlatformPageGroup(
        name="",
        pages=[
            PlatformPage(name="Case metrics", url_name="common:metrics-case"),
            PlatformPage(name="Policy metrics", url_name="common:metrics-policy"),
            PlatformPage(name="Report metrics", url_name="common:metrics-report"),
            PlatformPage(
                name="Account details", url_name="users:edit-user", object_class=User
            ),
            PlatformPage(
                name="Active QA auditor", url_name="common:edit-active-qa-auditor"
            ),
            PlatformPage(
                name="Platform version history", url_name="common:platform-history"
            ),
            PlatformPage(
                name="Markdown cheatsheet", url_name="common:markdown-cheatsheet"
            ),
            PlatformPage(
                name="Edit frequently used links",
                url_name="common:edit-frequently-used-links",
            ),
            PlatformPage(name="Edit footer links", url_name="common:edit-footer-links"),
            PlatformPage(
                name="Report viewer editor",
                url_name="reports:edit-report-wrapper",
                object_class=Report,
            ),
            PlatformPage(
                name="WCAG errors editor",
                url_name="audits:wcag-definition-list",
                subpages=[
                    PlatformPage(
                        name="Create WCAG error",
                        url_name="audits:wcag-definition-create",
                        object_required_for_url=True,
                    ),
                    PlatformPage(
                        name="Update WCAG definition",
                        url_name="audits:wcag-definition-update",
                        object_required_for_url=True,
                    ),
                ],
            ),
            PlatformPage(
                name="Statement issues editor",
                url_name="audits:statement-check-list",
                subpages=[
                    PlatformPage(
                        name="Create statement issue",
                        url_name="audits:statement-check-create",
                    ),
                    PlatformPage(
                        name="Update statement issue",
                        url_name="audits:statement-check-update",
                        object_required_for_url=True,
                    ),
                ],
            ),
            PlatformPage(
                name="Email template manager",
                url_name="common:email-template-list",
                subpages=[
                    PlatformPage(
                        name="{object.name} preview",
                        url_name="common:email-template-preview",
                        object_required_for_url=True,
                        object_class=EmailTemplate,
                    ),
                    PlatformPage(
                        name="Create email template",
                        url_name="common:email-template-create",
                    ),
                    PlatformPage(
                        name="Email template editor",
                        url_name="common:email-template-update",
                        object_required_for_url=True,
                        object_class=EmailTemplate,
                    ),
                ],
            ),
            PlatformPage(name="Bulk URL search", url_name="common:bulk-url-search"),
        ],
    ),
    # Non-case
    PlatformPageGroup(
        name="",
        pages=[
            PlatformPage(name="Create case", url_name="cases:case-create"),
            PlatformPage(name="Search", url_name="cases:case-list"),
            PlatformPage(
                name="Accessibility statement",
                url_name="common:accessibility-statement",
            ),
            PlatformPage(name="Report an issue", url_name="common:issue-report"),
            PlatformPage(name="Contact admin", url_name="common:contact-admin"),
            HomePlatformPage(name="Your cases", url_name="dashboard:home"),
            PlatformPage(name="Tasks", url_name="notifications:task-list"),
            PlatformPage(
                name="Reminder",
                url_name="notifications:edit-reminder-task",
                object_required_for_url=True,
                object_class=Task,
            ),
            PlatformPage(name="Privacy notice", url_name="common:privacy-notice"),
            PlatformPage(
                name="More information about monitoring",
                url_name="common:more-information",
            ),
            PlatformPage(name="Platform checking", url_name="common:platform-checking"),
            PlatformPage(name="Issue reports", url_name="common:issue-reports-list"),
        ],
    ),
]

sitemap_by_url_name: Dict[str, PlatformPage] = {}


def add_pages(pages: List[PlatformPage]):
    """Iterate through pages list adding to sitemap dictionary"""
    for page in pages:
        if page.url_name:
            if page.url_name in sitemap_by_url_name:
                print(f"Duplicate page url_name found for {page.url_name} ({page})")
            else:
                sitemap_by_url_name[page.url_name] = page
        if page.subpages is not None:
            add_pages(pages=page.subpages)


site_map: List[PlatformPageGroup] = copy.copy(SITE_MAP)
for platform_page_group in site_map:
    if platform_page_group.pages is not None:
        add_pages(pages=platform_page_group.pages)


def get_current_platform_page(request: HttpRequest) -> PlatformPage:
    """Return the current platform page"""
    url_resolver: URLResolver = resolve(request.path_info)
    url_name: str = url_resolver.view_name
    platform_page: PlatformPage = sitemap_by_url_name.get(
        url_name, PlatformPage(name=f"Page not found for {url_name}", url_name=url_name)
    )
    platform_page.populate_from_request(request=request)
    return platform_page


def build_sitemap_for_request(request: HttpRequest) -> List[PlatformPageGroup]:
    """Populate the sitemap based on the current request url"""
    current_platform_page: PlatformPage = get_current_platform_page(request=request)
    case: Optional[Case] = current_platform_page.get_case()
    site_map = copy.deepcopy(SITE_MAP)
    if case is not None:
        case_navigation: List[PlatformPageGroup] = [
            platform_page_group
            for platform_page_group in site_map
            if platform_page_group.type == CASE_NAV
            or platform_page_group.type == PREVIOUS_CASE_NAV
        ]
        for platform_page_group in case_navigation:
            platform_page_group.populate_from_case(case=case)
        return case_navigation
    return SITE_MAP


def get_platform_page_name_by_url(url: str) -> str:
    """Lookup and return the name of the page the url points to"""
    try:
        url_resolver: URLResolver = resolve(url)
        url_name: str = url_resolver.view_name

        if url_name in sitemap_by_url_name:
            platform_page: PlatformPage = sitemap_by_url_name.get(url_name)
            return platform_page.get_name()
        else:
            return f"Page name not found for {url_name}"
    except Resolver404:
        return f"URL not found for {url}"
