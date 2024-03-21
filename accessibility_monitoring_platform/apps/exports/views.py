"""
Views for export app
"""

from datetime import date
from typing import Type

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..cases.utils import download_cases
from ..common.utils import record_model_create_event, record_model_update_event
from .forms import ExportConfirmForm, ExportCreateForm, ExportDeleteForm
from .models import Export, ExportCase


class ExportListView(ListView):
    """
    View to list exports
    """

    model: Type[Export] = Export
    context_object_name: str = "exports"
    template_name: str = "exports/export_list.html"

    def get_queryset(self) -> QuerySet[Export]:
        return Export.objects.filter(is_deleted=False)


class ExportCreateView(CreateView):
    """
    View to create an export
    """

    model: Type[Export] = Export
    form_class: Type[ExportCreateForm] = ExportCreateForm
    context_object_name: str = "export"
    template_name: str = "exports/export_create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        export: Export = form.save(commit=False)
        export.exporter = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        export: Export = self.object
        user: User = self.request.user
        record_model_create_event(user=user, model_object=export)
        return reverse("exports:export-detail", kwargs={"pk": export.id})


class ExportDetailView(DetailView):
    """
    View of details of a single export
    """

    model: Type[Export] = Export
    context_object_name: str = "export"


class ConfirmExportUpdateView(UpdateView):
    """
    View to update each case to say it was sent to equality body.
    Redirect to export ready cases.
    """

    model: Type[Export] = Export
    form_class: Type[ExportConfirmForm] = ExportConfirmForm
    context_object_name: str = "export"
    template_name: str = "exports/export_confirm_export.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Bulk update ready export cases; Redirect to export"""
        export: Export = self.object
        today: date = date.today()
        user: User = self.request.user
        for case in export.ready_cases:
            case.sent_to_enforcement_body_sent_date = today
            record_model_update_event(user=user, model_object=case)
            case.save()
        export.status = Export.Status.EXPORTED
        export.export_date = today
        record_model_update_event(user=user, model_object=export)
        export.save()
        return HttpResponseRedirect(
            reverse("exports:export-ready-cases", kwargs={"pk": export.id})
        )


class ExportConfirmDeleteUpdateView(UpdateView):
    """
    View to confirm deletion of export
    """

    model: Type[Export] = Export
    form_class: Type[ExportDeleteForm] = ExportDeleteForm
    context_object_name: str = "export"
    template_name: str = "exports/export_confirm_delete.html"

    def get_form(self):
        """Populate next page select field"""
        form = super().get_form()
        export: Export = self.object
        form.fields["is_deleted"].label = f"Are you sure you want to remove {export}?"
        return form

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        export: Export = form.save(commit=False)
        user: User = self.request.user
        record_model_update_event(user=user, model_object=export)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("exports:export-list")


def export_all_cases(request: HttpRequest, pk: int) -> HttpResponse:
    """View to export all cases"""
    export: Export = get_object_or_404(Export, id=pk)
    return download_cases(
        cases=export.all_cases, filename=f"DRAFT_EHRC_cases_{export.cutoff_date}.csv"
    )


def export_ready_cases(request: HttpRequest, pk: int) -> HttpResponse:
    """View to export only ready cases."""
    export: Export = get_object_or_404(Export, pk=pk)
    return download_cases(
        cases=export.ready_cases, filename=f"EHRC_cases_{export.cutoff_date}.csv"
    )


def mark_export_case_as_ready(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """View to export cases"""
    export_case: Export = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.READY
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )


def mark_export_case_as_unready(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """View to export cases"""
    export_case: Export = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.UNREADY
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )


def mark_export_case_as_excluded(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """View to export cases"""
    export_case: Export = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.EXCLUDED
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )
