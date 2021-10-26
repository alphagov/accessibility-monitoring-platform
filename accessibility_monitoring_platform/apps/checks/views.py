"""
Views for checks app (called tests by users)
"""
from functools import partial
from typing import Any, Dict, List, Type

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import CheckCreateForm, CheckUpdateMetadataForm, CheckUpdatePagesForm
from .models import Check, Page, EXEMPTION_DEFAULT, PAGE_TYPE_DEFAULT, MANDATORY_PAGE_TYPES

from ..cases.models import Case
from ..common.utils import (  # type: ignore
    FieldLabelAndValue,
    record_model_update_event,
    record_model_create_event,
)
from .utils import extract_labels_and_values


class CheckUpdateView(UpdateView):
    """
    View to update check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of check"""
        if form.changed_data:
            self.object: Check = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class CheckCreateView(CreateView):
    """
    View to create a check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"
    form_class: Type[CheckCreateForm] = CheckCreateForm
    template_name: str = "checks/forms/create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        check: Check = form.save(commit=False)
        check.case = Case.objects.get(pk=self.kwargs["case_id"])
        return super().form_valid(form)

    def get_form(self):
        """Initialise form fields"""
        form = super().get_form()
        form.fields["is_exemption"].initial = EXEMPTION_DEFAULT
        form.fields["type"].initial = PAGE_TYPE_DEFAULT
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        record_model_create_event(user=self.request.user, model_object=self.object)  # type: ignore
        for page_type in MANDATORY_PAGE_TYPES:
            Page.objects.create(parent_check=self.object, type=page_type)  # type: ignore
        if "save_continue" in self.request.POST:
            url = reverse_lazy(
                "checks:edit-check-metadata",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        else:
            url = reverse_lazy("cases:edit-test-results", kwargs={"pk": self.object.case.id})  # type: ignore
        return url

class CheckDetailView(DetailView):
    """
    View of details of a single check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        get_rows: Callable = partial(extract_labels_and_values, check=self.object)  # type: ignore

        check_metadata_rows: List[FieldLabelAndValue] = get_rows(
            form=CheckUpdateMetadataForm()
        )
        check_metadata_rows.insert(
            1,
            FieldLabelAndValue(
                label="Auditor",
                value=self.object.case.auditor,  # type: ignore
            ),
        )

        context["check_metadata_rows"] = check_metadata_rows
        context["pages"] = self.object.page_check.filter(is_deleted=False)  # type: ignore
        return context


class CheckMetadataUpdateView(CheckUpdateView):
    """
    View to update check metadata
    """

    form_class: Type[CheckUpdateMetadataForm] = CheckUpdateMetadataForm
    template_name: str = "checks/forms/metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url = reverse_lazy(
                "checks:edit-check-pages",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        else:
            url = reverse_lazy(
                "checks:check-detail",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                }
            )
        return url


class CheckPagesUpdateView(CheckUpdateView):
    """
    View to update check pages
    """

    form_class: Type[CheckUpdatePagesForm] = CheckUpdatePagesForm
    template_name: str = "checks/forms/pages.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url = reverse_lazy(
                "checks:edit-check-pages",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        else:
            url = reverse_lazy(
                "checks:check-detail",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                }
            )
        return url


def delete_check(request: HttpRequest, case_id: int, pk: int) -> HttpResponse:
    """
    Delete check

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of case
        pk (int): Id of check to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    check: Check = get_object_or_404(Check, id=pk)
    check.is_deleted = True
    check.save()
    return redirect(reverse_lazy("cases:edit-test-results", kwargs={"pk": case_id}))  # type: ignore


def restore_check(request: HttpRequest, case_id: int, pk: int) -> HttpResponse:
    """
    Restore deleted check

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of case
        pk (int): Id of check to restore

    Returns:
        HttpResponse: Django HttpResponse
    """
    check: Check = get_object_or_404(Check, id=pk)
    check.is_deleted = False
    check.save()
    return redirect(reverse_lazy("checks:check-detail", kwargs={"case_id": case_id, "pk": check.id}))  # type: ignore
