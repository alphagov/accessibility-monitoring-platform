"""
Views for export app
"""

from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..common.views import HideCaseNavigationMixin
from ..simplified.models import SimplifiedCase
from ..simplified.utils import record_model_create_event, record_model_update_event
from .csv_export_utils import (
    download_equality_body_cases,
    populate_equality_body_columns,
)
from .forms import ExportConfirmForm, ExportCreateForm, ExportDeleteForm
from .models import Export, ExportCase


class EnforcementBodyMixin:
    """Mixin to get enforcement body from request"""

    enforcement_body: str = SimplifiedCase.EnforcementBody.EHRC

    def get(self, request, *args, **kwargs):
        """Get enforcement body"""
        self.enforcement_body = self.request.GET.get(
            "enforcement_body", SimplifiedCase.EnforcementBody.EHRC
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["enforcement_body"] = self.enforcement_body
        return context


class ExportListView(EnforcementBodyMixin, ListView):
    """
    View to list exports
    """

    model: type[Export] = Export
    context_object_name: str = "exports"
    template_name: str = "exports/export_list.html"

    def get_queryset(self) -> QuerySet[Export]:
        return Export.objects.filter(
            is_deleted=False, enforcement_body=self.enforcement_body
        )


class ExportCreateView(EnforcementBodyMixin, CreateView):
    """
    View to create an export
    """

    model: type[Export] = Export
    form_class: type[ExportCreateForm] = ExportCreateForm
    context_object_name: str = "export"
    template_name: str = "exports/export_create.html"

    def get_form(self):
        """Populate next page select field"""
        form = super().get_form()
        self.enforcement_body = self.request.GET.get(
            "enforcement_body", SimplifiedCase.EnforcementBody.EHRC
        )
        form.fields["enforcement_body"].initial = self.enforcement_body
        return form

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

    model: type[Export] = Export
    context_object_name: str = "export"


class ExportCaseAsEmailDetailView(HideCaseNavigationMixin, DetailView):
    """
    View of details of a Case for export as an email
    """

    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "exports/export_case_as_email.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["export_columns"] = populate_equality_body_columns(case=self.object)
        context["export"] = get_object_or_404(Export, pk=self.kwargs["export_id"])
        return context


class ConfirmExportUpdateView(UpdateView):
    """
    View to update each case to say it was sent to equality body.
    Redirect to export ready cases.
    """

    model: type[Export] = Export
    form_class: type[ExportConfirmForm] = ExportConfirmForm
    context_object_name: str = "export"
    template_name: str = "exports/export_confirm_export.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Bulk update ready export cases; Redirect to export"""
        export: Export = self.object
        today: date = date.today()
        user: User = self.request.user
        for case in export.ready_cases:
            case.sent_to_enforcement_body_sent_date = today
            record_model_update_event(user=user, model_object=case, case=case)
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

    model: type[Export] = Export
    form_class: type[ExportDeleteForm] = ExportDeleteForm
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
        return f'{reverse("exports:export-list")}?enforcement_body={self.object.enforcement_body}'


def export_all_cases(request: HttpRequest, pk: int) -> HttpResponse:
    """View to export all cases"""
    export: Export = get_object_or_404(Export, id=pk)
    return download_equality_body_cases(
        cases=export.all_cases,
        filename=f"DRAFT_{export.enforcement_body.upper()}_cases_{export.cutoff_date}.csv",
    )


def export_ready_cases(request: HttpRequest, pk: int) -> HttpResponse:
    """View to export only ready cases."""
    export: Export = get_object_or_404(Export, pk=pk)
    return download_equality_body_cases(
        cases=export.ready_cases,
        filename=f"{export.enforcement_body.upper()}_cases_{export.cutoff_date}.csv",
    )


def mark_all_export_cases_as_ready(
    request: HttpRequest, pk: int
) -> HttpResponseRedirect:
    """Mark all the cases in an export as ready"""
    export: Export = get_object_or_404(Export, id=pk)
    for export_case in export.exportcase_set.all():
        export_case.status = ExportCase.Status.READY
        export_case.save()
    return redirect(reverse("exports:export-detail", kwargs={"pk": export.id}))


def mark_export_case_as_ready(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark export as ready"""
    export_case: ExportCase = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.READY
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )


def mark_export_case_as_unready(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark export as unready"""
    export_case: Export = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.UNREADY
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )


def mark_export_case_as_excluded(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark export as excluded"""
    export_case: Export = get_object_or_404(ExportCase, id=pk)
    export_case.status = ExportCase.Status.EXCLUDED
    export_case.save()
    return redirect(
        f'{reverse("exports:export-detail", kwargs={"pk": export_case.export.id})}#export-case-{export_case.id}'
    )
