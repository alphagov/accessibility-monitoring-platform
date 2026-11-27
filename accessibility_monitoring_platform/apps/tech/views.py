"""Views for tech team app"""

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from ..audits.models import CustomStatementCheckResult
from ..cases.models import CASE_STATUSES
from ..common.models import EmailTemplate
from ..detailed.csv_export import (
    DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from ..detailed.models import DetailedCase
from ..mobile.csv_export import (
    MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from ..mobile.models import MobileCase
from ..simplified.csv_export import (
    SIMPLIFIED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from ..simplified.models import SimplifiedCase
from .forms import PlatformCheckingForm

logger = logging.getLogger(__name__)


class CaseContextMixin:
    """Put examples of cases in context"""

    template_name: str = "tech/reference_implementation.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        simplified_case: SimplifiedCase | None = SimplifiedCase.objects.filter(
            status=SimplifiedCase.Status.COMPLETE
        ).first()
        if simplified_case is None:
            simplified_case: SimplifiedCase | None = (
                SimplifiedCase.objects.all().first()
            )
        context["case"] = simplified_case
        context["simplified_case"] = simplified_case
        context["detailed_case"] = DetailedCase.objects.first()
        context["mobile_case"] = MobileCase.objects.first()
        return context


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ReferenceImplementaionView(CaseContextMixin, StaffRequiredMixin, TemplateView):
    """Reference implementation of reusable components"""

    template_name: str = "tech/reference_implementation.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["banner_case_detailed"] = context["detailed_case"]
        context["banner_case_mobile"] = MobileCase.objects.last()
        context["banner_case_archived"] = SimplifiedCase.objects.exclude(
            archive=""
        ).first()
        context["case_statuses"] = CASE_STATUSES
        return context


class CustomStatementCheckResultsView(StaffRequiredMixin, TemplateView):
    """View showing custom statement check results"""

    template_name: str = "tech/custom_statement_check_results.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        custom_statement_check_results: QuerySet[CustomStatementCheckResult] = (
            CustomStatementCheckResult.objects.filter(is_deleted=False)
        )
        no_initial_param: str | None = self.request.GET.get("no_initial")
        if no_initial_param:
            custom_statement_check_results = custom_statement_check_results.filter(
                public_comment=""
            )
        twelve_week_param: str | None = self.request.GET.get("twelve_week")
        if twelve_week_param:
            custom_statement_check_results = custom_statement_check_results.exclude(
                retest_comment=""
            )
        auditor_text_param: str | None = self.request.GET.get("auditor_text")
        if auditor_text_param:
            custom_statement_check_results = custom_statement_check_results.exclude(
                auditor_information=""
            )
        context["custom_statement_check_results"] = (
            custom_statement_check_results.order_by("-simplified_case_id", "id")
        )
        context["no_initial_param"] = no_initial_param
        context["twelve_week_param"] = twelve_week_param
        context["auditor_text_param"] = auditor_text_param
        return context


class EmailTemplatesView(CaseContextMixin, StaffRequiredMixin, TemplateView):
    """View showing email templates and which types of case use them."""

    template_name: str = "tech/email_templates.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["email_templates"] = EmailTemplate.objects.filter(is_deleted=False)
        return context


class EqualityBodyCsvMetadataView(StaffRequiredMixin, TemplateView):
    """
    View showing equality body CSV metadata for simplified, detailed and mobile cases
    and highlighting differences.
    """

    template_name: str = "tech/equality_body_csv_metadata.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["metadata"] = zip(
            SIMPLIFIED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
            DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
            MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
        )
        context["report"] = zip(
            SIMPLIFIED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
            DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
            MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
        )
        context["correspondence"] = zip(
            SIMPLIFIED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
        )
        context["test_summary"] = zip(
            SIMPLIFIED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
            DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
            MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
        )
        return context


class PlatformCheckingView(StaffRequiredMixin, FormView):
    """Test writing log messages and raiseing exceptions"""

    form_class = PlatformCheckingForm
    template_name: str = "tech/platform_checking.html"
    success_url: str = reverse_lazy("tech:platform-checking")

    def form_valid(self, form):
        if "raise_400" in self.request.POST:
            raise BadRequest
        if "raise_403" in self.request.POST:
            raise PermissionDenied
        if "raise_500" in self.request.POST:
            1 / 0  # noqa: B018
        logger.log(
            level=int(form.cleaned_data["level"]), msg=form.cleaned_data["message"]
        )
        return super().form_valid(form)


class SitemapView(StaffRequiredMixin, TemplateView):
    template_name: str = "tech/sitemap.html"
