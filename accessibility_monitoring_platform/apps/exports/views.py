"""
Views for export app
"""

from typing import Type

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from ..cases.utils import download_cases
from ..common.utils import record_model_create_event
from .forms import ExportCreateForm
from .models import Export, ExportCase

# record_model_update_event,


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
    View to create ain export
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


def export_all_cases(request: HttpRequest, pk: int) -> HttpResponse:
    """View to export cases"""
    export: Export = get_object_or_404(Export, id=pk)
    return download_cases(cases=export.all_cases)


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
