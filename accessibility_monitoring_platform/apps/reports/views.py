"""
Views for reports app
"""

from typing import Any

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Template, loader
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from ..common.views import HideCaseNavigationMixin
from ..simplified.models import CaseEvent, SimplifiedCase
from ..simplified.utils import record_model_create_event, record_model_update_event
from .forms import ReportWrapperUpdateForm
from .models import Report, ReportVisitsMetrics, ReportWrapper
from .utils import build_report_context, get_report_visits_metrics, publish_report_util


def create_report(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create report. If one already exists use that instead.

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: SimplifiedCase = get_object_or_404(SimplifiedCase, id=case_id)
    if case.report:
        return redirect(
            reverse("simplified:edit-report-ready-for-qa", kwargs={"pk": case.id})
        )
    report: Report = Report.objects.create(base_case=case)
    record_model_create_event(user=request.user, model_object=report, case=case)
    CaseEvent.objects.create(
        simplified_case=case,
        done_by=request.user,
        event_type=CaseEvent.EventType.CREATE_REPORT,
        message="Created report",
    )
    return redirect(
        reverse("simplified:edit-report-ready-for-qa", kwargs={"pk": case.id})
    )


class ReportUpdateView(UpdateView):
    """
    View to update report
    """

    model: type[Report] = Report
    context_object_name: str = "report"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of report"""
        if form.changed_data:
            self.object: Report = form.save(commit=False)
            self.object.created_by = self.request.user
            record_model_update_event(
                user=self.request.user, model_object=self.object, case=self.object.case
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class ReportTemplateView(TemplateView):
    """
    View to for template with report in context
    """

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        context["report"] = get_object_or_404(Report, id=kwargs.get("pk"))
        return context


class ReportPreviewTemplateView(ReportTemplateView):
    """
    View to preview the report
    """

    template_name: str = "reports/report_preview.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        report: Report = context["report"]
        template: Template = loader.get_template(report.template_path)
        context.update(get_report_visits_metrics(report.base_case))

        context["s3_report"] = report.latest_s3_report
        report_context: dict[str, Any] = build_report_context(report=report)
        context.update(report_context)
        context["html_report"] = template.render(report_context, self.request)
        return context


class ReportRepublishTemplateView(DetailView):
    """
    View to republish the report
    """

    model: type[Report] = Report
    context_object_name: str = "report"
    template_name: str = "reports/report_republish.html"


def publish_report(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Publish report

    Args:
        request (HttpRequest): Django HttpRequest
        id (int): Id of report

    Returns:
        HttpResponse: Django HttpResponse
    """
    report: Report = get_object_or_404(Report, id=pk)
    publish_report_util(report=report, request=request)
    return redirect(
        reverse(
            "simplified:edit-publish-report",
            kwargs={"pk": report.base_case.simplifiedcase.id},
        )
    )


class ReportWrapperUpdateView(UpdateView):
    """
    View to update report wrapper
    """

    form_class: type[ReportWrapperUpdateForm] = ReportWrapperUpdateForm
    template_name: str = "reports/forms/wrapper.html"
    context_object_name: str = "report_wrapper"
    success_url: str = reverse_lazy("dashboard:home")

    def get_object(self, queryset=None):  # pylint: disable=unused-argument
        """Return report wrapper object"""
        return ReportWrapper.objects.all().first()


class ReportVisitsMetricsView(HideCaseNavigationMixin, ReportTemplateView):
    """
    View of list of published reports
    """

    template_name: str = "reports/report_visits_metrics.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        context["showing"] = self.request.GET.get("showing")
        context["userhash"] = self.request.GET.get("userhash")
        case: SimplifiedCase = context["report"].case

        if context["userhash"]:
            context["visit_logs"] = ReportVisitsMetrics.objects.filter(
                case=case,
                fingerprint_codename=context["userhash"],
            )
        elif context["showing"] == "unique-visitors":
            visit_logs: list[Any] = []
            disinct_values: QuerySet = (
                ReportVisitsMetrics.objects.filter(case=case)
                .values("fingerprint_hash")
                .distinct()
            )
            for query_set in disinct_values:
                visit_logs.append(
                    ReportVisitsMetrics.objects.filter(
                        case=case,
                        fingerprint_hash=query_set["fingerprint_hash"],
                    ).first()
                )
            visit_logs.sort(reverse=True, key=lambda x: x.id)
            context["visit_logs"] = visit_logs
        else:
            context["visit_logs"] = ReportVisitsMetrics.objects.filter(case=case)

        return context
