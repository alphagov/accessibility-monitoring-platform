"""Module with all page names to be placed in context"""

import copy
import logging
from dataclasses import dataclass
from enum import StrEnum, auto

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpRequest
from django.urls import Resolver404, URLResolver, resolve, reverse

from ..audits.forms import (
    AuditMetadataUpdateForm,
    AuditRetestMetadataUpdateForm,
    InitialDisproportionateBurdenUpdateForm,
    TwelveWeekDisproportionateBurdenUpdateForm,
)
from ..audits.models import Audit, Page, Retest, RetestPage
from ..cases.forms import (
    CaseCloseUpdateForm,
    CaseEnforcementRecommendationUpdateForm,
    CaseEqualityBodyMetadataUpdateForm,
    CaseFourWeekContactDetailsUpdateForm,
    CaseMetadataUpdateForm,
    CaseNoPSBContactUpdateForm,
    CaseOneWeekContactDetailsUpdateForm,
    CaseOneWeekFollowupFinalUpdateForm,
    CaseQAApprovalUpdateForm,
    CaseQAAuditorUpdateForm,
    CaseReportAcknowledgedUpdateForm,
    CaseReportFourWeekFollowupUpdateForm,
    CaseReportOneWeekFollowupUpdateForm,
    CaseReportReadyForQAUpdateForm,
    CaseReportSentOnUpdateForm,
    CaseRequestContactDetailsUpdateForm,
    CaseReviewChangesUpdateForm,
    CaseStatementEnforcementUpdateForm,
    CaseTwelveWeekUpdateAcknowledgedUpdateForm,
    CaseTwelveWeekUpdateRequestedUpdateForm,
    ManageContactDetailsUpdateForm,
)
from ..cases.models import Case, Contact, EqualityBodyCorrespondence, ZendeskTicket
from ..comments.models import Comment
from ..exports.models import Export
from ..notifications.models import Task
from ..reports.models import Report
from .models import EmailTemplate

logger = logging.getLogger(__name__)


class PlatformPage:
    name: str
    platform_page_group_name: str = ""
    url_name: str | None = None
    url_kwarg_key: str | None = None
    object_class: type[models.Model] | None = None
    object: Audit | Case | None = None
    object_required_for_url: bool = False
    complete_flag_name: str | None = None
    show_flag_name: str | None = None
    visible_only_when_current: bool = False
    subpages: list["PlatformPage"] | None = None
    case_details_form_class: type[forms.ModelForm] | None = None
    case_details_template_name: str = ""

    def __init__(
        self,
        name: str,
        platform_page_group_name: str = "",
        url_name: str | None = None,
        url_kwarg_key: str | None = None,
        object_class: type[models.Model] | None = None,
        object: Audit | Case | Page | None = None,
        object_required_for_url: bool = False,
        complete_flag_name: str | None = None,
        show_flag_name: str | None = None,
        visible_only_when_current: bool = False,
        subpages: list["PlatformPage"] | None = None,
        case_details_form_class: type[forms.ModelForm] | None = None,
        case_details_template_name: str = "",
    ):
        self.name = name
        self.platform_page_group_name = platform_page_group_name
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
        self.visible_only_when_current = visible_only_when_current
        self.subpages = subpages
        self.case_details_form_class = case_details_form_class
        self.case_details_template_name = case_details_template_name

    def __repr__(self):
        repr: str = f'PlatformPage(name="{self.name}", url_name="{self.url_name}"'
        if self.object_class is not None:
            repr += f', object_class="{self.object_class}")'
        else:
            repr += ")"
        return repr

    @property
    def url(self) -> str | None:
        if self.url_name is None:
            return None
        if self.name.startswith("Page not found for "):
            return ""
        if self.object is not None and self.url_kwarg_key is not None:
            return reverse(self.url_name, kwargs={self.url_kwarg_key: self.object.id})
        if self.object_required_for_url and self.object is None:
            logger.warning(
                "Expected object missing; Url cannot be calculated %s %s",
                self.url_name,
                self,
            )
            return ""
        return reverse(self.url_name)

    @property
    def show(self):
        if self.object is not None and self.show_flag_name is not None:
            return getattr(self.object, self.show_flag_name)
        return True

    @property
    def complete(self):
        if self.object is not None and self.complete_flag_name is not None:
            return getattr(self.object, self.complete_flag_name)

    def populate_subpage_objects(self):
        if self.object is not None:
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for subpage in self.subpages:
                    subpage_instance: PlatformPage = copy.copy(subpage)
                    if subpage_instance.object_class == self.object_class:
                        subpage_instance.object = self.object
                    subpage_instance.populate_subpage_objects()
                    subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances

    def populate_from_case(self, case: Case):
        if self.subpages is not None:
            for subpage in self.subpages:
                subpage.populate_from_case(case=case)

    def populate_from_url(self, url: str):
        """Set page object from url"""
        if self.object_class is not None:
            url_resolver: URLResolver = resolve(url)
            if self.url_kwarg_key in url_resolver.captured_kwargs:
                self.object = self.object_class.objects.get(
                    id=url_resolver.captured_kwargs[self.url_kwarg_key]
                )
                self.populate_subpage_objects()

    def populate_from_request(self, request: HttpRequest):
        """Set page object from request"""
        self.populate_from_url(url=request.path_info)

    def get_name(self) -> str:
        if self.object is None:
            return self.name
        return self.name.format(object=self.object)

    def get_case(self) -> Case | None:
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
        self.object_class: type[Case] = Case
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case
        super().populate_from_case(case=case)


class CaseContactsPlatformPage(CasePlatformPage):
    def populate_from_case(self, case: Case):
        if case is not None:
            self.object = case
            self.subpages = get_subpages_by_url_name(url_name=self.url_name)
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for subpage in self.subpages:
                    if subpage.object_class == Case:
                        subpage_instance: PlatformPage = copy.copy(subpage)
                        subpage_instance.object = case
                        subpage_instance.populate_subpage_objects()
                        subpage_instances.append(subpage_instance)
                for contact in case.contacts:
                    for subpage in self.subpages:
                        if subpage.object_class == Contact:
                            subpage_instance: PlatformPage = copy.copy(subpage)
                            subpage_instance.object = contact
                            subpage_instance.populate_subpage_objects()
                            subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances


class CaseCommentsPlatformPage(CasePlatformPage):
    def populate_from_case(self, case: Case):
        if case is not None:
            self.object = case
            self.subpages = get_subpages_by_url_name(url_name=self.url_name)
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for comment in case.qa_comments:
                    for subpage in self.subpages:
                        if subpage.object_class == Comment:
                            subpage_instance: PlatformPage = copy.copy(subpage)
                            subpage_instance.object = comment
                            subpage_instance.populate_subpage_objects()
                            subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances


class AuditPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: type[Audit] = Audit
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case.audit
        super().populate_from_case(case=case)


class AuditPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: Case):
        if case.audit is not None:
            self.object = case.audit
            self.subpages = get_subpages_by_url_name(url_name=self.url_name)
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for page in case.audit.testable_pages:
                    for subpage in self.subpages:
                        if subpage.object_class == Page:
                            subpage_instance: PlatformPage = copy.copy(subpage)
                            subpage_instance.object = page
                            subpage_instance.populate_subpage_objects()
                            subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances


class ReportPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: type[Report] = Report
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: Case):
        self.object = case.report
        super().populate_from_case(case=case)


class CaseEmailTemplatePreviewPlatformPage(PlatformPage):
    case: Case | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: type[EmailTemplate] = EmailTemplate
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    @property
    def url(self) -> str | None:
        if self.case is None or self.object is None:
            return ""
        return reverse(
            self.url_name,
            kwargs={"case_id": self.case.id, self.url_kwarg_key: self.object.id},
        )

    def populate_from_case(self, case: Case):
        self.case = case
        super().populate_from_case(case=case)


class AuditRetestPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: Case):
        if case.audit is not None:
            self.object = case.audit
            self.subpages = get_subpages_by_url_name(url_name=self.url_name)
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for page in case.audit.testable_pages:
                    for subpage in self.subpages:
                        if subpage.object_class == Page:
                            subpage_instance: PlatformPage = copy.copy(subpage)
                            subpage_instance.object = page
                            subpage_instance.populate_subpage_objects()
                            subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances


class EqualityBodyRetestPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object_required_for_url = True
        self.object_class: type[Retest] = Retest
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"


class RetestOverviewPlatformPage(CasePlatformPage):
    def populate_from_case(self, case: Case):
        self.object = case
        self.subpages = get_subpages_by_url_name(url_name=self.url_name)
        if self.subpages is not None:
            subpage_instances: list[PlatformPage] = []
            for retest in case.retests:
                if retest.id_within_case > 0:
                    for subpage in self.subpages:
                        if subpage.object_class == Retest:
                            subpage_instance: PlatformPage = copy.copy(subpage)
                            subpage_instance.object = retest
                            subpage_instance.populate_subpage_objects()
                            subpage_instances.append(subpage_instance)
            self.subpages = subpage_instances


class EqualityBodyRetestPagesPlatformPage(EqualityBodyRetestPlatformPage):
    def populate_subpage_objects(self):
        if self.subpages is not None and self.object is not None:
            subpage_instances: list[PlatformPage] = []
            for retest_page in self.object.retestpage_set.all():
                for subpage in self.subpages:
                    if subpage.object_class == RetestPage:
                        subpage_instance: PlatformPage = copy.copy(subpage)
                        subpage_instance.object = retest_page
                        subpage_instances.append(subpage_instance)
            self.subpages = subpage_instances


@dataclass
class PlatformPageGroup:
    class Type(StrEnum):
        CASE_NAV: str = auto()
        FUTURE_CASE_NAV: str = auto()
        PREVIOUS_CASE_NAV: str = auto()
        DEFAULT: str = auto()

    name: str
    type: Type = Type.DEFAULT
    show_flag_name: str | None = None
    pages: list[PlatformPage] | None = None

    @property
    def show(self):
        return True

    def populate_from_case(self, case: Case):
        for page in self.pages:
            page.populate_from_case(case=case)

    def number_pages_and_subpages(self) -> int:
        if self.pages is not None:
            count: int = len(
                [
                    page
                    for page in self.pages
                    if page.show
                    and not page.visible_only_when_current
                    and page.complete_flag_name is not None
                ]
            )
            for page in self.pages:
                if page.subpages is not None:
                    count += len(
                        [
                            page
                            for page in page.subpages
                            if page.show
                            and not page.visible_only_when_current
                            and page.complete_flag_name is not None
                        ]
                    )
            return count
        return 0

    def number_complete(self) -> int:
        if self.pages is not None:
            count: int = 0
            for page in self.pages:
                if (
                    not page.show
                    or page.visible_only_when_current
                    or page.complete_flag_name is None
                ):
                    continue
                if page.complete:
                    count += 1
                if page.subpages is not None:
                    count += len(
                        [
                            subpage
                            for subpage in page.subpages
                            if subpage.complete and subpage.show
                        ]
                    )
            return count
        return 0


class CasePlatformPageGroup(PlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: Case | None = None

    @property
    def show(self):
        if self.case is not None and self.show_flag_name is not None:
            return getattr(self.case, self.show_flag_name)
        return True

    def populate_from_case(self, case: Case):
        self.case = case
        super().populate_from_case(case=case)


SITE_MAP: list[PlatformPageGroup] = [
    CasePlatformPageGroup(
        name="Case details",
        show_flag_name="not_archived",
        pages=[
            CasePlatformPage(
                name="Case metadata",
                url_name="cases:edit-case-metadata",
                complete_flag_name="case_details_complete_date",
                case_details_form_class=CaseMetadataUpdateForm,
                case_details_template_name="cases/details/details_case_metadata.html",
            )
        ],
    ),
    CasePlatformPageGroup(
        name="Initial test",
        show_flag_name="show_start_test",
        pages=[
            CasePlatformPage(
                name="Testing details",
                url_name="cases:edit-test-results",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Initial WCAG test",
        show_flag_name="not_archived_has_audit",
        pages=[
            AuditPlatformPage(
                name="Initial test metadata",
                url_name="audits:edit-audit-metadata",
                complete_flag_name="audit_metadata_complete_date",
                case_details_form_class=AuditMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            AuditPagesPlatformPage(
                name="Add or remove pages",
                url_name="audits:edit-audit-pages",
                complete_flag_name="audit_pages_complete_date",
                subpages=[
                    PlatformPage(
                        name="{object.page_title} test ({object.count_failed_check_results})",
                        url_name="audits:edit-audit-page-checks",
                        url_kwarg_key="pk",
                        object_class=Page,
                        complete_flag_name="complete_date",
                        case_details_template_name="cases/details/details_initial_page_wcag_results.html",
                    )
                ],
                case_details_template_name="cases/details/details_initial_pages.html",
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-website-decision",
                complete_flag_name="audit_website_decision_complete_date",
                case_details_template_name="cases/details/details_initial_website_compliance.html",
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
        show_flag_name="not_archived_has_audit",
        pages=[
            AuditPlatformPage(
                name="Statement links",
                url_name="audits:edit-statement-pages",
                complete_flag_name="audit_statement_pages_complete_date",
                case_details_template_name="cases/details/details_statement_links.html",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 1",
                url_name="audits:edit-audit-statement-1",
                show_flag_name="uses_pre_2023_statement_checks",
                complete_flag_name="archive_audit_statement_1_complete_date",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 2",
                url_name="audits:edit-audit-statement-2",
                show_flag_name="uses_pre_2023_statement_checks",
                complete_flag_name="archive_audit_statement_2_complete_date",
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
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_website.html",
                    ),
                    AuditPlatformPage(
                        name="Compliance status",
                        url_name="audits:edit-statement-compliance",
                        complete_flag_name="audit_statement_compliance_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_compliance.html",
                    ),
                    AuditPlatformPage(
                        name="Non-accessible content",
                        url_name="audits:edit-statement-non-accessible",
                        complete_flag_name="audit_statement_non_accessible_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_non_accessible.html",
                    ),
                    AuditPlatformPage(
                        name="Statement preparation",
                        url_name="audits:edit-statement-preparation",
                        complete_flag_name="audit_statement_preparation_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_preparation.html",
                    ),
                    AuditPlatformPage(
                        name="Feedback and enforcement procedure",
                        url_name="audits:edit-statement-feedback",
                        complete_flag_name="audit_statement_feedback_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_feedback.html",
                    ),
                    AuditPlatformPage(
                        name="Custom statement issues",
                        url_name="audits:edit-statement-custom",
                        complete_flag_name="audit_statement_custom_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_initial_statement_checks_custom.html",
                    ),
                ],
                case_details_template_name="cases/details/details_initial_statement_checks_overview.html",
            ),
            AuditPlatformPage(
                name="Disproportionate burden",
                url_name="audits:edit-initial-disproportionate-burden",
                complete_flag_name="initial_disproportionate_burden_complete_date",
                case_details_form_class=InitialDisproportionateBurdenUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            AuditPlatformPage(
                name="Statement compliance",
                url_name="audits:edit-statement-decision",
                complete_flag_name="audit_statement_decision_complete_date",
                case_details_template_name="cases/details/details_initial_statement_compliance.html",
            ),
            AuditPlatformPage(
                name="Report options",
                url_name="audits:edit-audit-report-options",
                show_flag_name="uses_pre_2023_statement_checks",
                complete_flag_name="archive_audit_report_options_complete_date",
            ),
            AuditPlatformPage(
                name="Test summary",
                url_name="audits:edit-audit-statement-summary",
                complete_flag_name="audit_statement_summary_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Start report",
        show_flag_name="show_create_report",
        pages=[
            CasePlatformPage(
                name="Start report",
                url_name="cases:edit-create-report",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Report QA",
        show_flag_name="not_archived_has_report",
        pages=[
            CasePlatformPage(
                name="Report ready for QA",
                url_name="cases:edit-report-ready-for-qa",
                complete_flag_name="reporting_details_complete_date",
                case_details_form_class=CaseReportReadyForQAUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="QA auditor",
                url_name="cases:edit-qa-auditor",
                complete_flag_name="qa_auditor_complete_date",
                case_details_form_class=CaseQAAuditorUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CaseCommentsPlatformPage(
                name="Comments ({object.qa_comments_count})",
                url_name="cases:edit-qa-comments",
                subpages=[
                    PlatformPage(
                        name="Edit or delete comment",
                        url_name="comments:edit-qa-comment",
                        object_class=Comment,
                        object_required_for_url=True,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="cases/details/details_qa_comments.html",
            ),
            CasePlatformPage(
                name="QA approval",
                url_name="cases:edit-qa-approval",
                complete_flag_name="qa_approval_complete_date",
                case_details_form_class=CaseQAApprovalUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Publish report",
                url_name="cases:edit-publish-report",
                complete_flag_name="publish_report_complete_date",
                subpages=[
                    ReportPlatformPage(
                        name="Republish report",
                        url_name="reports:report-republish",
                        object_class=Report,
                        visible_only_when_current=True,
                    ),
                ],
            ),
        ],
    ),
    # Reports
    PlatformPageGroup(
        name="",
        pages=[
            ReportPlatformPage(
                name="Report preview",
                url_name="reports:report-preview",
                object_class=Report,
            ),
            ReportPlatformPage(
                name="Report visit logs",
                url_name="reports:report-metrics-view",
                object_class=Report,
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Contact details",
        show_flag_name="not_archived",
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
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit contact {object}",
                        url_name="cases:edit-contact-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        object_required_for_url=True,
                        object_class=Contact,
                    ),
                ],
                case_details_form_class=ManageContactDetailsUpdateForm,
                case_details_template_name="cases/details/details_manage_contact_details.html",
            ),
            CasePlatformPage(
                name="Request contact details",
                url_name="cases:edit-request-contact-details",
                complete_flag_name="request_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseRequestContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="One-week follow-up",
                url_name="cases:edit-one-week-contact-details",
                complete_flag_name="one_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseOneWeekContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Four-week follow-up",
                url_name="cases:edit-four-week-contact-details",
                complete_flag_name="four_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseFourWeekContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Unresponsive PSB",
                url_name="cases:edit-no-psb-response",
                complete_flag_name="no_psb_contact_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseNoPSBContactUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Report correspondence",
        show_flag_name="not_archived",
        pages=[
            CasePlatformPage(
                name="Report sent on",
                url_name="cases:edit-report-sent-on",
                complete_flag_name="report_sent_on_complete_date",
                case_details_form_class=CaseReportSentOnUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="One week follow-up",
                url_name="cases:edit-report-one-week-followup",
                complete_flag_name="one_week_followup_complete_date",
                case_details_form_class=CaseReportOneWeekFollowupUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Four week follow-up",
                url_name="cases:edit-report-four-week-followup",
                complete_flag_name="four_week_followup_complete_date",
                case_details_form_class=CaseReportFourWeekFollowupUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Report acknowledged",
                url_name="cases:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                case_details_form_class=CaseReportAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="12-week correspondence",
        show_flag_name="not_archived",
        pages=[
            CasePlatformPage(
                name="12-week update requested",
                url_name="cases:edit-12-week-update-requested",
                complete_flag_name="twelve_week_update_requested_complete_date",
                case_details_form_class=CaseTwelveWeekUpdateRequestedUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="One week follow-up for final update",
                url_name="cases:edit-12-week-one-week-followup-final",
                complete_flag_name="one_week_followup_final_complete_date",
                case_details_form_class=CaseOneWeekFollowupFinalUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="12-week update request acknowledged",
                url_name="cases:edit-12-week-update-request-ack",
                complete_flag_name="twelve_week_update_request_ack_complete_date",
                case_details_form_class=CaseTwelveWeekUpdateAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Start 12-week retest",
        show_flag_name="show_start_12_week_retest",
        pages=[
            CasePlatformPage(
                name="Start 12-week retest",
                url_name="cases:edit-twelve-week-retest",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="12-week WCAG test",
        show_flag_name="show_12_week_retest",
        pages=[
            AuditPlatformPage(
                name="12-week retest metadata",
                url_name="audits:edit-audit-retest-metadata",
                complete_flag_name="audit_retest_metadata_complete_date",
                case_details_form_class=AuditRetestMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            AuditRetestPagesPlatformPage(
                name="Retest pages",
                url_name="audits:edit-audit-retest-pages",
                complete_flag_name="audit_retest_pages_complete_date",
                subpages=[
                    PlatformPage(
                        name="{object.page_title} retest",
                        url_name="audits:edit-audit-retest-page-checks",
                        url_kwarg_key="pk",
                        object_class=Page,
                        complete_flag_name="retest_complete_date",
                        case_details_template_name="cases/details/details_twelve_week_page_wcag_results.html",
                    )
                ],
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-audit-retest-website-decision",
                complete_flag_name="audit_retest_website_decision_complete_date",
                case_details_template_name="cases/details/details_twelve_week_website_compliance.html",
            ),
            AuditPlatformPage(
                name="Test summary",
                url_name="audits:edit-audit-retest-wcag-summary",
                complete_flag_name="audit_retest_wcag_summary_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="12-week statement",
        show_flag_name="show_12_week_retest",
        pages=[
            AuditPlatformPage(
                name="Statement links",
                url_name="audits:edit-audit-retest-statement-pages",
                complete_flag_name="audit_retest_statement_pages_complete_date",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 1",
                url_name="audits:edit-audit-retest-statement-1",
                show_flag_name="uses_pre_2023_statement_checks",
                complete_flag_name="archive_audit_retest_statement_1_complete_date",
            ),
            AuditPlatformPage(
                name="Accessibility statement Pt. 2",
                url_name="audits:edit-audit-retest-statement-2",
                show_flag_name="uses_pre_2023_statement_checks",
                complete_flag_name="archive_audit_retest_statement_2_complete_date",
            ),
            AuditPlatformPage(
                name="Statement overview",
                url_name="audits:edit-retest-statement-overview",
                show_flag_name="uses_statement_checks",
                complete_flag_name="audit_retest_statement_overview_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="Statement information",
                        url_name="audits:edit-retest-statement-website",
                        complete_flag_name="audit_retest_statement_website_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_website.html",
                    ),
                    AuditPlatformPage(
                        name="Compliance status",
                        url_name="audits:edit-retest-statement-compliance",
                        complete_flag_name="audit_retest_statement_compliance_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_compliance.html",
                    ),
                    AuditPlatformPage(
                        name="Non-accessible content",
                        url_name="audits:edit-retest-statement-non-accessible",
                        complete_flag_name="audit_retest_statement_non_accessible_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_non_accessible.html",
                    ),
                    AuditPlatformPage(
                        name="Statement preparation",
                        url_name="audits:edit-retest-statement-preparation",
                        complete_flag_name="audit_retest_statement_preparation_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_preparation.html",
                    ),
                    AuditPlatformPage(
                        name="Feedback and enforcement procedure",
                        url_name="audits:edit-retest-statement-feedback",
                        complete_flag_name="audit_retest_statement_feedback_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_feedback.html",
                    ),
                    AuditPlatformPage(
                        name="Custom issues",
                        url_name="audits:edit-retest-statement-custom",
                        complete_flag_name="audit_retest_statement_custom_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="cases/details/details_twelve_week_statement_checks_custom.html",
                    ),
                ],
                case_details_template_name="cases/details/details_twelve_week_statement_checks_overview.html",
            ),
            AuditPlatformPage(
                name="Disproportionate burden",
                url_name="audits:edit-twelve-week-disproportionate-burden",
                complete_flag_name="twelve_week_disproportionate_burden_complete_date",
                case_details_form_class=TwelveWeekDisproportionateBurdenUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-audit-retest-statement-decision",
                complete_flag_name="audit_retest_statement_decision_complete_date",
                case_details_template_name="cases/details/details_twelve_week_statement_compliance.html",
            ),
            AuditPlatformPage(
                name="Test summary",
                url_name="audits:edit-audit-retest-statement-summary",
                complete_flag_name="audit_retest_statement_summary_complete_date",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Closing the case",
        show_flag_name="not_archived",
        pages=[
            CasePlatformPage(
                name="Reviewing changes",
                url_name="cases:edit-review-changes",
                complete_flag_name="review_changes_complete_date",
                case_details_form_class=CaseReviewChangesUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Recommendation",
                url_name="cases:edit-enforcement-recommendation",
                complete_flag_name="enforcement_recommendation_complete_date",
                case_details_form_class=CaseEnforcementRecommendationUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Closing the case",
                url_name="cases:edit-case-close",
                complete_flag_name="case_close_complete_date",
                case_details_form_class=CaseCloseUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
        ],
    ),
    CasePlatformPageGroup(
        name="Post case",
        type=PlatformPageGroup.Type.PREVIOUS_CASE_NAV,
        pages=[
            CasePlatformPage(
                name="Statement enforcement",
                url_name="cases:edit-statement-enforcement",
                case_details_form_class=CaseStatementEnforcementUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Equality body metadata",
                url_name="cases:edit-equality-body-metadata",
                case_details_form_class=CaseEqualityBodyMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            CasePlatformPage(
                name="Equality body correspondence",
                url_name="cases:list-equality-body-correspondence",
                subpages=[
                    CasePlatformPage(
                        name="Add Zendesk ticket",
                        url_name="cases:create-equality-body-correspondence",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit Zendesk ticket",
                        url_name="cases:edit-equality-body-correspondence",
                        object_class=EqualityBodyCorrespondence,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="cases/details/details_equality_body_correspondence.html",
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
                case_details_template_name="cases/details/details_retest_overview.html",
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
            CasePlatformPage(
                name="Reminder",
                url_name="notifications:reminder-create",
                url_kwarg_key="case_id",
            ),
            CasePlatformPage(name="Deactivate case", url_name="cases:deactivate-case"),
            CasePlatformPage(name="Post case summary", url_name="cases:edit-post-case"),
            CasePlatformPage(
                name="Email templates", url_name="cases:email-template-list"
            ),
            CaseEmailTemplatePreviewPlatformPage(
                name="{object.name}",
                url_name="cases:email-template-preview",
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
                name="PSB Zendesk tickets",
                url_name="cases:zendesk-tickets",
                subpages=[
                    CasePlatformPage(
                        name="Add PSB Zendesk ticket",
                        url_name="cases:create-zendesk-ticket",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit PSB Zendesk ticket",
                        url_name="cases:update-zendesk-ticket",
                        object_class=ZendeskTicket,
                        visible_only_when_current=True,
                    ),
                ],
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

SITEMAP_BY_URL_NAME: dict[str, PlatformPage] = {}


def add_pages(pages: list[PlatformPage], platform_page_group: PlatformPageGroup):
    """Iterate through pages list adding to sitemap dictionary"""
    for page in pages:
        page.platform_page_group_name: str = platform_page_group.name
        if page.url_name:
            if page.url_name in SITEMAP_BY_URL_NAME:
                logger.warning(
                    "Duplicate page url_name found %s %s", page.url_name, page
                )
            else:
                SITEMAP_BY_URL_NAME[page.url_name] = page
        if page.subpages is not None:
            add_pages(pages=page.subpages, platform_page_group=platform_page_group)


logger.info("Initialise SITEMAP_BY_URL_NAME")
site_map: list[PlatformPageGroup] = copy.copy(SITE_MAP)
for platform_page_group in site_map:
    if platform_page_group.pages is not None:
        add_pages(
            pages=platform_page_group.pages, platform_page_group=platform_page_group
        )


def get_subpages_by_url_name(url_name: str | None) -> list[PlatformPage]:
    if url_name and url_name in SITEMAP_BY_URL_NAME:
        subpages: list[PlatformPage] = copy.deepcopy(
            SITEMAP_BY_URL_NAME.get(url_name).subpages
        )
        return subpages


def get_requested_platform_page(request: HttpRequest) -> PlatformPage:
    """Return the current platform page"""
    url_resolver: URLResolver = resolve(request.path_info)
    url_name: str = url_resolver.view_name
    platform_page: PlatformPage = SITEMAP_BY_URL_NAME.get(
        url_name, PlatformPage(name=f"Page not found for {url_name}", url_name=url_name)
    )
    platform_page.populate_from_request(request=request)
    return platform_page


def build_sitemap_for_current_page(
    current_platform_page: PlatformPage,
) -> list[PlatformPageGroup]:
    """
    Populate the sitemap based on the current page.
    Return the case navigation subset of the sitemap if the current
    page is case-related, otherwise return the entire sitemap.
    """
    case: Case | None = current_platform_page.get_case()
    if case is not None:
        site_map = copy.deepcopy(SITE_MAP)
        case_navigation: list[PlatformPageGroup] = [
            platform_page_group
            for platform_page_group in site_map
            if platform_page_group.type == PlatformPageGroup.Type.CASE_NAV
            or platform_page_group.type == PlatformPageGroup.Type.PREVIOUS_CASE_NAV
        ]
        for platform_page_group in case_navigation:
            platform_page_group.populate_from_case(case=case)
        return case_navigation
    return SITE_MAP


class Sitemap:
    platform_page_groups: list[PlatformPageGroup]
    current_platform_page: PlatformPage

    def __init__(self, request: HttpRequest):
        self.current_platform_page = get_requested_platform_page(request=request)
        self.platform_page_groups = build_sitemap_for_current_page(
            current_platform_page=self.current_platform_page
        )


def get_platform_page_name_by_url(url: str) -> str:
    """Lookup and return the name of the page the url points to"""
    try:
        url_resolver: URLResolver = resolve(url)
        url_name: str = url_resolver.view_name

        if url_name in SITEMAP_BY_URL_NAME:
            platform_page: PlatformPage = SITEMAP_BY_URL_NAME.get(url_name)
            platform_page.populate_from_url(url=url)
            return platform_page.get_name()
        else:
            return f"Page name not found for {url_name}"
    except Resolver404:
        return f"URL not found for {url}"
