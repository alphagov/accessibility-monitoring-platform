"""Module with all page names to be placed in context"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import ClassVar, Optional

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpRequest
from django.urls import URLResolver, resolve, reverse

from ..audits.forms import (
    AuditMetadataUpdateForm,
    AuditRetestMetadataUpdateForm,
    InitialDisproportionateBurdenUpdateForm,
    TwelveWeekDisproportionateBurdenUpdateForm,
)
from ..audits.models import Audit, Page, Retest, RetestPage, StatementCheckResult
from ..cases.models import BaseCase
from ..comments.models import Comment
from ..detailed.forms import DetailedCaseMetadataUpdateForm
from ..detailed.models import Contact as DetailedCaseContact
from ..detailed.models import DetailedCase
from ..exports.models import Export
from ..mobile.forms import MobileCaseMetadataUpdateForm
from ..mobile.models import MobileCase
from ..notifications.models import Task
from ..reports.models import Report
from ..simplified.forms import (
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
from ..simplified.models import (
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    ZendeskTicket,
)
from .models import EmailTemplate

logger = logging.getLogger(__name__)


def populate_subpages_with_instance(
    platform_page: PlatformPage, instance=models.Model
) -> list[PlatformPage]:
    """Set instance on each subpage where instance class matches"""
    subpages: list[PlatformPage] = []
    for subpage in platform_page.subpages:
        if subpage.instance_class is not None and isinstance(
            instance, subpage.instance_class
        ):
            bound_subpage: PlatformPage = copy.copy(subpage)
            bound_subpage.instance = instance
            bound_subpage.populate_subpage_instances()
            subpages.append(bound_subpage)
    return subpages


class Sitemap:
    platform_page_groups: list[PlatformPageGroup]
    current_platform_page: PlatformPage
    next_platform_page: PlatformPage | None

    def __init__(self, request: HttpRequest):
        self.current_platform_page = get_requested_platform_page(request=request)
        self.platform_page_groups = build_sitemap_for_current_page(
            current_platform_page=self.current_platform_page
        )


class PlatformPage:
    name: str
    platform_page_group: Optional["PlatformPageGroup"] = None
    url_name: str | None = None
    url_kwarg_key: str | None = None
    instance_class: type[models.Model] | None = None
    instance: models.Model | None = None
    instance_required_for_url: bool = False
    complete_flag_name: str | None = None
    show_flag_name: str | None = None
    visible_only_when_current: bool = False
    subpages: list[PlatformPage] | None = None
    case_details_form_class: type[forms.ModelForm] | None = None
    case_details_template_name: str = ""
    next_page_url_name: str | None = None
    next_page: PlatformPage | None = None

    def __init__(
        self,
        name: str,
        platform_page_group: Optional["PlatformPageGroup"] = None,
        url_name: str | None = None,
        url_kwarg_key: str | None = None,
        instance_class: type[models.Model] | None = None,
        instance: models.Model | None = None,
        instance_required_for_url: bool = False,
        complete_flag_name: str | None = None,
        show_flag_name: str | None = None,
        visible_only_when_current: bool = False,
        subpages: list["PlatformPage"] | None = None,
        case_details_form_class: type[forms.ModelForm] | None = None,
        case_details_template_name: str = "",
        next_page_url_name: str | None = None,
    ):
        self.name = name
        self.platform_page_group = platform_page_group
        self.url_name = url_name
        if url_kwarg_key is None and instance_class is not None:
            self.url_kwarg_key = "pk"
        else:
            self.url_kwarg_key = url_kwarg_key
        self.instance_class = instance_class
        self.instance = instance
        self.instance_required_for_url = instance_required_for_url
        self.complete_flag_name = complete_flag_name
        self.show_flag_name = show_flag_name
        self.visible_only_when_current = visible_only_when_current
        self.subpages = subpages
        self.case_details_form_class = case_details_form_class
        self.case_details_template_name = case_details_template_name
        self.next_page_url_name = next_page_url_name

    def __repr__(self):
        repr: str = f'PlatformPage(name="{self.name}", url_name="{self.url_name}"'
        if self.instance_class is not None:
            repr += f', instance_class="{self.instance_class}")'
        else:
            repr += ")"
        return repr

    @property
    def url(self) -> str | None:
        if self.url_name is None:
            return None
        if self.name.startswith("Page not found for "):
            return ""
        if self.instance is not None and self.url_kwarg_key is not None:
            return reverse(self.url_name, kwargs={self.url_kwarg_key: self.instance.id})
        if self.instance_required_for_url and self.instance is None:
            logger.warning(
                "Expected instance missing; Url cannot be calculated %s %s",
                self.url_name,
                self,
            )
            return ""
        return reverse(self.url_name)

    @property
    def show(self):
        if self.instance is not None and self.show_flag_name is not None:
            return getattr(self.instance, self.show_flag_name)
        return True

    @property
    def complete(self):
        if self.instance is not None and self.complete_flag_name is not None:
            return getattr(self.instance, self.complete_flag_name)

    def set_instance(self, instance: models.Model | None):
        if self.instance_class is not None and instance is not None:
            if isinstance(instance, self.instance_class):
                self.instance = instance
            else:
                logger.warning("Cannot set instance of %s to %s", self, instance)

    def populate_subpage_instances(self):
        if self.instance is not None:
            if self.subpages is not None:
                subpage_instances: list[PlatformPage] = []
                for subpage in self.subpages:
                    subpage_instance: PlatformPage = copy.copy(subpage)
                    if subpage_instance.instance_class == self.instance_class:
                        subpage_instance.instance = self.instance
                    subpage_instance.populate_subpage_instances()
                    subpage_instances.append(subpage_instance)
                self.subpages = subpage_instances

    def populate_from_case(self, case: SimplifiedCase):
        if self.subpages is not None:
            for subpage in self.subpages:
                subpage.populate_from_case(case=case)

    def populate_from_url(self, url: str):
        """Set page instance from url"""
        if self.instance_class is not None:
            url_resolver: URLResolver = resolve(url)
            if self.url_kwarg_key in url_resolver.captured_kwargs:
                self.instance = self.instance_class.objects.get(
                    id=url_resolver.captured_kwargs[self.url_kwarg_key]
                )
                self.populate_subpage_instances()

    def populate_from_request(self, request: HttpRequest):
        """Set page instance from request"""
        self.populate_from_url(url=request.path_info)

    def get_name(self) -> str:
        if self.instance is None:
            return self.name
        return self.name.format(instance=self.instance)

    def get_case(self) -> SimplifiedCase | None:
        if self.instance is not None:
            if isinstance(self.instance, SimplifiedCase):
                return self.instance
            if hasattr(self.instance, "case"):
                return self.instance.case
            if hasattr(self.instance, "audit"):
                return self.instance.audit.case
            if hasattr(self.instance, "retest"):
                return self.instance.retest.case
            if isinstance(self.instance, DetailedCase):
                return self.instance
            if hasattr(self.instance, "detailed_case"):
                return self.instance.detailed_case


class HomePlatformPage(PlatformPage):
    def populate_from_request(self, request: HttpRequest):
        """Set get name from parameters"""
        view_param: str = request.GET.get("view", "View your cases")
        self.name: str = "All cases" if view_param == "View all cases" else "Your cases"


class ExportPlatformPage(PlatformPage):
    enforcement_body: str = "EHRC"

    def populate_from_request(self, request: HttpRequest):
        """Set name from parameters"""
        enforcement_body_param: str = request.GET.get("enforcement_body", "ehrc")
        self.enforcement_body = enforcement_body_param.upper()

    def get_name(self) -> str:
        if not hasattr(self, "enforcement_body") or self.enforcement_body is None:
            return self.name
        return self.name.format(enforcement_body=self.enforcement_body)


class SimplifiedCasePlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_required_for_url = True
        self.instance_class: ClassVar[SimplifiedCase] = SimplifiedCase
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: SimplifiedCase):
        self.set_instance(instance=case)
        super().populate_from_case(case=case)


class DetailedCasePlatformPage(SimplifiedCasePlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: ClassVar[DetailedCase] = DetailedCase

    def get_case(self) -> DetailedCase | None:
        if self.instance is not None:
            if isinstance(self.instance, DetailedCase):
                return self.instance

    def populate_from_case(self, case: DetailedCase):
        self.set_instance(instance=case)


class MobileCasePlatformPage(SimplifiedCasePlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: ClassVar[MobileCase] = MobileCase

    def get_case(self) -> MobileCase | None:
        if self.instance is not None:
            if isinstance(self.instance, MobileCase):
                return self.instance

    def populate_from_case(self, case: MobileCase):
        self.set_instance(instance=case)


class CaseContactsPlatformPage(SimplifiedCasePlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        if case is not None:
            self.set_instance(instance=case)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = populate_subpages_with_instance(
                    platform_page=self, instance=case
                )
                for contact in case.contacts:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=contact
                    )
                self.subpages = bound_subpages


class DetailedCaseContactsPlatformPage(DetailedCasePlatformPage):
    def populate_from_case(self, case: DetailedCase):
        if case is not None:
            self.set_instance(instance=case)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = populate_subpages_with_instance(
                    platform_page=self, instance=case
                )
                for contact in case.contacts:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=contact
                    )
                self.subpages = bound_subpages


class CaseCommentsPlatformPage(SimplifiedCasePlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        if case is not None:
            self.set_instance(instance=case)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = []
                for comment in case.qa_comments:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=comment
                    )
                self.subpages = bound_subpages


class AuditPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_required_for_url = True
        self.instance_class: ClassVar[Audit] = Audit
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def set_instance(self, instance: models.Model):
        if isinstance(instance, SimplifiedCase) and instance.audit is not None:
            self.instance = instance.audit
        else:
            super().set_instance(instance=instance)

    def populate_from_case(self, case: SimplifiedCase):
        self.set_instance(instance=case.audit)
        super().populate_from_case(case=case)


class AuditPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        if case.audit is not None:
            self.set_instance(instance=case.audit)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = []
                for page in case.audit.testable_pages:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=page
                    )
                self.subpages = bound_subpages


class AuditCustomIssuesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        if case.audit is not None:
            self.set_instance(instance=case.audit)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = populate_subpages_with_instance(
                    platform_page=self, instance=case.audit
                )
                for custom_issue in case.audit.custom_statement_check_results:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=custom_issue
                    )
                for (
                    custom_issue
                ) in case.audit.new_12_week_custom_statement_check_results:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=custom_issue
                    )
                self.subpages = bound_subpages


class ReportPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_required_for_url = True
        self.instance_class: ClassVar[Report] = Report
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: SimplifiedCase):
        if case.report is not None:
            self.set_instance(instance=case.report)
        super().populate_from_case(case=case)


class CaseEmailTemplatePreviewPlatformPage(PlatformPage):
    case: SimplifiedCase | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_required_for_url = True
        self.instance_class: ClassVar[EmailTemplate] = EmailTemplate
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    @property
    def url(self) -> str | None:
        if self.case is None or self.instance is None:
            return ""
        return reverse(
            self.url_name,
            kwargs={"case_id": self.case.id, self.url_kwarg_key: self.instance.id},
        )

    def populate_from_case(self, case: SimplifiedCase):
        self.case = case
        super().populate_from_case(case=case)


class AuditRetestPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        if case.audit is not None:
            self.set_instance(instance=case.audit)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = []
                for page in case.audit.testable_pages:
                    if page.failed_check_results.count() > 0:
                        bound_subpages += populate_subpages_with_instance(
                            platform_page=self, instance=page
                        )
                self.subpages = bound_subpages


class EqualityBodyRetestPlatformPage(PlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_required_for_url = True
        self.instance_class: ClassVar[Retest] = Retest
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    @property
    def show(self):
        return False


class RetestOverviewPlatformPage(SimplifiedCasePlatformPage):
    def populate_from_case(self, case: SimplifiedCase):
        self.set_instance(instance=case)
        if self.subpages is not None:
            bound_subpages: list[PlatformPage] = []
            for retest in case.retests:
                if retest.id_within_case > 0:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=retest
                    )
            self.subpages = bound_subpages


class EqualityBodyRetestPagesPlatformPage(EqualityBodyRetestPlatformPage):
    def populate_subpage_instances(self):
        if self.subpages is not None and self.instance is not None:
            bound_subpages: list[PlatformPage] = []
            for retest_page in self.instance.retestpage_set.all():
                bound_subpages += populate_subpages_with_instance(
                    platform_page=self, instance=retest_page
                )
            self.subpages = bound_subpages


@dataclass
class PlatformPageGroup:
    class Type(StrEnum):
        SIMPLIFIED_CASE_NAV: str = auto()
        DETAILED_CASE_NAV: str = auto()
        MOBILE_CASE_NAV: str = auto()
        CASE_TOOLS: str = auto()
        DEFAULT: str = auto()

    name: str
    type: Type = Type.DEFAULT
    show_flag_name: str | None = None
    case_nav_group: bool = True
    pages: list[PlatformPage] | None = None

    @property
    def show(self):
        return self.case_nav_group

    def populate_from_case(self, case: SimplifiedCase):
        for page in self.pages:
            page.populate_from_case(case=case)

    def number_pages_and_subpages(self) -> int:
        """Count number of pages and subpages which can be marked as complete"""
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
        """Count number of pages and subpages which have been marked as complete"""
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


class SimplifiedCasePlatformPageGroup(PlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: SimplifiedCase | None = None

    @property
    def show(self):
        if self.case is not None and self.show_flag_name is not None:
            return getattr(self.case, self.show_flag_name)
        return self.case_nav_group

    def populate_from_case(self, case: SimplifiedCase):
        self.case = case
        super().populate_from_case(case=case)


class DetailedCasePlatformPageGroup(SimplifiedCasePlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.DETAILED_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: DetailedCase | None = None


class MobileCasePlatformPageGroup(SimplifiedCasePlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.MOBILE_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: MobileCase | None = None


TEST_TYPE_TO_CASE_NAV: dict[BaseCase.TestType, PlatformPageGroup.Type] = {
    BaseCase.TestType.SIMPLIFIED: PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV,
    BaseCase.TestType.DETAILED: PlatformPageGroup.Type.DETAILED_CASE_NAV,
    BaseCase.TestType.MOBILE: PlatformPageGroup.Type.MOBILE_CASE_NAV,
}

SITE_MAP: list[PlatformPageGroup] = [
    SimplifiedCasePlatformPageGroup(
        name="Case details",
        show_flag_name="not_archived",
        pages=[
            SimplifiedCasePlatformPage(
                name="Case metadata",
                url_name="simplified:edit-case-metadata",
                complete_flag_name="case_details_complete_date",
                case_details_form_class=CaseMetadataUpdateForm,
                case_details_template_name="simplified/details/details_case_metadata.html",
            )
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Initial test",
        show_flag_name="show_start_test",
        pages=[
            SimplifiedCasePlatformPage(
                name="Testing details",
                url_name="simplified:edit-test-results",
                next_page_url_name="audits:edit-audit-metadata",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Initial WCAG test",
        show_flag_name="not_archived_has_audit",
        pages=[
            AuditPlatformPage(
                name="Initial test metadata",
                url_name="audits:edit-audit-metadata",
                complete_flag_name="audit_metadata_complete_date",
                case_details_form_class=AuditMetadataUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="audits:edit-audit-pages",
            ),
            AuditPagesPlatformPage(
                name="Add or remove pages",
                url_name="audits:edit-audit-pages",
                complete_flag_name="audit_pages_complete_date",
                subpages=[
                    PlatformPage(
                        name="{instance.page_title} test",
                        url_name="audits:edit-audit-page-checks",
                        url_kwarg_key="pk",
                        instance_class=Page,
                        instance_required_for_url=True,
                        complete_flag_name="complete_date",
                        case_details_template_name="simplified/details/details_initial_page_wcag_results.html",
                    )
                ],
                case_details_template_name="simplified/details/details_initial_pages.html",
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-website-decision",
                complete_flag_name="audit_website_decision_complete_date",
                case_details_template_name="simplified/details/details_initial_website_compliance.html",
                next_page_url_name="audits:edit-audit-wcag-summary",
            ),
            AuditPlatformPage(
                name="WCAG summary",
                url_name="audits:edit-audit-wcag-summary",
                complete_flag_name="audit_wcag_summary_complete_date",
                next_page_url_name="audits:edit-statement-pages",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Initial statement",
        show_flag_name="not_archived_has_audit",
        pages=[
            AuditPlatformPage(
                name="Statement links",
                url_name="audits:edit-statement-pages",
                complete_flag_name="audit_statement_pages_complete_date",
                case_details_template_name="simplified/details/details_statement_links.html",
                next_page_url_name="audits:edit-statement-overview",
            ),
            AuditPlatformPage(
                name="Statement overview",
                url_name="audits:edit-statement-overview",
                complete_flag_name="audit_statement_overview_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="Statement information",
                        url_name="audits:edit-statement-website",
                        complete_flag_name="audit_statement_website_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_website.html",
                        next_page_url_name="audits:edit-statement-compliance",
                    ),
                    AuditPlatformPage(
                        name="Compliance status",
                        url_name="audits:edit-statement-compliance",
                        complete_flag_name="audit_statement_compliance_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_compliance.html",
                        next_page_url_name="audits:edit-statement-non-accessible",
                    ),
                    AuditPlatformPage(
                        name="Non-accessible content",
                        url_name="audits:edit-statement-non-accessible",
                        complete_flag_name="audit_statement_non_accessible_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_non_accessible.html",
                        next_page_url_name="audits:edit-statement-preparation",
                    ),
                    AuditPlatformPage(
                        name="Statement preparation",
                        url_name="audits:edit-statement-preparation",
                        complete_flag_name="audit_statement_preparation_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_preparation.html",
                        next_page_url_name="audits:edit-statement-feedback",
                    ),
                    AuditPlatformPage(
                        name="Feedback and enforcement procedure",
                        url_name="audits:edit-statement-feedback",
                        complete_flag_name="audit_statement_feedback_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_feedback.html",
                        next_page_url_name="audits:edit-statement-custom",
                    ),
                ],
                case_details_template_name="simplified/details/details_initial_statement_checks_overview.html",
            ),
            AuditCustomIssuesPlatformPage(
                name="Custom issues",
                url_name="audits:edit-statement-custom",
                complete_flag_name="audit_statement_custom_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="Add custom issue",
                        url_name="audits:edit-custom-issue-create",
                        url_kwarg_key="audit_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit custom issue {instance.issue_identifier}",
                        url_name="audits:edit-custom-issue-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=StatementCheckResult,
                    ),
                    PlatformPage(
                        name="Remove custom issue {instance.issue_identifier}",
                        url_name="audits:edit-custom-issue-delete-confirm",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=StatementCheckResult,
                    ),
                ],
                case_details_template_name="simplified/details/details_initial_statement_checks_custom.html",
                next_page_url_name="audits:edit-initial-disproportionate-burden",
            ),
            AuditPlatformPage(
                name="Disproportionate burden",
                url_name="audits:edit-initial-disproportionate-burden",
                complete_flag_name="initial_disproportionate_burden_complete_date",
                case_details_form_class=InitialDisproportionateBurdenUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="audits:edit-statement-decision",
            ),
            AuditPlatformPage(
                name="Statement compliance",
                url_name="audits:edit-statement-decision",
                complete_flag_name="audit_statement_decision_complete_date",
                case_details_template_name="simplified/details/details_initial_statement_compliance.html",
                next_page_url_name="audits:edit-audit-statement-summary",
            ),
            AuditPlatformPage(
                name="Statement summary",
                url_name="audits:edit-audit-statement-summary",
                complete_flag_name="audit_statement_summary_complete_date",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Start report",
        show_flag_name="show_create_report",
        pages=[
            SimplifiedCasePlatformPage(
                name="Start report",
                url_name="simplified:edit-create-report",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Report QA",
        show_flag_name="not_archived_has_report",
        pages=[
            SimplifiedCasePlatformPage(
                name="Report ready for QA",
                url_name="simplified:edit-report-ready-for-qa",
                complete_flag_name="reporting_details_complete_date",
                case_details_form_class=CaseReportReadyForQAUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-qa-auditor",
            ),
            SimplifiedCasePlatformPage(
                name="QA auditor",
                url_name="simplified:edit-qa-auditor",
                complete_flag_name="qa_auditor_complete_date",
                case_details_form_class=CaseQAAuditorUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-qa-comments",
            ),
            CaseCommentsPlatformPage(
                name="Comments ({instance.qa_comments_count})",
                url_name="simplified:edit-qa-comments",
                subpages=[
                    PlatformPage(
                        name="Edit or delete comment",
                        url_name="comments:edit-qa-comment",
                        instance_class=Comment,
                        instance_required_for_url=True,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="simplified/details/details_qa_comments.html",
                next_page_url_name="simplified:edit-qa-approval",
            ),
            SimplifiedCasePlatformPage(
                name="QA approval",
                url_name="simplified:edit-qa-approval",
                complete_flag_name="qa_approval_complete_date",
                case_details_form_class=CaseQAApprovalUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-publish-report",
            ),
            SimplifiedCasePlatformPage(
                name="Publish report",
                url_name="simplified:edit-publish-report",
                complete_flag_name="publish_report_complete_date",
                subpages=[
                    ReportPlatformPage(
                        name="Republish report",
                        url_name="reports:report-republish",
                        instance_class=Report,
                        visible_only_when_current=True,
                    ),
                ],
                next_page_url_name="simplified:manage-contact-details",
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
                instance_class=Report,
            ),
            ReportPlatformPage(
                name="Report visit logs",
                url_name="reports:report-metrics-view",
                instance_class=Report,
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Contact details",
        show_flag_name="not_archived",
        pages=[
            CaseContactsPlatformPage(
                name="Manage contact details",
                url_name="simplified:manage-contact-details",
                complete_flag_name="manage_contact_details_complete_date",
                subpages=[
                    SimplifiedCasePlatformPage(
                        name="Add contact",
                        url_name="simplified:edit-contact-create",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit contact {instance}",
                        url_name="simplified:edit-contact-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=Contact,
                    ),
                ],
                case_details_form_class=ManageContactDetailsUpdateForm,
                case_details_template_name="simplified/details/details_manage_contact_details.html",
            ),
            SimplifiedCasePlatformPage(
                name="Request contact details",
                url_name="simplified:edit-request-contact-details",
                complete_flag_name="request_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseRequestContactDetailsUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-one-week-contact-details",
            ),
            SimplifiedCasePlatformPage(
                name="One-week follow-up",
                url_name="simplified:edit-one-week-contact-details",
                complete_flag_name="one_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseOneWeekContactDetailsUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-four-week-contact-details",
            ),
            SimplifiedCasePlatformPage(
                name="Four-week follow-up",
                url_name="simplified:edit-four-week-contact-details",
                complete_flag_name="four_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=CaseFourWeekContactDetailsUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-report-sent-on",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Report correspondence",
        show_flag_name="not_archived",
        pages=[
            SimplifiedCasePlatformPage(
                name="Report sent on",
                url_name="simplified:edit-report-sent-on",
                complete_flag_name="report_sent_on_complete_date",
                case_details_form_class=CaseReportSentOnUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-report-one-week-followup",
            ),
            SimplifiedCasePlatformPage(
                name="One week follow-up",
                url_name="simplified:edit-report-one-week-followup",
                complete_flag_name="one_week_followup_complete_date",
                case_details_form_class=CaseReportOneWeekFollowupUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-report-four-week-followup",
            ),
            SimplifiedCasePlatformPage(
                name="Four week follow-up",
                url_name="simplified:edit-report-four-week-followup",
                complete_flag_name="four_week_followup_complete_date",
                case_details_form_class=CaseReportFourWeekFollowupUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-report-acknowledged",
            ),
            SimplifiedCasePlatformPage(
                name="Report acknowledged",
                url_name="simplified:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                case_details_form_class=CaseReportAcknowledgedUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-12-week-update-requested",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="12-week correspondence",
        show_flag_name="not_archived",
        pages=[
            SimplifiedCasePlatformPage(
                name="12-week update requested",
                url_name="simplified:edit-12-week-update-requested",
                complete_flag_name="twelve_week_update_requested_complete_date",
                case_details_form_class=CaseTwelveWeekUpdateRequestedUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-12-week-one-week-followup-final",
            ),
            SimplifiedCasePlatformPage(
                name="One week follow-up for final update",
                url_name="simplified:edit-12-week-one-week-followup-final",
                complete_flag_name="one_week_followup_final_complete_date",
                case_details_form_class=CaseOneWeekFollowupFinalUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-12-week-update-request-ack",
            ),
            SimplifiedCasePlatformPage(
                name="12-week update request acknowledged",
                url_name="simplified:edit-12-week-update-request-ack",
                complete_flag_name="twelve_week_update_request_ack_complete_date",
                case_details_form_class=CaseTwelveWeekUpdateAcknowledgedUpdateForm,
                case_details_template_name="simplified/details/details.html",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Start 12-week retest",
        show_flag_name="show_start_12_week_retest",
        pages=[
            SimplifiedCasePlatformPage(
                name="Start 12-week retest",
                url_name="simplified:edit-twelve-week-retest",
                next_page_url_name="audits:edit-audit-retest-metadata",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="12-week WCAG test",
        show_flag_name="show_12_week_retest",
        pages=[
            AuditPlatformPage(
                name="12-week retest metadata",
                url_name="audits:edit-audit-retest-metadata",
                complete_flag_name="audit_retest_metadata_complete_date",
                case_details_form_class=AuditRetestMetadataUpdateForm,
                case_details_template_name="simplified/details/details.html",
            ),
            AuditRetestPagesPlatformPage(
                name="Update page links",
                url_name="audits:edit-audit-retest-pages",
                complete_flag_name="audit_retest_pages_complete_date",
                subpages=[
                    PlatformPage(
                        name="{instance.page_title} retest",
                        url_name="audits:edit-audit-retest-page-checks",
                        url_kwarg_key="pk",
                        instance_class=Page,
                        instance_required_for_url=True,
                        complete_flag_name="retest_complete_date",
                        case_details_template_name="simplified/details/details_twelve_week_page_wcag_results.html",
                    )
                ],
                case_details_template_name="simplified/details/details_12_week_pages.html",
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-audit-retest-website-decision",
                complete_flag_name="audit_retest_website_decision_complete_date",
                case_details_template_name="simplified/details/details_twelve_week_website_compliance.html",
                next_page_url_name="audits:edit-audit-retest-wcag-summary",
            ),
            AuditPlatformPage(
                name="WCAG summary",
                url_name="audits:edit-audit-retest-wcag-summary",
                complete_flag_name="audit_retest_wcag_summary_complete_date",
                next_page_url_name="audits:edit-audit-retest-statement-pages",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="12-week statement",
        show_flag_name="show_12_week_retest",
        pages=[
            AuditPlatformPage(
                name="Statement links",
                url_name="audits:edit-audit-retest-statement-pages",
                complete_flag_name="audit_retest_statement_pages_complete_date",
                next_page_url_name="audits:edit-retest-statement-overview",
            ),
            AuditPlatformPage(
                name="Statement overview",
                url_name="audits:edit-retest-statement-overview",
                complete_flag_name="audit_retest_statement_overview_complete_date",
                subpages=[
                    AuditPlatformPage(
                        name="Statement information",
                        url_name="audits:edit-retest-statement-website",
                        complete_flag_name="audit_retest_statement_website_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_website.html",
                        next_page_url_name="audits:edit-retest-statement-compliance",
                    ),
                    AuditPlatformPage(
                        name="Compliance status",
                        url_name="audits:edit-retest-statement-compliance",
                        complete_flag_name="audit_retest_statement_compliance_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_compliance.html",
                        next_page_url_name="audits:edit-retest-statement-non-accessible",
                    ),
                    AuditPlatformPage(
                        name="Non-accessible content",
                        url_name="audits:edit-retest-statement-non-accessible",
                        complete_flag_name="audit_retest_statement_non_accessible_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_non_accessible.html",
                        next_page_url_name="audits:edit-retest-statement-preparation",
                    ),
                    AuditPlatformPage(
                        name="Statement preparation",
                        url_name="audits:edit-retest-statement-preparation",
                        complete_flag_name="audit_retest_statement_preparation_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_preparation.html",
                        next_page_url_name="audits:edit-retest-statement-feedback",
                    ),
                    AuditPlatformPage(
                        name="Feedback and enforcement procedure",
                        url_name="audits:edit-retest-statement-feedback",
                        complete_flag_name="audit_retest_statement_feedback_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_feedback.html",
                        next_page_url_name="audits:edit-retest-statement-custom",
                    ),
                ],
                case_details_template_name="simplified/details/details_twelve_week_statement_checks_overview.html",
            ),
            AuditCustomIssuesPlatformPage(
                name="Custom issues",
                url_name="audits:edit-retest-statement-custom",
                complete_flag_name="audit_retest_statement_custom_complete_date",
                subpages=[
                    PlatformPage(
                        name="Edit initial custom issue {instance.issue_identifier}",
                        url_name="audits:edit-retest-initial-custom-issue-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=StatementCheckResult,
                    ),
                    AuditPlatformPage(
                        name="Add 12-week custom issue",
                        url_name="audits:edit-retest-12-week-custom-issue-create",
                        url_kwarg_key="audit_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit 12-week custom issue {instance.issue_identifier}",
                        url_name="audits:edit-retest-new-12-week-custom-issue-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=StatementCheckResult,
                    ),
                    PlatformPage(
                        name="Remove 12-week custom issue {instance.issue_identifier}",
                        url_name="audits:edit-retest-new-12-week-custom-issue-delete-confirm",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=StatementCheckResult,
                    ),
                ],
                case_details_template_name="simplified/details/details_twelve_week_statement_checks_custom.html",
                next_page_url_name="audits:edit-twelve-week-disproportionate-burden",
            ),
            AuditPlatformPage(
                name="Disproportionate burden",
                url_name="audits:edit-twelve-week-disproportionate-burden",
                complete_flag_name="twelve_week_disproportionate_burden_complete_date",
                case_details_form_class=TwelveWeekDisproportionateBurdenUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="audits:edit-audit-retest-statement-decision",
            ),
            AuditPlatformPage(
                name="Compliance decision",
                url_name="audits:edit-audit-retest-statement-decision",
                complete_flag_name="audit_retest_statement_decision_complete_date",
                case_details_template_name="simplified/details/details_twelve_week_statement_compliance.html",
                next_page_url_name="audits:edit-audit-retest-statement-summary",
            ),
            AuditPlatformPage(
                name="Statement summary",
                url_name="audits:edit-audit-retest-statement-summary",
                complete_flag_name="audit_retest_statement_summary_complete_date",
                next_page_url_name="simplified:edit-review-changes",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Closing the case",
        show_flag_name="not_archived",
        pages=[
            SimplifiedCasePlatformPage(
                name="Reviewing changes",
                url_name="simplified:edit-review-changes",
                complete_flag_name="review_changes_complete_date",
                case_details_form_class=CaseReviewChangesUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-enforcement-recommendation",
            ),
            SimplifiedCasePlatformPage(
                name="Recommendation",
                url_name="simplified:edit-enforcement-recommendation",
                complete_flag_name="enforcement_recommendation_complete_date",
                case_details_form_class=CaseEnforcementRecommendationUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-case-close",
            ),
            SimplifiedCasePlatformPage(
                name="Closing the case",
                url_name="simplified:edit-case-close",
                complete_flag_name="case_close_complete_date",
                case_details_form_class=CaseCloseUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-statement-enforcement",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Post case",
        pages=[
            SimplifiedCasePlatformPage(
                name="Statement enforcement",
                url_name="simplified:edit-statement-enforcement",
                case_details_form_class=CaseStatementEnforcementUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-equality-body-metadata",
            ),
            SimplifiedCasePlatformPage(
                name="Equality body metadata",
                url_name="simplified:edit-equality-body-metadata",
                case_details_form_class=CaseEqualityBodyMetadataUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:list-equality-body-correspondence",
            ),
            SimplifiedCasePlatformPage(
                name="Equality body correspondence",
                url_name="simplified:list-equality-body-correspondence",
                subpages=[
                    SimplifiedCasePlatformPage(
                        name="Add Zendesk ticket",
                        url_name="simplified:create-equality-body-correspondence",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit Zendesk ticket",
                        url_name="simplified:edit-equality-body-correspondence",
                        instance_class=EqualityBodyCorrespondence,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="simplified/details/details_equality_body_correspondence.html",
            ),
            RetestOverviewPlatformPage(
                name="Retest overview",
                url_name="simplified:edit-retest-overview",
                subpages=[
                    EqualityBodyRetestPlatformPage(
                        name="Retest #{instance.id_within_case}",
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
                                        name="{instance.retest} | {instance}",
                                        url_name="audits:edit-retest-page-checks",
                                        instance_class=RetestPage,
                                        complete_flag_name="complete_date",
                                    )
                                ],
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Comparison",
                                url_name="audits:retest-comparison-update",
                                complete_flag_name="comparison_complete_date",
                                next_page_url_name="audits:retest-compliance-update",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Compliance decision",
                                url_name="audits:retest-compliance-update",
                                complete_flag_name="compliance_complete_date",
                                next_page_url_name="audits:edit-equality-body-statement-pages",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement links",
                                url_name="audits:edit-equality-body-statement-pages",
                                complete_flag_name="statement_pages_complete_date",
                                next_page_url_name="audits:edit-equality-body-statement-overview",
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
                                        next_page_url_name="audits:edit-equality-body-statement-compliance",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Compliance status",
                                        url_name="audits:edit-equality-body-statement-compliance",
                                        complete_flag_name="statement_compliance_complete_date",
                                        next_page_url_name="audits:edit-equality-body-statement-non-accessible",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Non-accessible content",
                                        url_name="audits:edit-equality-body-statement-non-accessible",
                                        complete_flag_name="statement_non_accessible_complete_date",
                                        next_page_url_name="audits:edit-equality-body-statement-preparation",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Statement preparation",
                                        url_name="audits:edit-equality-body-statement-preparation",
                                        complete_flag_name="statement_preparation_complete_date",
                                        next_page_url_name="audits:edit-equality-body-statement-feedback",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Feedback and enforcement procedure",
                                        url_name="audits:edit-equality-body-statement-feedback",
                                        complete_flag_name="statement_feedback_complete_date",
                                        next_page_url_name="audits:edit-equality-body-statement-custom",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Custom statement issues",
                                        url_name="audits:edit-equality-body-statement-custom",
                                        complete_flag_name="statement_custom_complete_date",
                                        next_page_url_name="audits:edit-equality-body-statement-results",
                                    ),
                                ],
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement results",
                                url_name="audits:edit-equality-body-statement-results",
                                complete_flag_name="statement_results_complete_date",
                                next_page_url_name="audits:edit-equality-body-disproportionate-burden",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Disproportionate burden",
                                url_name="audits:edit-equality-body-disproportionate-burden",
                                complete_flag_name="disproportionate_burden_complete_date",
                                next_page_url_name="audits:edit-equality-body-statement-decision",
                            ),
                            EqualityBodyRetestPlatformPage(
                                name="Statement decision",
                                url_name="audits:edit-equality-body-statement-decision",
                                complete_flag_name="statement_decision_complete_date",
                                next_page_url_name="simplified:edit-retest-overview",
                            ),
                        ],
                    )
                ],
                case_details_template_name="simplified/details/details_retest_overview.html",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Case tools",
        type=PlatformPageGroup.Type.CASE_TOOLS,
        pages=[
            SimplifiedCasePlatformPage(
                name="View and search all case data",
                url_name="simplified:case-view-and-search",
            ),
            SimplifiedCasePlatformPage(
                name="Outstanding issues",
                show_flag_name="not_archived",
                url_name="simplified:outstanding-issues",
            ),
            SimplifiedCasePlatformPage(
                name="Email templates",
                show_flag_name="not_archived",
                url_name="simplified:email-template-list",
                url_kwarg_key="case_id",
                subpages=[
                    CaseEmailTemplatePreviewPlatformPage(
                        name="{instance.name}",
                        show_flag_name="not_archived",
                        url_name="simplified:email-template-preview",
                    ),
                ],
            ),
            SimplifiedCasePlatformPage(
                name="PSB Zendesk tickets",
                url_name="simplified:zendesk-tickets",
                case_details_template_name="simplified/details/details_psb_zendesk_tickets.html",
                subpages=[
                    SimplifiedCasePlatformPage(
                        name="Add PSB Zendesk ticket",
                        url_name="simplified:create-zendesk-ticket",
                        url_kwarg_key="case_id",
                    ),
                    PlatformPage(
                        name="Edit PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="simplified:update-zendesk-ticket",
                        instance_class=ZendeskTicket,
                    ),
                    PlatformPage(
                        name="Remove PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="simplified:confirm-delete-zendesk-ticket",
                        instance_class=ZendeskTicket,
                    ),
                ],
            ),
            SimplifiedCasePlatformPage(
                name="Unresponsive PSB",
                show_flag_name="not_archived",
                url_name="simplified:edit-no-psb-response",
                case_details_form_class=CaseNoPSBContactUpdateForm,
                case_details_template_name="simplified/details/details.html",
                next_page_url_name="simplified:edit-enforcement-recommendation",
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Simplified case",
        case_nav_group=False,
        pages=[
            SimplifiedCasePlatformPage(
                name="Simplified case overview", url_name="simplified:case-detail"
            ),
            SimplifiedCasePlatformPage(
                name="Create reminder",
                url_name="notifications:reminder-create",
                url_kwarg_key="case_id",
            ),
            SimplifiedCasePlatformPage(
                name="Deactivate case", url_name="simplified:deactivate-case"
            ),
            SimplifiedCasePlatformPage(
                name="Post case summary", url_name="simplified:edit-post-case"
            ),
            SimplifiedCasePlatformPage(
                name="Reactivate case", url_name="simplified:reactivate-case"
            ),
            SimplifiedCasePlatformPage(
                name="Cannot start new retest",
                url_name="simplified:retest-create-error",
            ),
            SimplifiedCasePlatformPage(
                name="Status workflow", url_name="simplified:status-workflow"
            ),
        ],
    ),
    PlatformPageGroup(
        name="Exports",
        pages=[
            ExportPlatformPage(
                name="{enforcement_body} CSV export manager",
                url_name="exports:export-list",
            ),
            PlatformPage(
                name="Delete {instance}",
                url_name="exports:export-confirm-delete",
                instance_required_for_url=True,
                instance_class=Export,
            ),
            PlatformPage(
                name="Confirm {instance}",
                url_name="exports:export-confirm-export",
                instance_required_for_url=True,
                instance_class=Export,
            ),
            ExportPlatformPage(
                name="New {enforcement_body} CSV export",
                url_name="exports:export-create",
            ),
            PlatformPage(
                name="{instance}",
                url_name="exports:export-detail",
                instance_required_for_url=True,
                instance_class=Export,
            ),
            SimplifiedCasePlatformPage(
                name="Export Case as email for #{instance.case_number}",
                url_name="exports:export-case-as-email",
            ),
        ],
    ),
    PlatformPageGroup(
        name="Settings",
        pages=[
            PlatformPage(name="Case metrics", url_name="common:metrics-case"),
            PlatformPage(name="Policy metrics", url_name="common:metrics-policy"),
            PlatformPage(name="Report metrics", url_name="common:metrics-report"),
            PlatformPage(
                name="Account details", url_name="users:edit-user", instance_class=User
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
                instance_class=Report,
            ),
            PlatformPage(
                name="WCAG errors editor",
                url_name="audits:wcag-definition-list",
                subpages=[
                    PlatformPage(
                        name="Create WCAG error",
                        url_name="audits:wcag-definition-create",
                        instance_required_for_url=True,
                    ),
                    PlatformPage(
                        name="Update WCAG definition",
                        url_name="audits:wcag-definition-update",
                        instance_required_for_url=True,
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
                        instance_required_for_url=True,
                    ),
                ],
            ),
            PlatformPage(name="Bulk URL search", url_name="common:bulk-url-search"),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Detailed testing case",
        case_nav_group=False,
        pages=[
            DetailedCasePlatformPage(
                name="Case overview", url_name="detailed:case-detail"
            ),
            DetailedCasePlatformPage(
                name="Change status", url_name="detailed:edit-case-status"
            ),
            DetailedCasePlatformPage(
                name="Case notes",
                url_name="detailed:create-case-note",
                url_kwarg_key="case_id",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Case details",
        pages=[
            DetailedCasePlatformPage(
                name="Case metadata",
                url_name="detailed:edit-case-metadata",
                complete_flag_name="case_metadata_complete_date",
                case_details_form_class=DetailedCaseMetadataUpdateForm,
                # case_details_template_name="simplified/details/details_case_metadata.html",
                next_page_url_name="detailed:manage-contact-details",
            )
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Initial contact",
        pages=[
            DetailedCaseContactsPlatformPage(
                name="Contact details",
                url_name="detailed:manage-contact-details",
                complete_flag_name="manage_contacts_complete_date",
                subpages=[
                    DetailedCasePlatformPage(
                        name="Add contact",
                        url_name="detailed:edit-contact-create",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit contact {instance}",
                        url_name="detailed:edit-contact-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_required_for_url=True,
                        instance_class=DetailedCaseContact,
                    ),
                ],
                # case_details_form_class=ManageContactDetailsUpdateForm,
                # case_details_template_name="simplified/details/details_manage_contact_details.html",
                next_page_url_name="detailed:edit-request-contact-details",
            ),
            DetailedCasePlatformPage(
                name="Information request",
                url_name="detailed:edit-request-contact-details",
                complete_flag_name="request_contact_details_complete_date",
                next_page_url_name="detailed:edit-chasing-record",
            ),
            DetailedCasePlatformPage(
                name="Chasing record",
                url_name="detailed:edit-chasing-record",
                complete_flag_name="chasing_record_complete_date",
                next_page_url_name="detailed:edit-information-delivered",
            ),
            DetailedCasePlatformPage(
                name="Information delivered",
                url_name="detailed:edit-information-delivered",
                complete_flag_name="information_delivered_complete_date",
                next_page_url_name="detailed:edit-initial-testing-details",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Initial test",
        pages=[
            DetailedCasePlatformPage(
                name="Testing details",
                url_name="detailed:edit-initial-testing-details",
                complete_flag_name="initial_testing_details_complete_date",
                next_page_url_name="detailed:edit-initial-testing-outcome",
            ),
            DetailedCasePlatformPage(
                name="Testing outcome",
                url_name="detailed:edit-initial-testing-outcome",
                complete_flag_name="initial_testing_outcome_complete_date",
                next_page_url_name="detailed:edit-initial-website-compliance",
            ),
            DetailedCasePlatformPage(
                name="Website compliance",
                url_name="detailed:edit-initial-website-compliance",
                complete_flag_name="initial_website_compliance_complete_date",
                next_page_url_name="detailed:edit-disproportionate-burden-compliance",
            ),
            DetailedCasePlatformPage(
                name="Disproportionate burden",
                url_name="detailed:edit-disproportionate-burden-compliance",
                complete_flag_name="initial_disproportionate_burden_complete_date",
                next_page_url_name="detailed:edit-initial-statement-compliance",
            ),
            DetailedCasePlatformPage(
                name="Statement compliance",
                url_name="detailed:edit-initial-statement-compliance",
                complete_flag_name="initial_statement_compliance_complete_date",
                next_page_url_name="detailed:edit-report-draft",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Report",
        pages=[
            DetailedCasePlatformPage(
                name="Report draft",
                url_name="detailed:edit-report-draft",
                complete_flag_name="initial_website_compliance_complete_date",
                next_page_url_name="detailed:edit-qa-approval",
            ),
            DetailedCasePlatformPage(
                name="QA approval",
                url_name="detailed:edit-qa-approval",
                complete_flag_name="initial_disproportionate_burden_complete_date",
                next_page_url_name="detailed:edit-publish-report",
            ),
            DetailedCasePlatformPage(
                name="Publish report",
                url_name="detailed:edit-publish-report",
                complete_flag_name="initial_statement_compliance_complete_date",
                next_page_url_name="detailed:edit-report-sent",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Correspondence",
        pages=[
            DetailedCasePlatformPage(
                name="Report sent",
                url_name="detailed:edit-report-sent",
                complete_flag_name="report_sent_complete_date",
                next_page_url_name="detailed:edit-report-acknowledged",
            ),
            DetailedCasePlatformPage(
                name="Report acknowledged",
                url_name="detailed:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                next_page_url_name="detailed:edit-12-week-deadline",
            ),
            DetailedCasePlatformPage(
                name="12-week deadline",
                url_name="detailed:edit-12-week-deadline",
                complete_flag_name="twelve_week_deadline_complete_date",
                next_page_url_name="detailed:edit-12-week-request-update",
            ),
            DetailedCasePlatformPage(
                name="12-week update request",
                url_name="detailed:edit-12-week-request-update",
                complete_flag_name="twelve_week_update_complete_date",
                next_page_url_name="detailed:edit-12-week-acknowledged",
            ),
            DetailedCasePlatformPage(
                name="12-week acknowledged",
                url_name="detailed:edit-12-week-acknowledged",
                complete_flag_name="twelve_week_acknowledged_complete_date",
                next_page_url_name="detailed:edit-retest-result",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Reviewing changes",
        pages=[
            DetailedCasePlatformPage(
                name="Retest result",
                url_name="detailed:edit-retest-result",
                complete_flag_name="retest_result_complete_date",
                next_page_url_name="detailed:edit-retest-summary",
            ),
            DetailedCasePlatformPage(
                name="Summary of changes",
                url_name="detailed:edit-retest-summary",
                complete_flag_name="summary_of_changes_complete_date",
                next_page_url_name="detailed:edit-retest-website-compliance",
            ),
            DetailedCasePlatformPage(
                name="Website compliance",
                url_name="detailed:edit-retest-website-compliance",
                complete_flag_name="retest_website_compliance_complete_date",
                next_page_url_name="detailed:edit-retest-disproportionate-burden",
            ),
            DetailedCasePlatformPage(
                name="Disproportionate burden",
                url_name="detailed:edit-retest-disproportionate-burden",
                complete_flag_name="retest_disproportionate_burden_complete_date",
                next_page_url_name="detailed:edit-retest-statement-compliance",
            ),
            DetailedCasePlatformPage(
                name="Statement compliance",
                url_name="detailed:edit-retest-statement-compliance",
                complete_flag_name="retest_statement_compliance_complete_date",
                next_page_url_name="detailed:edit-retest-metrics",
            ),
            DetailedCasePlatformPage(
                name="Final metrics",
                url_name="detailed:edit-retest-metrics",
                complete_flag_name="retest_metrics_complete_date",
                next_page_url_name="detailed:edit-case-close",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Closing the case",
        pages=[
            DetailedCasePlatformPage(
                name="Closing the case",
                url_name="detailed:edit-case-close",
                complete_flag_name="case_close_complete_date",
                next_page_url_name="detailed:edit-equality-body-metadata",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Post case",
        pages=[
            DetailedCasePlatformPage(
                name="Equality body metadata",
                url_name="detailed:edit-equality-body-metadata",
                complete_flag_name="enforcement_body_metadata_complete_date",
                next_page_url_name="detailed:case-detail",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Mobile testing case",
        case_nav_group=False,
        pages=[
            MobileCasePlatformPage(name="Case overview", url_name="mobile:case-detail"),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Case details",
        pages=[
            MobileCasePlatformPage(
                name="Case metadata",
                url_name="mobile:edit-case-metadata",
                complete_flag_name="case_metadata_complete_date",
                case_details_form_class=MobileCaseMetadataUpdateForm,
                # case_details_template_name="simplified/details/details_case_metadata.html",
            )
        ],
    ),
    PlatformPageGroup(
        name="Non-Case other",
        pages=[
            PlatformPage(name="Create case", url_name="simplified:pick-test-type"),
            PlatformPage(name="Create case", url_name="simplified:case-create"),
            PlatformPage(name="Search cases", url_name="cases:case-list"),
            PlatformPage(
                name="Create simplified case", url_name="simplified:case-create"
            ),
            PlatformPage(name="Create detailed case", url_name="detailed:case-create"),
            PlatformPage(name="Create mobile case", url_name="mobile:case-create"),
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
                instance_required_for_url=True,
                instance_class=Task,
            ),
            PlatformPage(name="Privacy notice", url_name="common:privacy-notice"),
            PlatformPage(
                name="More information about monitoring",
                url_name="common:more-information",
            ),
        ],
    ),
    PlatformPageGroup(
        name="Tech team",
        pages=[
            SimplifiedCasePlatformPage(
                name="Case history", url_name="simplified:case-history"
            ),
            PlatformPage(name="Issue reports", url_name="common:issue-reports-list"),
            PlatformPage(
                name="Reference implementations",
                url_name="common:reference-implementation",
            ),
            PlatformPage(name="Tools and sitemap", url_name="common:platform-checking"),
            PlatformPage(
                name="Reset detailed or mobile case data", url_name="common:import-csv"
            ),
        ],
    ),
]


def build_sitemap_by_url_name(
    site_map: list[PlatformPageGroup],
) -> dict[str, PlatformPage]:
    """Initialise SITEMAP_BY_URL_NAME dictionary"""

    def add_pages(pages: list[PlatformPage], platform_page_group: PlatformPageGroup):
        """Iterate through pages list adding to sitemap dictionary"""
        for page in pages:
            page.platform_page_group: PlatformPageGroup = platform_page_group
            if page.url_name:
                if page.url_name in sitemap_by_url_name:
                    logger.warning(
                        "Duplicate page url_name found %s %s", page.url_name, page
                    )
                else:
                    sitemap_by_url_name[page.url_name] = page
            if page.subpages is not None:
                add_pages(pages=page.subpages, platform_page_group=platform_page_group)

    sitemap_by_url_name: dict[str, PlatformPage] = {}
    for platform_page_group in site_map:
        if platform_page_group.pages is not None:
            add_pages(
                pages=platform_page_group.pages, platform_page_group=platform_page_group
            )
    return sitemap_by_url_name


SITEMAP_BY_URL_NAME: dict[str, PlatformPage] = build_sitemap_by_url_name(
    site_map=SITE_MAP
)


def get_requested_platform_page(request: HttpRequest) -> PlatformPage:
    """Return the current platform page"""
    url_resolver: URLResolver = resolve(request.path_info)
    url_name: str = url_resolver.view_name
    platform_page: PlatformPage = get_platform_page_by_url_name(url_name=url_name)
    platform_page.populate_from_request(request=request)
    return platform_page


def get_platform_page_by_url_name(
    url_name: str, instance: models.Model | None = None
) -> PlatformPage:
    """
    Find platform page in sitemap; Set platform page instance and return
    the platform page.
    """
    if url_name in SITEMAP_BY_URL_NAME:
        platform_page: PlatformPage = copy.copy(SITEMAP_BY_URL_NAME[url_name])
        platform_page.set_instance(instance=instance)
        return platform_page
    return PlatformPage(name=f"Page not found for {url_name}", url_name=url_name)


def build_sitemap_for_current_page(
    current_platform_page: PlatformPage,
) -> list[PlatformPageGroup]:
    """
    Populate the sitemap based on the current page.
    Return the case navigation subset of the sitemap if the current
    page is case-related, otherwise return the entire sitemap.
    """
    case: SimplifiedCase | DetailedCase | None = current_platform_page.get_case()
    case_nav_type: PlatformPageGroup.Type | None = (
        TEST_TYPE_TO_CASE_NAV.get(case.test_type) if case is not None else None
    )

    if current_platform_page.next_page_url_name is not None:
        current_platform_page.next_page = get_platform_page_by_url_name(
            url_name=current_platform_page.next_page_url_name, instance=case
        )
    if case is not None and case_nav_type is not None:
        site_map = copy.deepcopy(SITE_MAP)
        case_navigation: list[PlatformPageGroup] = [
            platform_page_group
            for platform_page_group in site_map
            if platform_page_group.type
            in [
                case_nav_type,
                PlatformPageGroup.Type.CASE_TOOLS,
            ]
        ]
        for platform_page_group in case_navigation:
            platform_page_group.populate_from_case(case=case)
        return case_navigation
    return SITE_MAP
