"""
Views for export app
"""

from typing import Type

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import ExportCreateForm
from .models import Export


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
        return reverse("exports:export-list")


class ExportDetailView(DetailView):
    """
    View of details of a single export
    """

    model: Type[Export] = Export
    context_object_name: str = "export"
