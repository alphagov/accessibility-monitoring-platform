"""Views for tech team app"""

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from ..common.models import Boolean, IssueReport
from ..detailed.models import DetailedCase
from ..mobile.models import MobileCase
from ..reports.models import Report
from ..simplified.models import SimplifiedCase
from .forms import ImportCSVForm, ImportTrelloCommentsForm, PlatformCheckingForm
from .utils import import_mobile_cases_csv, import_trello_comments

logger = logging.getLogger(__name__)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class PlatformCheckingView(StaffRequiredMixin, FormView):
    """Write log message"""

    form_class = PlatformCheckingForm
    template_name: str = "tech/platform_checking.html"
    success_url: str = reverse_lazy("tech:platform-checking")

    def form_valid(self, form):
        if "trigger_400" in self.request.POST:
            raise BadRequest
        if "trigger_403" in self.request.POST:
            raise PermissionDenied
        if "trigger_500" in self.request.POST:
            1 / 0
        logger.log(
            level=int(form.cleaned_data["level"]), msg=form.cleaned_data["message"]
        )
        return super().form_valid(form)


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
        context["banner_case_detailed"] = context["detailed_case"]
        context["banner_case_mobile"] = MobileCase.objects.last()
        context["banner_case_archived"] = SimplifiedCase.objects.exclude(
            archive=""
        ).first()
        return context


class IssueReportListView(ListView):
    """View of list of issue reports"""

    model: type[IssueReport] = IssueReport
    template_name: str = "tech/issue_report_list.html"
    context_object_name: str = "issue_reports"
    paginate_by: int = 10


class ImportCSV(StaffRequiredMixin, FormView):
    """Reset obile Cases data from CSV"""

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
