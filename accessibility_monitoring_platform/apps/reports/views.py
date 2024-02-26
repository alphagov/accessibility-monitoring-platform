"""
Views for reports app
"""

from typing import Any, Dict, List, Type

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Template, loader
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView

from ..cases.models import Case, CaseEvent
from ..common.utils import record_model_create_event, record_model_update_event
from .forms import ReportNotesUpdateForm, ReportWrapperUpdateForm
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
    case: Case = get_object_or_404(Case, id=case_id)
    if case.report:
        return redirect(
            reverse("reports:report-publisher", kwargs={"pk": case.report.id})
        )
    if case.audit is not None and not case.audit.uses_statement_checks:
        report: Report = Report.objects.create(
            case=case, report_version="v1_1_0__20230421"
        )
    else:
        report: Report = Report.objects.create(case=case)
    record_model_create_event(user=request.user, model_object=report)
    CaseEvent.objects.create(
        case=case,
        done_by=request.user,
        event_type=CaseEvent.EventType.CREATE_REPORT,
        message="Created report",
    )
    return redirect(reverse("reports:report-publisher", kwargs={"pk": report.id}))


class ReportUpdateView(UpdateView):
    """
    View to update report
    """

    model: Type[Report] = Report
    context_object_name: str = "report"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of report"""
        if form.changed_data:
            self.object: Report = form.save(commit=False)
            self.object.created_by = self.request.user
            record_model_update_event(user=self.request.user, model_object=self.object)
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class ReportNotesUpdateView(ReportUpdateView):
    """
    View to update report notes
    """

    form_class: Type[ReportNotesUpdateForm] = ReportNotesUpdateForm
    template_name: str = "reports/forms/metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            report_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("reports:report-publisher", kwargs=report_pk)
        return super().get_success_url()


class ReportTemplateView(TemplateView):
    """
    View to for template with report in context
    """

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(*args, **kwargs)
        context["report"] = get_object_or_404(Report, id=kwargs.get("pk"))
        return context


class ReportPublisherTemplateView(ReportTemplateView):
    """
    View to preview the report
    """

    template_name: str = "reports/report_publisher.html"

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(*args, **kwargs)
        report: Report = context["report"]
        template: Template = loader.get_template(report.template_path)
        context.update(get_report_visits_metrics(report.case))

        context["s3_report"] = report.latest_s3_report
        report_context: Dict[str, Any] = build_report_context(report=report)
        context.update(report_context)
        context["html_report"] = template.render(report_context, self.request)
        return context


class ReportConfirmPublishTemplateView(ReportTemplateView):
    """
    View to confirm publishing the report
    """

    template_name: str = "reports/report_confirm_publish.html"


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
    return redirect(reverse("reports:report-publisher", kwargs={"pk": report.id}))


class ReportWrapperUpdateView(UpdateView):
    """
    View to update report wrapper
    """

    form_class: Type[ReportWrapperUpdateForm] = ReportWrapperUpdateForm
    template_name: str = "reports/forms/wrapper.html"
    context_object_name: str = "report_wrapper"
    success_url: str = reverse_lazy("dashboard:home")

    def get_object(self, queryset=None):  # pylint: disable=unused-argument
        """Return report wrapper object"""
        return ReportWrapper.objects.all().first()


class ReportVisitsMetricsView(ReportTemplateView):
    """
    View of list of published reports
    """

    template_name: str = "reports/report_visits_metrics.html"

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(*args, **kwargs)
        context["showing"] = self.request.GET.get("showing")
        context["userhash"] = self.request.GET.get("userhash")

        if context["userhash"]:
            context["visit_logs"] = ReportVisitsMetrics.objects.filter(
                case=context["report"].case,
                fingerprint_codename=context["userhash"],
            )
        elif context["showing"] == "unique-visitors":
            visit_logs: List[Any] = []
            disinct_values: QuerySet = (
                ReportVisitsMetrics.objects.filter(case=context["report"].case)
                .values("fingerprint_hash")
                .distinct()
            )
            for query_set in disinct_values:
                visit_logs.append(
                    ReportVisitsMetrics.objects.filter(
                        fingerprint_hash=query_set["fingerprint_hash"]
                    ).first()
                )
            visit_logs.sort(reverse=True, key=lambda x: x.id)
            context["visit_logs"] = visit_logs
        else:
            context["visit_logs"] = ReportVisitsMetrics.objects.filter(
                case=context["report"].case
            )

        return context
