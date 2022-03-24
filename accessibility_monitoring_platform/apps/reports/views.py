"""
Views for reports app
"""
from typing import Any, Dict, List, Optional, Type

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.forms.models import ModelForm
from django.shortcuts import redirect, get_object_or_404
from django.template import loader, Template
from django.utils.safestring import mark_safe

from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import (
    ReportMetadataUpdateForm,
    SectionUpdateForm,
    TableRowFormset,
    TableRowFormsetOneExtra,
)
from .models import Report, Section, TableRow, PublishedReport
from .utils import generate_report_content

from ..common.utils import (
    get_id_from_button_name,
    record_model_update_event,
)
from ..cases.models import Case

from ..common.utils import (
    record_model_create_event,
)


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
    return redirect(reverse("reports:report-detail", kwargs={"pk": report.id}))  # type: ignore


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

        if self.request.POST:
            table_rows_formset: TableRowFormset = TableRowFormset(self.request.POST)
        else:
            if "add_row" in self.request.GET:
                table_rows_formset: TableRowFormsetOneExtra = TableRowFormsetOneExtra(
                    queryset=section.table_rows,  # type: ignore
                )
            else:
                table_rows_formset: TableRowFormset = TableRowFormset(
                    queryset=section.table_rows,  # type: ignore
                )

        context["table_rows_formset"] = table_rows_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        table_rows_formset: TableRowFormset = context["table_rows_formset"]
        section: Section = form.save(commit=False)

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

        table_row_id_to_delete: Optional[int] = get_id_from_button_name(
            button_name_prefix="delete_table_row_",
            querydict=self.request.POST,
        )
        if table_row_id_to_delete is not None:
            table_row_to_delete: TableRow = TableRow.objects.get(id=table_row_id_to_delete)
            table_row_to_delete.is_deleted = True
            record_model_update_event(user=self.request.user, model_object=table_row_to_delete)  # type: ignore
            table_row_to_delete.save()

        table_row_id_to_undelete: Optional[int] = get_id_from_button_name(
            button_name_prefix="undelete_table_row_",
            querydict=self.request.POST,
        )
        if table_row_id_to_undelete is not None:
            table_row_to_undelete: TableRow = TableRow.objects.get(id=table_row_id_to_undelete)
            table_row_to_undelete.is_deleted = False
            record_model_update_event(user=self.request.user, model_object=table_row_to_undelete)  # type: ignore
            table_row_to_undelete.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            report_pk: Dict[str, int] = {"pk": self.object.report.id}  # type: ignore
            return reverse("reports:report-detail", kwargs=report_pk)
        if "add_row" in self.request.POST:
            section_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            url: str = reverse("reports:edit-report-section", kwargs=section_pk)
            url: str = f"{url}?add_row=true"
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


class ReportPreviewTemplateView(ReportTemplateView):
    """
    View to preview the report
    """

    template_name: str = "reports/report_preview.html"


class ReportConfirmRebuildTemplateView(ReportTemplateView):
    """
    View to confirm rebuilding the report
    """

    template_name: str = "reports/report_confirm_rebuild.html"


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
    template: Template = loader.get_template("reports/report_preview.html")
    context = {"report": report}
    html: str = template.render(context, request)
    PublishedReport.objects.create(
        report=report,
        created_by=request.user,
        html_content=html,
    )
    messages.add_message(
        request,
        messages.INFO,
        mark_safe("HTML report successfully created!" ""),
    )
    return redirect(
        reverse("reports:report-detail", kwargs={"pk": report.id})  # type: ignore
    )


class PublishedReportListView(ListView):
    """
    View of list of published reports
    """

    model: Type[PublishedReport] = PublishedReport
    context_object_name: str = "published_reports"


class PublishedReportDetailView(DetailView):
    """
    View of detail of a published report
    """

    model: Type[PublishedReport] = PublishedReport
    context_object_name: str = "published_report"
