"""
Views for reports app
"""
from typing import Any, Dict, List, Optional, Type

from django import forms
from django.contrib import messages
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.template import loader, Template
from django.utils.safestring import mark_safe

from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import (
    ReportMetadataUpdateForm,
    SectionUpdateForm,
    TableRowFormset,
    TableRowFormsetOneExtra,
    ReportWrapperUpdateForm,
)
from .models import Report, Section, TableRow, ReportWrapper, ReportVisitsMetrics
from .utils import (
    check_for_buttons_by_name,
    generate_report_content,
    get_report_visits_metrics,
)
from ..common.utils import (
    record_model_create_event,
    record_model_update_event,
)
from ..cases.models import Case
from ..s3_read_write.utils import S3ReadWriteReport
from ..s3_read_write.models import S3Report


def create_report(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create report

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: Case = get_object_or_404(Case, id=case_id)
    report: Report = Report.objects.create(case=case)
    record_model_create_event(user=request.user, model_object=report)  # type: ignore
    generate_report_content(report=report)
    return redirect(reverse("reports:report-publisher", kwargs={"pk": report.id}))  # type: ignore


def rebuild_report(
    request: HttpRequest, pk: int  # pylint: disable=unused-argument
) -> HttpResponse:
    """
    Rebuild report

    Args:
        request (HttpRequest): Django HttpRequest
        id (int): Id of report

    Returns:
        HttpResponse: Django HttpResponse
    """
    report: Report = get_object_or_404(Report, id=pk)
    generate_report_content(report=report)
    return redirect(reverse("reports:report-detail", kwargs={"pk": pk}))


class ReportDetailView(DetailView):
    """
    View of details of a single report
    """

    model: Type[Report] = Report
    context_object_name: str = "report"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context.update(get_report_visits_metrics(self.object.case))
        return context


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
            record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class ReportMetadataUpdateView(ReportUpdateView):
    """
    View to update report metadata
    """

    form_class: Type[ReportMetadataUpdateForm] = ReportMetadataUpdateForm
    template_name: str = "reports/forms/metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            report_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("reports:report-detail", kwargs=report_pk)
        return super().get_success_url()


class SectionUpdateView(ReportUpdateView):
    """
    View to update report metadata
    """

    model: Type[Section] = Section
    context_object_name: str = "section"
    form_class: Type[SectionUpdateForm] = SectionUpdateForm
    template_name: str = "reports/forms/section.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        section: Section = self.object  # type: ignore

        if section.has_table:
            if self.request.POST:
                table_rows_formset: TableRowFormset = TableRowFormset(self.request.POST)
            else:
                if "add_row" in self.request.GET:
                    table_rows_formset: TableRowFormsetOneExtra = (
                        TableRowFormsetOneExtra(
                            queryset=section.tablerow_set.all(),  # type: ignore
                        )
                    )
                else:
                    table_rows_formset: TableRowFormset = TableRowFormset(
                        queryset=section.tablerow_set.all(),  # type: ignore
                    )

            for form in table_rows_formset.forms:
                if form.instance.is_deleted:
                    form.fields["cell_content_1"].widget = forms.HiddenInput()
                    form.fields["cell_content_2"].widget = forms.HiddenInput()

            context["table_rows_formset"] = table_rows_formset
        return context

    def get_form(self):
        """Populate help text with dates"""
        form = super().get_form()
        section: Section = self.object  # type: ignore
        if section.has_table:
            form.fields["content"].widget = forms.Textarea(
                attrs={"class": "govuk-textarea", "rows": "7"}
            )
        return form

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        section: Section = form.save(commit=False)

        if section.has_table:
            table_rows_formset: TableRowFormset = context["table_rows_formset"]
            if table_rows_formset.is_valid():
                table_rows: List[TableRow] = table_rows_formset.save(commit=False)
                for table_row in table_rows:
                    if not table_row.section_id:  # type: ignore
                        table_row.section = section
                        table_row.row_number = section.tablerow_set.count() + 1  # type: ignore
                        table_row.save()
                        record_model_create_event(user=self.request.user, model_object=table_row)  # type: ignore
                    else:
                        record_model_update_event(user=self.request.user, model_object=table_row)  # type: ignore
                        table_row.save()
            else:
                return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        section: Section = self.object  # type: ignore
        if section.has_table:
            updated_table_row_id: Optional[int] = check_for_buttons_by_name(
                request=self.request, section=section
            )
            if updated_table_row_id is not None:
                return f"{self.request.path}#row-{updated_table_row_id}"
        if "save_exit" in self.request.POST:
            report_pk: Dict[str, int] = {"pk": self.object.report.id}  # type: ignore
            return reverse("reports:report-detail", kwargs=report_pk)
        if "add_row" in self.request.POST:
            section_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            url: str = reverse("reports:edit-report-section", kwargs=section_pk)
            url: str = f"{url}?add_row=true#row-None"
            return url
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
        context["s3_report"] = report.latest_s3_report
        context["html_report"] = template.render(context, self.request)  # type: ignore
        return context


class ReportConfirmRefreshTemplateView(ReportTemplateView):
    """
    View to confirm refreshing the report
    """

    template_name: str = "reports/report_confirm_refresh.html"


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
    template: Template = loader.get_template(
        f"""reports_common/accessibility_report_{report.report_version}.html"""
    )
    context = {"report": report}
    html: str = template.render(context, request)  # type: ignore
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=report.case,
        user=request.user,  # type: ignore
        report_version=report.report_version,
    )
    messages.add_message(
        request,
        messages.INFO,
        mark_safe("HTML report successfully created!" ""),
    )
    return redirect(
        reverse("reports:report-publisher", kwargs={"pk": report.id})  # type: ignore
    )


class S3ReportListView(ListView):
    """
    View of list of published reports
    """

    model: Type[S3Report] = S3Report
    template_name: str = "reports/s3report_list.html"
    context_object_name: str = "s3_reports"

    def get_queryset(self) -> QuerySet[S3Report]:
        """Find S3 reports for case"""
        report: Report = Report.objects.get(id=self.kwargs.get("pk"))
        return S3Report.objects.filter(case=report.case).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report: Report = Report.objects.get(id=self.kwargs.get("pk"))
        context["report"] = report
        return context


class ReportWrapperUpdateView(UpdateView):
    """
    View to update report wrapper
    """

    form_class: Type[ReportWrapperUpdateForm] = ReportWrapperUpdateForm
    template_name: str = "reports/forms/wrapper.html"
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
            context["visit_logs"] = visit_logs
        else:
            context["visit_logs"] = ReportVisitsMetrics.objects.filter(
                case=context["report"].case
            )

        return context
