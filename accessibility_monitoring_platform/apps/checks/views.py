"""
Views for checks app (called tests by users)
"""
from functools import partial
from typing import Any, Dict, List, Type, Union

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView

from .forms import (
    CheckCreateForm,
    CheckUpdateMetadataForm,
    CheckUpdatePagesForm,
    CheckStandardPageFormset,
    CheckExtraPageFormset,
    CheckExtraPageFormsetOneExtra,
)
from .models import (
    Check,
    Page,
    EXEMPTION_DEFAULT,
    PAGE_TYPE_EXTRA,
    MANDATORY_PAGE_TYPES,
)

from ..cases.models import Case
from ..common.utils import (  # type: ignore
    FieldLabelAndValue,
    get_id_from_button_name,
    record_model_update_event,
    record_model_create_event,
)
from .utils import extract_labels_and_values

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


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
        form: ModelForm[Check] = super().get_form()  # type: ignore
        form.fields["is_exemption"].initial = EXEMPTION_DEFAULT
        form.fields["type"].initial = PAGE_TYPE_EXTRA
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
        context["standard_pages"] = self.object.page_check.filter(is_deleted=False).exclude(type=PAGE_TYPE_EXTRA)  # type: ignore
        context["extra_pages"] = self.object.page_check.filter(is_deleted=False, type=PAGE_TYPE_EXTRA)  # type: ignore
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
            url: str = reverse_lazy(
                "checks:edit-check-pages",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        else:
            url: str = f"""{reverse_lazy("checks:check-detail", kwargs={"pk": self.object.id, "case_id": self.object.case.id})}"""  # type: ignore
        return url


class CheckPagesUpdateView(CheckUpdateView):
    """
    View to update check pages
    """

    form_class: Type[CheckUpdatePagesForm] = CheckUpdatePagesForm
    template_name: str = "checks/forms/pages.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            standard_pages_formset: CheckStandardPageFormset = CheckStandardPageFormset(
                self.request.POST, prefix="standard"
            )
            extra_pages_formset: CheckExtraPageFormset = CheckExtraPageFormset(
                self.request.POST, prefix="extra"
            )
        else:
            standard_pages: QuerySet[Page] = self.object.page_check.exclude(  # type: ignore
                type=PAGE_TYPE_EXTRA
            )
            extra_pages: QuerySet[Page] = self.object.page_check.filter(  # type: ignore
                is_deleted=False, type=PAGE_TYPE_EXTRA
            )

            standard_pages_formset: CheckStandardPageFormset = CheckStandardPageFormset(
                queryset=standard_pages, prefix="standard"
            )
            if "add_extra" in self.request.GET:
                extra_pages_formset: CheckExtraPageFormsetOneExtra = (
                    CheckExtraPageFormsetOneExtra(queryset=extra_pages, prefix="extra")
                )
            else:
                extra_pages_formset: CheckExtraPageFormset = CheckExtraPageFormset(
                    queryset=extra_pages, prefix="extra"
                )
        context["standard_pages_formset"] = standard_pages_formset
        context["extra_pages_formset"] = extra_pages_formset
        context["standard_page_headers"] = STANDARD_PAGE_HEADERS
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        standard_pages_formset: CheckStandardPageFormset = context[
            "standard_pages_formset"
        ]
        extra_pages_formset: CheckExtraPageFormset = context["extra_pages_formset"]
        check: Check = form.save()

        if standard_pages_formset.is_valid():
            pages: List[Page] = standard_pages_formset.save(commit=False)
            for page in pages:
                record_model_update_event(user=self.request.user, model_object=page)  # type: ignore
                page.save()
        else:
            return super().form_invalid(form)

        if extra_pages_formset.is_valid():
            pages: List[Page] = extra_pages_formset.save(commit=False)
            for page in pages:
                if not page.parent_check_id:  # type: ignore
                    page.parent_check = check
                    page.save()
                    record_model_create_event(user=self.request.user, model_object=page)  # type: ignore
                else:
                    record_model_update_event(user=self.request.user, model_object=page)  # type: ignore
                    page.save()
        else:
            return super().form_invalid(form)

        page_id_to_delete: Union[int, None] = get_id_from_button_name(
            button_name_prefix="remove_extra_page_",
            querydict=self.request.POST,
        )
        if page_id_to_delete is not None:
            page_to_delete: Page = Page.objects.get(id=page_id_to_delete)
            page_to_delete.is_deleted = True
            record_model_update_event(user=self.request.user, model_object=page_to_delete)  # type: ignore
            page_to_delete.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            url: str = f"""{reverse_lazy("checks:check-detail", kwargs={"pk": self.object.id, "case_id": self.object.case.id})}#check-pages"""  # type: ignore
        elif "save_continue" in self.request.POST:
            url = reverse_lazy(
                "checks:edit-check-pages",
                kwargs={
                    "pk": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        else:
            url: str = f"{reverse_lazy('checks:edit-check-pages', kwargs={'pk': self.object.id, 'case_id': self.object.case.id})}?add_extra=true"  # type: ignore
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
