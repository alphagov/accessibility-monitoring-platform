"""Module with all page names to be placed in context"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from enum import StrEnum, auto

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpRequest
from django.urls import URLResolver, resolve, reverse

from ..audits.forms import (
    AuditInitialDisproportionateBurdenUpdateForm,
    AuditMetadataUpdateForm,
    AuditRetestMetadataUpdateForm,
    AuditTwelveWeekDisproportionateBurdenUpdateForm,
)
from ..audits.models import Audit, Page, Retest, RetestPage, StatementCheckResult
from ..cases.models import BaseCase
from ..comments.models import Comment
from ..detailed.forms import (
    DetailedCaseCloseUpdateForm,
    DetailedCaseMetadataUpdateForm,
    DetailedCaseRecommendationUpdateForm,
    DetailedContactInformationRequestUpdateForm,
    DetailedEnforcementBodyMetadataUpdateForm,
    DetailedFinalReportUpdateForm,
    DetailedInitialTestingDetailsUpdateForm,
    DetailedInitialTestingOutcomeUpdateForm,
    DetailedQAApprovalUpdateForm,
    DetailedQAAuditorUpdateForm,
    DetailedReportAcknowledgedUpdateForm,
    DetailedReportReadyForQAUpdateForm,
    DetailedReportSentUpdateForm,
    DetailedRetestComplianceDecisionsUpdateForm,
    DetailedRetestResultUpdateForm,
    DetailedStatementEnforcementUpdateForm,
    DetailedTwelveWeekDeadlineUpdateForm,
    DetailedTwelveWeekReceivedUpdateForm,
    DetailedTwelveWeekRequestUpdateForm,
    DetailedUnresponsivePSBUpdateForm,
)
from ..detailed.models import Contact as DetailedCaseContact
from ..detailed.models import DetailedCase, DetailedCaseHistory
from ..detailed.models import ZendeskTicket as DetailedZendeskTicket
from ..exports.models import Export
from ..mobile.forms import (
    MobileCaseCloseUpdateForm,
    MobileCaseMetadataUpdateForm,
    MobileCaseRecommendationUpdateForm,
    MobileContactInformationRequestUpdateForm,
    MobileEnforcementBodyMetadataUpdateForm,
    MobileFinalReportUpdateForm,
    MobileInitialTestAndroidDetailsUpdateForm,
    MobileInitialTestAndroidOutcomeUpdateForm,
    MobileInitialTestAuditorUpdateForm,
    MobileInitialTestiOSDetailsUpdateForm,
    MobileInitialTestiOSOutcomeUpdateForm,
    MobileQAApprovalUpdateForm,
    MobileQAAuditorUpdateForm,
    MobileReportAcknowledgedUpdateForm,
    MobileReportReadyForQAUpdateForm,
    MobileReportSentUpdateForm,
    MobileRetestAndroidComplianceDecisionsUpdateForm,
    MobileRetestAndroidResultUpdateForm,
    MobileRetestiOSComplianceDecisionsUpdateForm,
    MobileRetestiOSResultUpdateForm,
    MobileStatementEnforcementUpdateForm,
    MobileTwelveWeekDeadlineUpdateForm,
    MobileTwelveWeekReceivedUpdateForm,
    MobileTwelveWeekRequestUpdateForm,
    MobileUnresponsivePSBUpdateForm,
)
from ..mobile.models import (
    MobileCase,
    MobileCaseHistory,
    MobileContact,
    MobileZendeskTicket,
)
from ..notifications.models import Task
from ..reports.models import Report
from ..simplified.forms import (
    SimplifiedCaseCloseUpdateForm,
    SimplifiedCaseEnforcementRecommendationUpdateForm,
    SimplifiedCaseEqualityBodyMetadataUpdateForm,
    SimplifiedCaseFourWeekContactDetailsUpdateForm,
    SimplifiedCaseMetadataUpdateForm,
    SimplifiedCaseNoPSBContactUpdateForm,
    SimplifiedCaseOneWeekContactDetailsUpdateForm,
    SimplifiedCaseOneWeekFollowup12WeekUpdateForm,
    SimplifiedCaseQAApprovalUpdateForm,
    SimplifiedCaseQAAuditorUpdateForm,
    SimplifiedCaseReportAcknowledgedUpdateForm,
    SimplifiedCaseReportFourWeekFollowupUpdateForm,
    SimplifiedCaseReportOneWeekFollowupUpdateForm,
    SimplifiedCaseReportReadyForQAUpdateForm,
    SimplifiedCaseReportSentOnUpdateForm,
    SimplifiedCaseRequestContactDetailsUpdateForm,
    SimplifiedCaseReviewChangesUpdateForm,
    SimplifiedCaseStatementEnforcementUpdateForm,
    SimplifiedCaseTwelveWeekUpdateAcknowledgedUpdateForm,
    SimplifiedCaseTwelveWeekUpdateRequestedUpdateForm,
    SimplifiedManageContactDetailsUpdateForm,
)
from ..simplified.models import (
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    SimplifiedCaseHistory,
    ZendeskTicket,
)
from .models import EmailTemplate

AnyCaseType = BaseCase | SimplifiedCase | DetailedCase | MobileCase


logger = logging.getLogger(__name__)


def populate_subpages_with_instance(
    platform_page: PlatformPage, instance=models.Model
) -> list[PlatformPage]:
    """Set instance on each subpage where instance class matches"""
    subpages: list[PlatformPage] = []
    if platform_page.subpages is not None:
        for subpage in platform_page.subpages:
            if subpage.instance_class is not None and isinstance(
                instance, subpage.instance_class
            ):
                bound_subpage: PlatformPage = copy.copy(subpage)
                bound_subpage.instance = instance
                bound_subpage.populate_subpage_instances()
                subpages.append(bound_subpage)
    return subpages


class PlatformPage:
    name: str
    platform_page_group: PlatformPageGroup | None = None
    url_name: str | None = None
    url_kwarg_key: str | None = None
    instance_class: type[models.Model] | None = None
    instance: models.Model | None = None
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
        platform_page_group: PlatformPageGroup | None = None,
        url_name: str | None = None,
        url_kwarg_key: str | None = None,
        instance_class: type[models.Model] | None = None,
        instance: models.Model | None = None,
        complete_flag_name: str | None = None,
        show_flag_name: str | None = None,
        visible_only_when_current: bool = False,
        subpages: list[PlatformPage] | None = None,
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
    def url(self) -> str:
        if self.url_name is None:
            return ""
        if self.name.startswith("Page not found for "):
            return ""
        if self.url_kwarg_key and self.instance is not None:
            return reverse(self.url_name, kwargs={self.url_kwarg_key: self.instance.id})
        if self.url_kwarg_key and self.instance is None:
            logger.warning(
                "Expected instance missing; Url cannot be calculated %s %s",
                self.url_name,
                self,
            )
            return ""
        return reverse(self.url_name)

    @property
    def show(self):
        """Should page be visible in the case navigation UI"""
        if self.instance is not None and self.show_flag_name is not None:
            return getattr(self.instance, self.show_flag_name)
        if self.instance is None and self.url_kwarg_key:
            return False
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

    def populate_from_case(self, case: AnyCaseType):
        if case.__class__ == BaseCase:
            case: SimplifiedCase | DetailedCase | MobileCase = case.get_case()
        if self.instance is None and isinstance(case, self.instance_class):
            self.set_instance(instance=case)
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

    def get_case(self) -> AnyCaseType | None:
        if self.instance is not None:
            if isinstance(self.instance, BaseCase):
                return self.instance.get_case()
            if hasattr(self.instance, "base_case"):
                return self.instance.base_case.get_case()
            if hasattr(self.instance, "simplified_case") and isinstance(
                self.instance.simplified_case, SimplifiedCase
            ):
                return self.instance.simplified_case
            if hasattr(self.instance, "detailed_case") and isinstance(
                self.instance.detailed_case, DetailedCase
            ):
                return self.instance.detailed_case
            if hasattr(self.instance, "mobile_case") and isinstance(
                self.instance.mobile_case, MobileCase
            ):
                return self.instance.mobile_case
            if hasattr(self.instance, "audit"):
                return self.instance.audit.simplified_case
            if hasattr(self.instance, "retest"):
                return self.instance.retest.simplified_case


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


class BaseCasePlatformPage(PlatformPage):
    case_attr_name: str = "base_case"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: type[BaseCase] = BaseCase
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def set_instance(self, instance: models.Model | None):
        if self.instance_class is not None and instance is not None:
            if isinstance(instance, self.instance_class):
                self.instance = instance
            elif hasattr(instance, self.case_attr_name):
                self.instance = getattr(instance, self.case_attr_name)
            else:
                super().set_instance(instance=instance)


class SimplifiedCasePlatformPage(BaseCasePlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: type[SimplifiedCase] = SimplifiedCase
        self.case_attr_name = "simplified_case"


class DetailedCasePlatformPage(BaseCasePlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: type[DetailedCase] = DetailedCase
        self.case_attr_name = "detailed_case"


class MobileCasePlatformPage(BaseCasePlatformPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: type[MobileCase] = MobileCase
        self.case_attr_name = "mobile_case"


class CaseContactsPlatformPage(SimplifiedCasePlatformPage):
    def populate_from_case(self, case: AnyCaseType):
        if isinstance(case, SimplifiedCase):
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
    def populate_from_case(self, case: AnyCaseType):
        if isinstance(case, DetailedCase):
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


class MobileCaseContactsPlatformPage(MobileCasePlatformPage):
    def populate_from_case(self, case: AnyCaseType):
        if isinstance(case, MobileCase):
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


class BaseCaseCommentsPlatformPage(BaseCasePlatformPage):
    def populate_from_case(self, case: BaseCase):
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
        self.instance_class: type[Audit] = Audit
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def get_case(self) -> SimplifiedCase | None:
        if self.instance is not None:
            return self.instance.simplified_case

    def set_instance(self, instance: models.Model | None):
        if isinstance(instance, SimplifiedCase):
            if instance.audit is not None:
                self.instance = instance.audit
        else:
            super().set_instance(instance=instance)

    def populate_from_case(self, case: AnyCaseType):
        if hasattr(case, "audit") and isinstance(case.audit, Audit):
            self.set_instance(instance=case.audit)
        super().populate_from_case(case=case)


class AuditPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: AnyCaseType):
        if hasattr(case, "audit") and isinstance(case.audit, Audit):
            self.set_instance(instance=case.audit)
            if self.subpages is not None:
                bound_subpages: list[PlatformPage] = []
                for page in case.audit.testable_pages:
                    bound_subpages += populate_subpages_with_instance(
                        platform_page=self, instance=page
                    )
                self.subpages = bound_subpages


class AuditCustomIssuesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: AnyCaseType):
        if hasattr(case, "audit") and isinstance(case.audit, Audit):
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
        self.instance_class: type[Report] = Report
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    def populate_from_case(self, case: AnyCaseType):
        if hasattr(case, "report") and isinstance(case.report, Report):
            self.set_instance(instance=case.report)
        super().populate_from_case(case=case)


class CaseEmailTemplatePreviewPlatformPage(PlatformPage):
    case: AnyCaseType | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_class: type[EmailTemplate] = EmailTemplate
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    @property
    def url(self) -> str | None:
        if self.case is None or self.instance is None:
            return ""
        return reverse(
            self.url_name,
            kwargs={"case_id": self.base_case.id, self.url_kwarg_key: self.instance.id},
        )

    def populate_from_case(self, case: AnyCaseType | None):
        self.case = case
        super().populate_from_case(case=case)


class AuditRetestPagesPlatformPage(AuditPlatformPage):
    def populate_from_case(self, case: AnyCaseType):
        if hasattr(case, "audit") and isinstance(case.audit, Audit):
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
        self.instance_class: type[models.Model] = Retest
        if self.url_kwarg_key is None:
            self.url_kwarg_key: str = "pk"

    @property
    def show(self):
        return False

    def set_instance(self, instance: models.Model | None):
        if isinstance(instance, Retest):
            self.instance = instance

    def get_case(self) -> SimplifiedCase | None:
        if self.instance is not None:
            return self.instance.simplified_case


class RetestOverviewPlatformPage(SimplifiedCasePlatformPage):
    def populate_from_case(self, case: AnyCaseType):
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
        SIMPLIFIED_CASE_NAV = auto()
        DETAILED_CASE_NAV = auto()
        MOBILE_CASE_NAV = auto()
        SIMPLIFIED_CASE_TOOLS = auto()
        DETAILED_CASE_TOOLS = auto()
        MOBILE_CASE_TOOLS = auto()
        DEFAULT = auto()

    name: str
    type: Type = Type.DEFAULT
    show_flag_name: str | None = None
    case_nav_group: bool = True
    pages: list[PlatformPage] | None = None

    @property
    def show(self):
        return self.case_nav_group

    def populate_from_case(self, case: SimplifiedCase | DetailedCase | MobileCase):
        if self.pages is not None:
            for page in self.pages:
                page.populate_from_case(case=case)

    def completable_pages_and_subpages(self) -> list[PlatformPage]:
        """Pages and subpages which can be marked as complete"""
        if self.pages is None:
            return []
        completable_platform_pages: list[PlatformPage] = [
            page
            for page in self.pages
            if page.show and page.complete_flag_name is not None
        ]
        for page in self.pages:
            if page.subpages is not None:
                completable_platform_pages += [
                    page
                    for page in page.subpages
                    if page.show and page.complete_flag_name is not None
                ]
        return completable_platform_pages

    def number_pages_and_subpages(self) -> int:
        """Count number of pages and subpages which can be marked as complete"""
        return len(self.completable_pages_and_subpages())

    def number_complete(self) -> int:
        """Count number of pages and subpages which have been marked as complete"""
        return len(
            [
                platform_page
                for platform_page in self.completable_pages_and_subpages()
                if platform_page.complete
            ]
        )


class BaseCasePlatformPageGroup(PlatformPageGroup):

    @property
    def show(self):
        if self.case is not None and self.show_flag_name is not None:
            return getattr(self.case, self.show_flag_name)
        return self.case_nav_group

    def populate_from_case(self, case: SimplifiedCase | DetailedCase | MobileCase):
        self.case = case
        super().populate_from_case(case=case)


class SimplifiedCasePlatformPageGroup(BaseCasePlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: SimplifiedCase | None = None


class DetailedCasePlatformPageGroup(BaseCasePlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.DETAILED_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: DetailedCase | None = None


class MobileCasePlatformPageGroup(BaseCasePlatformPageGroup):
    def __init__(self, type=PlatformPageGroup.Type.MOBILE_CASE_NAV, **kwargs):
        super().__init__(**kwargs)
        self.type: PlatformPageGroup.Type = type
        self.case: MobileCase | None = None


MAP_TEST_TYPE_TO_CASE_NAV: dict[BaseCase.TestType, PlatformPageGroup.Type] = {
    BaseCase.TestType.SIMPLIFIED: PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV,
    BaseCase.TestType.DETAILED: PlatformPageGroup.Type.DETAILED_CASE_NAV,
    BaseCase.TestType.MOBILE: PlatformPageGroup.Type.MOBILE_CASE_NAV,
}

SIMPLIFIED_CASE_PAGE_GROUPS: list[PlatformPageGroup] = [
    SimplifiedCasePlatformPageGroup(
        name="Simplified testing case",
        case_nav_group=False,
        pages=[
            SimplifiedCasePlatformPage(
                name="Simplified case overview", url_name="simplified:case-detail"
            ),
            SimplifiedCasePlatformPage(
                name="Deactivate case", url_name="simplified:deactivate-case"
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
            PlatformPage(
                name="Edit case note #{instance.id_within_case}",
                url_name="simplified:edit-case-note",
                url_kwarg_key="pk",
                instance_class=SimplifiedCaseHistory,
            ),
        ],
    ),
    SimplifiedCasePlatformPageGroup(
        name="Case details",
        show_flag_name="not_archived",
        pages=[
            SimplifiedCasePlatformPage(
                name="Case metadata",
                url_name="simplified:edit-case-metadata",
                complete_flag_name="case_details_complete_date",
                case_details_form_class=SimplifiedCaseMetadataUpdateForm,
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
                case_details_template_name="cases/details/details.html",
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
                        next_page_url_name="audits:edit-statement-disproportionate",
                    ),
                    AuditPlatformPage(
                        name="Disproportionate burden claim",
                        url_name="audits:edit-statement-disproportionate",
                        complete_flag_name="audit_statement_disproportionate_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_initial_statement_checks_disproportionate.html",
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
                        instance_class=StatementCheckResult,
                    ),
                    PlatformPage(
                        name="Remove custom issue {instance.issue_identifier}",
                        url_name="audits:edit-custom-issue-delete-confirm",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
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
                case_details_form_class=AuditInitialDisproportionateBurdenUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=SimplifiedCaseReportReadyForQAUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-qa-auditor",
            ),
            SimplifiedCasePlatformPage(
                name="QA auditor",
                url_name="simplified:edit-qa-auditor",
                complete_flag_name="qa_auditor_complete_date",
                case_details_form_class=SimplifiedCaseQAAuditorUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-qa-comments",
            ),
            BaseCaseCommentsPlatformPage(
                name="QA comments ({instance.qa_comments_count})",
                url_name="simplified:edit-qa-comments",
                subpages=[
                    PlatformPage(
                        name="Edit or delete comment",
                        url_name="comments:edit-qa-comment-simplified",
                        url_kwarg_key="pk",
                        instance_class=Comment,
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
                case_details_form_class=SimplifiedCaseQAApprovalUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                        instance_class=Contact,
                    ),
                ],
                case_details_form_class=SimplifiedManageContactDetailsUpdateForm,
                case_details_template_name="simplified/details/details_manage_contact_details.html",
            ),
            SimplifiedCasePlatformPage(
                name="Request contact details",
                url_name="simplified:edit-request-contact-details",
                complete_flag_name="request_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=SimplifiedCaseRequestContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-one-week-contact-details",
            ),
            SimplifiedCasePlatformPage(
                name="One-week follow-up",
                url_name="simplified:edit-one-week-contact-details",
                complete_flag_name="one_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=SimplifiedCaseOneWeekContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-four-week-contact-details",
            ),
            SimplifiedCasePlatformPage(
                name="Four-week follow-up",
                url_name="simplified:edit-four-week-contact-details",
                complete_flag_name="four_week_contact_details_complete_date",
                show_flag_name="enable_correspondence_process",
                case_details_form_class=SimplifiedCaseFourWeekContactDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=SimplifiedCaseReportSentOnUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-report-one-week-followup",
            ),
            SimplifiedCasePlatformPage(
                name="One week follow-up",
                url_name="simplified:edit-report-one-week-followup",
                complete_flag_name="one_week_followup_complete_date",
                case_details_form_class=SimplifiedCaseReportOneWeekFollowupUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-report-four-week-followup",
            ),
            SimplifiedCasePlatformPage(
                name="Four week follow-up",
                url_name="simplified:edit-report-four-week-followup",
                complete_flag_name="four_week_followup_complete_date",
                case_details_form_class=SimplifiedCaseReportFourWeekFollowupUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-report-acknowledged",
            ),
            SimplifiedCasePlatformPage(
                name="Report acknowledged",
                url_name="simplified:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                case_details_form_class=SimplifiedCaseReportAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=SimplifiedCaseTwelveWeekUpdateRequestedUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-12-week-one-week-followup-final",
            ),
            SimplifiedCasePlatformPage(
                name="One week follow-up for 12-week update",
                url_name="simplified:edit-12-week-one-week-followup-final",
                complete_flag_name="one_week_followup_final_complete_date",
                case_details_form_class=SimplifiedCaseOneWeekFollowup12WeekUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-12-week-update-request-ack",
            ),
            SimplifiedCasePlatformPage(
                name="12-week update request acknowledged",
                url_name="simplified:edit-12-week-update-request-ack",
                complete_flag_name="twelve_week_update_request_ack_complete_date",
                case_details_form_class=SimplifiedCaseTwelveWeekUpdateAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_template_name="cases/details/details.html",
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
                        next_page_url_name="audits:edit-retest-statement-disproportionate",
                    ),
                    AuditPlatformPage(
                        name="Disproportionate burden claim",
                        url_name="audits:edit-retest-statement-disproportionate",
                        complete_flag_name="audit_retest_statement_disproportionate_complete_date",
                        show_flag_name="all_overview_statement_checks_have_passed",
                        case_details_template_name="simplified/details/details_twelve_week_statement_checks_disproportionate.html",
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
                        instance_class=StatementCheckResult,
                    ),
                    PlatformPage(
                        name="Remove 12-week custom issue {instance.issue_identifier}",
                        url_name="audits:edit-retest-new-12-week-custom-issue-delete-confirm",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
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
                case_details_form_class=AuditTwelveWeekDisproportionateBurdenUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=SimplifiedCaseReviewChangesUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-enforcement-recommendation",
            ),
            SimplifiedCasePlatformPage(
                name="Recommendation",
                url_name="simplified:edit-enforcement-recommendation",
                complete_flag_name="enforcement_recommendation_complete_date",
                case_details_form_class=SimplifiedCaseEnforcementRecommendationUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-case-close",
            ),
            SimplifiedCasePlatformPage(
                name="Closing the case",
                url_name="simplified:edit-case-close",
                complete_flag_name="case_close_complete_date",
                case_details_form_class=SimplifiedCaseCloseUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=SimplifiedCaseStatementEnforcementUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:edit-equality-body-metadata",
            ),
            SimplifiedCasePlatformPage(
                name="Equality body metadata",
                url_name="simplified:edit-equality-body-metadata",
                case_details_form_class=SimplifiedCaseEqualityBodyMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                        url_kwarg_key="pk",
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
                                        next_page_url_name="audits:edit-equality-body-statement-disproportionate",
                                    ),
                                    EqualityBodyRetestPlatformPage(
                                        name="Disproportionate burden claim",
                                        url_name="audits:edit-equality-body-statement-disproportionate",
                                        complete_flag_name="statement_disproportionate_complete_date",
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
        type=PlatformPageGroup.Type.SIMPLIFIED_CASE_TOOLS,
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
                        url_kwarg_key="pk",
                        instance_class=ZendeskTicket,
                    ),
                    PlatformPage(
                        name="Remove PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="simplified:confirm-delete-zendesk-ticket",
                        url_kwarg_key="pk",
                        instance_class=ZendeskTicket,
                    ),
                ],
            ),
            SimplifiedCasePlatformPage(
                name="Unresponsive PSB",
                show_flag_name="not_archived",
                url_name="simplified:edit-no-psb-response",
                case_details_form_class=SimplifiedCaseNoPSBContactUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="simplified:case-detail",
            ),
            SimplifiedCasePlatformPage(
                name="Case notes",
                url_name="simplified:create-case-note",
                url_kwarg_key="case_id",
                case_details_template_name="simplified/details/details_case_notes.html",
            ),
        ],
    ),
]
DETAILED_CASE_PAGE_GROUPS: list[PlatformPageGroup] = [
    DetailedCasePlatformPageGroup(
        name="Detailed testing case",
        case_nav_group=False,
        pages=[
            DetailedCasePlatformPage(
                name="Detailed case overview", url_name="detailed:case-detail"
            ),
            DetailedCasePlatformPage(
                name="Change status", url_name="detailed:edit-case-status"
            ),
            PlatformPage(
                name="Edit case note #{instance.id_within_case}",
                url_name="detailed:edit-case-note",
                url_kwarg_key="pk",
                instance_class=DetailedCaseHistory,
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
                case_details_template_name="detailed/details/details_case_metadata.html",
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
                        instance_class=DetailedCaseContact,
                    ),
                ],
                case_details_template_name="detailed/details/details_manage_contact_details.html",
                next_page_url_name="detailed:edit-request-contact-details",
            ),
            DetailedCasePlatformPage(
                name="Information request",
                url_name="detailed:edit-request-contact-details",
                complete_flag_name="contact_information_request_complete_date",
                case_details_form_class=DetailedContactInformationRequestUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-initial-testing-details",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Initial test",
        pages=[
            DetailedCasePlatformPage(
                name="Testing",
                url_name="detailed:edit-initial-testing-details",
                complete_flag_name="initial_testing_details_complete_date",
                case_details_form_class=DetailedInitialTestingDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-initial-testing-outcome",
            ),
            DetailedCasePlatformPage(
                name="Testing outcome",
                url_name="detailed:edit-initial-testing-outcome",
                complete_flag_name="initial_testing_outcome_complete_date",
                case_details_form_class=DetailedInitialTestingOutcomeUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-report-ready-for-qa",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Report QA",
        pages=[
            DetailedCasePlatformPage(
                name="Report ready for QA",
                url_name="detailed:edit-report-ready-for-qa",
                complete_flag_name="report_ready_for_qa_complete_date",
                case_details_form_class=DetailedReportReadyForQAUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-qa-auditor",
            ),
            DetailedCasePlatformPage(
                name="QA auditor",
                url_name="detailed:edit-qa-auditor",
                complete_flag_name="qa_auditor_complete_date",
                case_details_form_class=DetailedQAAuditorUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-qa-comments",
            ),
            BaseCaseCommentsPlatformPage(
                name="QA comments ({instance.qa_comments_count})",
                url_name="detailed:edit-qa-comments",
                subpages=[
                    PlatformPage(
                        name="Edit or delete comment",
                        url_name="comments:edit-qa-comment-detailed",
                        url_kwarg_key="pk",
                        instance_class=Comment,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="detailed/details/details_qa_comments.html",
                next_page_url_name="detailed:edit-qa-approval",
            ),
            DetailedCasePlatformPage(
                name="QA approval",
                url_name="detailed:edit-qa-approval",
                complete_flag_name="qa_approval_complete_date",
                case_details_form_class=DetailedQAApprovalUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-final-report",
            ),
            DetailedCasePlatformPage(
                name="Final report",
                url_name="detailed:edit-final-report",
                complete_flag_name="final_report_complete_date",
                case_details_form_class=DetailedFinalReportUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=DetailedReportSentUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-12-week-deadline",
            ),
            DetailedCasePlatformPage(
                name="12-week deadline",
                url_name="detailed:edit-12-week-deadline",
                complete_flag_name="twelve_week_deadline_complete_date",
                case_details_form_class=DetailedTwelveWeekDeadlineUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-report-acknowledged",
            ),
            DetailedCasePlatformPage(
                name="Report acknowledged",
                url_name="detailed:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                case_details_form_class=DetailedReportAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-12-week-request-update",
            ),
            DetailedCasePlatformPage(
                name="12-week update requested",
                url_name="detailed:edit-12-week-request-update",
                complete_flag_name="twelve_week_update_complete_date",
                case_details_form_class=DetailedTwelveWeekRequestUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-12-week-received",
            ),
            DetailedCasePlatformPage(
                name="12-week update received",
                url_name="detailed:edit-12-week-received",
                complete_flag_name="twelve_week_received_complete_date",
                case_details_form_class=DetailedTwelveWeekReceivedUpdateForm,
                case_details_template_name="cases/details/details.html",
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
                case_details_form_class=DetailedRetestResultUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-retest-compliance-decisions",
            ),
            DetailedCasePlatformPage(
                name="Compliance decisions",
                url_name="detailed:edit-retest-compliance-decisions",
                complete_flag_name="retest_compliance_decisions_complete_date",
                case_details_form_class=DetailedRetestComplianceDecisionsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-case-recommendation",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Closing the case",
        pages=[
            DetailedCasePlatformPage(
                name="Recommendation",
                url_name="detailed:edit-case-recommendation",
                complete_flag_name="case_recommendation_complete_date",
                case_details_form_class=DetailedCaseRecommendationUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-case-close",
            ),
            DetailedCasePlatformPage(
                name="Closing the case",
                url_name="detailed:edit-case-close",
                complete_flag_name="case_close_complete_date",
                case_details_form_class=DetailedCaseCloseUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-statement-enforcement",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Post case",
        pages=[
            DetailedCasePlatformPage(
                name="Statement enforcement",
                url_name="detailed:edit-statement-enforcement",
                complete_flag_name="statement_enforcement_complete_date",
                case_details_form_class=DetailedStatementEnforcementUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:edit-equality-body-metadata",
            ),
            DetailedCasePlatformPage(
                name="Equality body metadata",
                url_name="detailed:edit-equality-body-metadata",
                complete_flag_name="enforcement_body_metadata_complete_date",
                case_details_form_class=DetailedEnforcementBodyMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="detailed:case-detail",
            ),
        ],
    ),
    DetailedCasePlatformPageGroup(
        name="Case tools",
        type=PlatformPageGroup.Type.DETAILED_CASE_TOOLS,
        pages=[
            DetailedCasePlatformPage(
                name="View and search all case data",
                url_name="detailed:case-view-and-search",
            ),
            DetailedCasePlatformPage(
                name="Email templates",
                url_name="detailed:email-template-list",
                url_kwarg_key="case_id",
                subpages=[
                    CaseEmailTemplatePreviewPlatformPage(
                        name="{instance.name}",
                        url_name="detailed:email-template-preview",
                    ),
                ],
            ),
            DetailedCasePlatformPage(
                name="PSB Zendesk tickets",
                url_name="detailed:zendesk-tickets",
                case_details_template_name="detailed/details/details_psb_zendesk_tickets.html",
                subpages=[
                    DetailedCasePlatformPage(
                        name="Add PSB Zendesk ticket",
                        url_name="detailed:create-zendesk-ticket",
                        url_kwarg_key="case_id",
                    ),
                    PlatformPage(
                        name="Edit PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="detailed:update-zendesk-ticket",
                        url_kwarg_key="pk",
                        instance_class=DetailedZendeskTicket,
                    ),
                    PlatformPage(
                        name="Remove PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="detailed:confirm-delete-zendesk-ticket",
                        url_kwarg_key="pk",
                        instance_class=DetailedZendeskTicket,
                    ),
                ],
            ),
            DetailedCasePlatformPage(
                name="Unresponsive PSB",
                url_name="detailed:edit-unresponsive-psb",
                case_details_form_class=DetailedUnresponsivePSBUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            DetailedCasePlatformPage(
                name="Case notes",
                url_name="detailed:create-case-note",
                url_kwarg_key="case_id",
                case_details_template_name="detailed/details/details_case_notes.html",
            ),
        ],
    ),
]
MOBILE_CASE_PAGE_GROUPS: list[PlatformPageGroup] = [
    MobileCasePlatformPageGroup(
        name="Mobile testing case",
        case_nav_group=False,
        pages=[
            MobileCasePlatformPage(
                name="Mobile case overview", url_name="mobile:case-detail"
            ),
            MobileCasePlatformPage(
                name="Change status", url_name="mobile:edit-case-status"
            ),
            PlatformPage(
                name="Edit case note #{instance.id_within_case}",
                url_name="mobile:edit-case-note",
                url_kwarg_key="pk",
                instance_class=MobileCaseHistory,
            ),
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
                case_details_template_name="mobile/details/details_case_metadata.html",
                next_page_url_name="mobile:manage-contact-details",
            )
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Initial contact",
        pages=[
            MobileCaseContactsPlatformPage(
                name="Contact details",
                url_name="mobile:manage-contact-details",
                complete_flag_name="manage_contacts_complete_date",
                subpages=[
                    MobileCasePlatformPage(
                        name="Add contact",
                        url_name="mobile:edit-contact-create",
                        url_kwarg_key="case_id",
                        visible_only_when_current=True,
                    ),
                    PlatformPage(
                        name="Edit contact {instance}",
                        url_name="mobile:edit-contact-update",
                        url_kwarg_key="pk",
                        visible_only_when_current=True,
                        instance_class=MobileContact,
                    ),
                ],
                case_details_template_name="mobile/details/details_manage_contact_details.html",
                next_page_url_name="mobile:edit-request-contact-details",
            ),
            MobileCasePlatformPage(
                name="Information request",
                url_name="mobile:edit-request-contact-details",
                complete_flag_name="contact_information_request_complete_date",
                case_details_form_class=MobileContactInformationRequestUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-initial-test-auditor",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Initial test",
        pages=[
            MobileCasePlatformPage(
                name="Auditor",
                url_name="mobile:edit-initial-test-auditor",
                complete_flag_name="initial_auditor_complete_date",
                case_details_form_class=MobileInitialTestAuditorUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-initial-test-ios-details",
            ),
            MobileCasePlatformPage(
                name="iOS details",
                url_name="mobile:edit-initial-test-ios-details",
                complete_flag_name="initial_ios_details_complete_date",
                case_details_form_class=MobileInitialTestiOSDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-initial-test-ios-outcome",
            ),
            MobileCasePlatformPage(
                name="iOS outcome",
                url_name="mobile:edit-initial-test-ios-outcome",
                complete_flag_name="initial_ios_outcome_complete_date",
                case_details_form_class=MobileInitialTestiOSOutcomeUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-initial-test-android-details",
            ),
            MobileCasePlatformPage(
                name="Android details",
                url_name="mobile:edit-initial-test-android-details",
                complete_flag_name="initial_android_details_complete_date",
                case_details_form_class=MobileInitialTestAndroidDetailsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-initial-test-android-outcome",
            ),
            MobileCasePlatformPage(
                name="Android outcome",
                url_name="mobile:edit-initial-test-android-outcome",
                complete_flag_name="initial_android_outcome_complete_date",
                case_details_form_class=MobileInitialTestAndroidOutcomeUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-report-ready-for-qa",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Report QA",
        pages=[
            MobileCasePlatformPage(
                name="Reports ready for QA",
                url_name="mobile:edit-report-ready-for-qa",
                complete_flag_name="report_ready_for_qa_complete_date",
                case_details_form_class=MobileReportReadyForQAUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-qa-auditor",
            ),
            MobileCasePlatformPage(
                name="QA auditor",
                url_name="mobile:edit-qa-auditor",
                complete_flag_name="qa_auditor_complete_date",
                case_details_form_class=MobileQAAuditorUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-qa-comments",
            ),
            BaseCaseCommentsPlatformPage(
                name="QA comments ({instance.qa_comments_count})",
                url_name="mobile:edit-qa-comments",
                subpages=[
                    PlatformPage(
                        name="Edit or delete comment",
                        url_name="comments:edit-qa-comment-mobile",
                        url_kwarg_key="pk",
                        instance_class=Comment,
                        visible_only_when_current=True,
                    ),
                ],
                case_details_template_name="mobile/details/details_qa_comments.html",
                next_page_url_name="mobile:edit-qa-approval",
            ),
            MobileCasePlatformPage(
                name="QA approval",
                url_name="mobile:edit-qa-approval",
                complete_flag_name="qa_approval_complete_date",
                case_details_form_class=MobileQAApprovalUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-final-report",
            ),
            MobileCasePlatformPage(
                name="Final reports",
                url_name="mobile:edit-final-report",
                complete_flag_name="final_report_complete_date",
                case_details_form_class=MobileFinalReportUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-report-sent",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Correspondence",
        pages=[
            MobileCasePlatformPage(
                name="Reports sent",
                url_name="mobile:edit-report-sent",
                complete_flag_name="report_sent_complete_date",
                case_details_form_class=MobileReportSentUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-12-week-deadline",
            ),
            MobileCasePlatformPage(
                name="12-week deadline",
                url_name="mobile:edit-12-week-deadline",
                complete_flag_name="twelve_week_deadline_complete_date",
                case_details_form_class=MobileTwelveWeekDeadlineUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-report-acknowledged",
            ),
            MobileCasePlatformPage(
                name="Reports acknowledged",
                url_name="mobile:edit-report-acknowledged",
                complete_flag_name="report_acknowledged_complete_date",
                case_details_form_class=MobileReportAcknowledgedUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-12-week-request-update",
            ),
            MobileCasePlatformPage(
                name="12-week update requested",
                url_name="mobile:edit-12-week-request-update",
                complete_flag_name="twelve_week_update_complete_date",
                case_details_form_class=MobileTwelveWeekRequestUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-12-week-received",
            ),
            MobileCasePlatformPage(
                name="12-week update received",
                url_name="mobile:edit-12-week-received",
                complete_flag_name="twelve_week_received_complete_date",
                case_details_form_class=MobileTwelveWeekReceivedUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-retest-ios-result",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Reviewing changes",
        pages=[
            MobileCasePlatformPage(
                name="iOS retesting",
                url_name="mobile:edit-retest-ios-result",
                complete_flag_name="retest_ios_result_complete_date",
                case_details_form_class=MobileRetestiOSResultUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-retest-ios-compliance-decisions",
            ),
            MobileCasePlatformPage(
                name="iOS retest result",
                url_name="mobile:edit-retest-ios-compliance-decisions",
                complete_flag_name="retest_ios_compliance_decisions_complete_date",
                case_details_form_class=MobileRetestiOSComplianceDecisionsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-retest-android-result",
            ),
            MobileCasePlatformPage(
                name="Android retesting",
                url_name="mobile:edit-retest-android-result",
                complete_flag_name="retest_android_result_complete_date",
                case_details_form_class=MobileRetestAndroidResultUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-retest-android-compliance-decisions",
            ),
            MobileCasePlatformPage(
                name="Android retest result",
                url_name="mobile:edit-retest-android-compliance-decisions",
                complete_flag_name="retest_android_compliance_decisions_complete_date",
                case_details_form_class=MobileRetestAndroidComplianceDecisionsUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-case-recommendation",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Closing the case",
        pages=[
            MobileCasePlatformPage(
                name="Recommendation",
                url_name="mobile:edit-case-recommendation",
                complete_flag_name="case_recommendation_complete_date",
                case_details_form_class=MobileCaseRecommendationUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-case-close",
            ),
            MobileCasePlatformPage(
                name="Closing the case",
                url_name="mobile:edit-case-close",
                complete_flag_name="case_close_complete_date",
                case_details_form_class=MobileCaseCloseUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-statement-enforcement",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Post case",
        pages=[
            MobileCasePlatformPage(
                name="Statement enforcement",
                url_name="mobile:edit-statement-enforcement",
                complete_flag_name="statement_enforcement_complete_date",
                case_details_form_class=MobileStatementEnforcementUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:edit-equality-body-metadata",
            ),
            MobileCasePlatformPage(
                name="Equality body metadata",
                url_name="mobile:edit-equality-body-metadata",
                complete_flag_name="enforcement_body_metadata_complete_date",
                case_details_form_class=MobileEnforcementBodyMetadataUpdateForm,
                case_details_template_name="cases/details/details.html",
                next_page_url_name="mobile:case-detail",
            ),
        ],
    ),
    MobileCasePlatformPageGroup(
        name="Case tools",
        type=PlatformPageGroup.Type.MOBILE_CASE_TOOLS,
        pages=[
            MobileCasePlatformPage(
                name="View and search all case data",
                url_name="mobile:case-view-and-search",
            ),
            MobileCasePlatformPage(
                name="Email templates",
                url_name="mobile:email-template-list",
                url_kwarg_key="case_id",
                subpages=[
                    CaseEmailTemplatePreviewPlatformPage(
                        name="{instance.name}",
                        url_name="mobile:email-template-preview",
                    ),
                ],
            ),
            MobileCasePlatformPage(
                name="PSB Zendesk tickets",
                url_name="mobile:zendesk-tickets",
                case_details_template_name="mobile/details/details_psb_zendesk_tickets.html",
                subpages=[
                    MobileCasePlatformPage(
                        name="Add PSB Zendesk ticket",
                        url_name="mobile:create-zendesk-ticket",
                        url_kwarg_key="case_id",
                    ),
                    PlatformPage(
                        name="Edit PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="mobile:update-zendesk-ticket",
                        url_kwarg_key="pk",
                        instance_class=MobileZendeskTicket,
                    ),
                    PlatformPage(
                        name="Remove PSB Zendesk ticket #{instance.id_within_case}",
                        url_name="mobile:confirm-delete-zendesk-ticket",
                        url_kwarg_key="pk",
                        instance_class=MobileZendeskTicket,
                    ),
                ],
            ),
            MobileCasePlatformPage(
                name="Unresponsive PSB",
                url_name="mobile:edit-unresponsive-psb",
                case_details_form_class=MobileUnresponsivePSBUpdateForm,
                case_details_template_name="cases/details/details.html",
            ),
            MobileCasePlatformPage(
                name="Case notes",
                url_name="mobile:create-case-note",
                url_kwarg_key="case_id",
                case_details_template_name="mobile/details/details_case_notes.html",
            ),
        ],
    ),
]
SITE_MAP: list[PlatformPageGroup] = (
    SIMPLIFIED_CASE_PAGE_GROUPS
    + DETAILED_CASE_PAGE_GROUPS
    + MOBILE_CASE_PAGE_GROUPS
    + [
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
                    url_kwarg_key="pk",
                    instance_class=Export,
                ),
                PlatformPage(
                    name="Confirm {instance}",
                    url_name="exports:export-confirm-export",
                    url_kwarg_key="pk",
                    instance_class=Export,
                ),
                ExportPlatformPage(
                    name="New {enforcement_body} CSV export",
                    url_name="exports:export-create",
                ),
                PlatformPage(
                    name="{instance}",
                    url_name="exports:export-detail",
                    url_kwarg_key="pk",
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
                    name="Account details",
                    url_name="users:edit-user",
                    instance_class=User,
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
                PlatformPage(
                    name="Edit footer links", url_name="common:edit-footer-links"
                ),
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
                        ),
                        PlatformPage(
                            name="Update WCAG definition",
                            url_name="audits:wcag-definition-update",
                            url_kwarg_key="pk",
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
                            url_kwarg_key="pk",
                        ),
                    ],
                ),
                PlatformPage(
                    name="More information about monitoring",
                    url_name="common:more-information",
                ),
                PlatformPage(name="Bulk URL search", url_name="common:bulk-url-search"),
            ],
        ),
        PlatformPageGroup(
            name="Tech team",
            pages=[
                SimplifiedCasePlatformPage(
                    name="Simplified case history", url_name="simplified:case-history"
                ),
                DetailedCasePlatformPage(
                    name="Detailed case history", url_name="detailed:case-history"
                ),
                MobileCasePlatformPage(
                    name="Mobile case history", url_name="mobile:case-history"
                ),
                PlatformPage(
                    name="Reference implementation",
                    url_name="tech:reference-implementation",
                ),
                PlatformPage(
                    name="Equality body CSV metadata",
                    url_name="tech:equality-body-csv-metadata",
                ),
                PlatformPage(
                    name="Check logging and exceptions",
                    url_name="tech:platform-checking",
                ),
                PlatformPage(name="Sitemap", url_name="tech:sitemap"),
                PlatformPage(
                    name="Reset mobile case data",
                    url_name="tech:import-csv",
                ),
                PlatformPage(
                    name="Import detailed Trello comments",
                    url_name="tech:import-trello-comments",
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
        # Miscellaneous
        PlatformPageGroup(
            name="",
            pages=[
                PlatformPage(name="Search cases", url_name="cases:case-list"),
                PlatformPage(
                    name="Create simplified case", url_name="simplified:case-create"
                ),
                PlatformPage(
                    name="Create detailed case", url_name="detailed:case-create"
                ),
                PlatformPage(name="Create mobile case", url_name="mobile:case-create"),
                PlatformPage(
                    name="Accessibility statement",
                    url_name="common:accessibility-statement",
                ),
                PlatformPage(name="Contact admin", url_name="common:contact-admin"),
                PlatformPage(name="Dashboard", url_name="dashboard:home"),
                PlatformPage(name="Tasks", url_name="notifications:task-list"),
                BaseCasePlatformPage(
                    name="Create reminder",
                    url_name="notifications:reminder-create",
                    url_kwarg_key="case_id",
                ),
                PlatformPage(
                    name="Reminder",
                    url_name="notifications:edit-reminder-task",
                    url_kwarg_key="pk",
                    instance_class=Task,
                ),
                PlatformPage(name="Privacy notice", url_name="common:privacy-notice"),
            ],
        ),
    ]
)


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


SITEMAP_BY_URL_NAME: None = None
if SITEMAP_BY_URL_NAME is None:
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
    if SITEMAP_BY_URL_NAME is not None and url_name in SITEMAP_BY_URL_NAME:
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
    case: AnyCaseType | None = current_platform_page.get_case()
    case_nav_type: PlatformPageGroup.Type | None = (
        MAP_TEST_TYPE_TO_CASE_NAV.get(case.test_type) if case is not None else None
    )

    if current_platform_page.next_page_url_name is not None:
        current_platform_page.next_page = get_platform_page_by_url_name(
            url_name=current_platform_page.next_page_url_name, instance=case
        )

    if case is not None and case_nav_type is not None:
        site_map = copy.deepcopy(SITE_MAP)
        case_navigation: list[PlatformPageGroup] = []

        for platform_page_group in site_map:
            if (
                platform_page_group.type == case_nav_type
                or (
                    case_nav_type == PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV
                    and platform_page_group.type
                    == PlatformPageGroup.Type.SIMPLIFIED_CASE_TOOLS
                )
                or (
                    case_nav_type == PlatformPageGroup.Type.DETAILED_CASE_NAV
                    and platform_page_group.type
                    == PlatformPageGroup.Type.DETAILED_CASE_TOOLS
                )
                or (
                    case_nav_type == PlatformPageGroup.Type.MOBILE_CASE_NAV
                    and platform_page_group.type
                    == PlatformPageGroup.Type.MOBILE_CASE_TOOLS
                )
            ):
                platform_page_group.populate_from_case(case=case)
                case_navigation.append(platform_page_group)

        return case_navigation
    return SITE_MAP


class Sitemap:
    platform_page_groups: list[PlatformPageGroup]
    current_platform_page: PlatformPage
    next_platform_page: PlatformPage | None

    def __init__(self, request: HttpRequest):
        self.current_platform_page = get_requested_platform_page(request=request)
        self.platform_page_groups = build_sitemap_for_current_page(
            current_platform_page=self.current_platform_page
        )
