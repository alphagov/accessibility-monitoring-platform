"""Views for tech team app"""

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from ..common.models import Boolean
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
from ..reports.models import Report
from ..simplified.csv_export import (
    SIMPLIFIED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from ..simplified.models import SimplifiedCase
from .forms import ImportCSVForm, ImportTrelloCommentsForm, PlatformCheckingForm
from .utils import import_mobile_cases_csv, import_trello_comments

logger = logging.getLogger(__name__)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ReferenceImplementaionView(StaffRequiredMixin, TemplateView):
    """Reference implementation of reusable components"""

    template_name: str = "tech/reference_implementation.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        report: Report | None = Report.objects.all().first()
        if report is None or not hasattr(
            report.base_case, "simplifiedcase"
        ):  # In test environment
            simplified_case: SimplifiedCase | None = (
                SimplifiedCase.objects.all().first()
            )
        else:
            simplified_case: SimplifiedCase = report.base_case.simplifiedcase
        context["case"] = simplified_case
        context["detailed_case"] = DetailedCase.objects.first()
        context["mobile_case"] = MobileCase.objects.first()
        context["banner_case_detailed"] = context["detailed_case"]
        context["banner_case_mobile"] = MobileCase.objects.last()
        context["banner_case_archived"] = SimplifiedCase.objects.exclude(
            archive=""
        ).first()
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
            1 / 0
        logger.log(
            level=int(form.cleaned_data["level"]), msg=form.cleaned_data["message"]
        )
        return super().form_valid(form)


class SitemapView(StaffRequiredMixin, TemplateView):
    template_name: str = "tech/sitemap.html"


class ImportCSV(StaffRequiredMixin, FormView):
    """Reset mobile Cases data from CSV"""

    form_class = ImportCSVForm
    template_name: str = "tech/import_csv.html"
    success_url: str = reverse_lazy("tech:import-csv")

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect:
        context: dict[str, Any] = self.get_context_data()
        form = context["form"]
        if form.is_valid():
            csv_data: str = form.cleaned_data["data"]
            import_mobile_cases_csv(csv_data)
        return self.render_to_response(self.get_context_data())


class ImportTrelloComments(StaffRequiredMixin, FormView):
    """Import Trello comments for Detailed cases from CSV data"""

    form_class = ImportTrelloCommentsForm
    template_name: str = "tech/import_trello_comments.html"
    success_url: str = reverse_lazy("tech:import-trello-comments")

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect:
        context: dict[str, Any] = self.get_context_data()
        form = context["form"]
        if form.is_valid():
            csv_data: str = form.cleaned_data["data"]
            reset_data: bool = form.cleaned_data["reset_data"] == Boolean.YES
            import_trello_comments(csv_data, reset_data)
        return self.render_to_response(self.get_context_data())
