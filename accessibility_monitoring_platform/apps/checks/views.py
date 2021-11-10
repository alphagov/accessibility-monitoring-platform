"""
Views for checks app (called tests by users)
"""
from functools import partial
from typing import Any, Callable, Dict, List, Type, Union

from django.forms.models import ModelForm
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView

from ..cases.models import Case
from ..common.utils import (
    FieldLabelAndValue,
    get_id_from_button_name,
    record_model_update_event,
    record_model_create_event,
)

from .forms import (
    CheckCreateForm,
    CheckUpdateMetadataForm,
    CheckUpdatePagesForm,
    CheckStandardPageFormset,
    CheckExtraPageFormset,
    CheckExtraPageFormsetOneExtra,
    CheckUpdateManualForm,
    CheckUpdateAxeForm,
    CheckUpdatePdfForm,
    CheckTestUpdateFormset,
)
from .models import (
    Check,
    Page,
    CheckTest,
    TEST_TYPE_MANUAL,
    TEST_TYPE_PDF,
    EXEMPTION_DEFAULT,
    PAGE_TYPE_EXTRA,
)
from .utils import create_pages_and_tests_for_new_check, extract_labels_and_values

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


def get_check_url(url_name: str, check: Check) -> str:
    """Return url string for name and check"""
    return reverse_lazy(
        f"checks:{url_name}",
        kwargs={
            "pk": check.id,  # type: ignore
            "case_id": check.case.id,  # type: ignore
        },
    )


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
        create_pages_and_tests_for_new_check(parent_check=self.object, user=self.request.user)  # type: ignore
        if "save_continue" in self.request.POST:
            url: str = get_check_url(url_name="edit-check-metadata", check=self.object)  # type: ignore
        else:
            url: str = reverse_lazy("cases:edit-test-results", kwargs={"pk": self.object.case.id})  # type: ignore
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
        if self.object.case.auditor:  # type: ignore
            check_metadata_rows.insert(
                1,
                FieldLabelAndValue(
                    label="Auditor",
                    value=self.object.case.auditor.get_full_name(),  # type: ignore
                ),
            )

        context["check_metadata_rows"] = check_metadata_rows
        context["standard_pages"] = self.object.page_check.filter(is_deleted=False).exclude(type=PAGE_TYPE_EXTRA)  # type: ignore
        context["extra_pages"] = self.object.page_check.filter(is_deleted=False, type=PAGE_TYPE_EXTRA)  # type: ignore

        pdf_check_tests: QuerySet[CheckTest] = CheckTest.objects.filter(parent_check=self.object, type=TEST_TYPE_PDF, failed="yes")  # type: ignore
        context["check_pdf_rows"] = [
            FieldLabelAndValue(label=check_test.wcag_test.name, value=check_test.notes)
            for check_test in pdf_check_tests
        ]

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
            url: str = get_check_url(url_name="edit-check-pages", check=self.object)  # type: ignore
        else:
            url: str = f'{get_check_url(url_name="check-detail", check=self.object)}#check-metadata'  # type: ignore
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
            url: str = f'{get_check_url(url_name="check-detail", check=self.object)}#check-pages'  # type: ignore
        elif "save_continue" in self.request.POST:
            url: str = get_check_url(url_name="edit-check-manual", check=self.object)  # type: ignore
        elif "add_extra" in self.request.POST:
            url: str = f'{get_check_url(url_name="edit-check-pages", check=self.object)}?add_extra=true'  # type: ignore
        else:
            url: str = get_check_url(url_name="edit-check-pages", check=self.object)  # type: ignore
        return url


class CheckManualUpdateView(CheckUpdateView):
    """
    View to update manual checks
    """

    form_class: Type[CheckUpdateManualForm] = CheckUpdateManualForm
    template_name: str = "checks/forms/manual.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            check_tests_formset: CheckTestUpdateFormset = CheckTestUpdateFormset(
                self.request.POST
            )
        else:
            check_tests: QuerySet[CheckTest] = self.object.test_check.filter(  # type: ignore
                type=TEST_TYPE_MANUAL
            )

            check_tests_formset: CheckTestUpdateFormset = CheckTestUpdateFormset(
                queryset=check_tests
            )
        for check_tests_form in check_tests_formset.forms:
            check_tests_form.fields["failed"].label = ""
            check_tests_form.fields["failed"].widget.attrs = {
                "label": check_tests_form.instance.wcag_test.name
            }
        context["check_tests_formset"] = check_tests_formset
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_check_url(url_name="edit-check-axe", check=self.object)  # type: ignore
        else:
            url: str = f'{get_check_url(url_name="check-detail", check=self.object)}#check-manual'  # type: ignore
        return url


class CheckAxeUpdateView(CheckUpdateView):
    """
    View to update axe checks
    """

    form_class: Type[CheckUpdateAxeForm] = CheckUpdateAxeForm
    template_name: str = "checks/forms/axe.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_check_url(url_name="edit-check-pdf", check=self.object)  # type: ignore
        else:
            url: str = f'{get_check_url(url_name="check-detail", check=self.object)}#check-axe'  # type: ignore
        return url


class CheckPdfUpdateView(CheckUpdateView):
    """
    View to update pdf checks
    """

    form_class: Type[CheckUpdatePdfForm] = CheckUpdatePdfForm
    template_name: str = "checks/forms/pdf.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            check_tests_formset: CheckTestUpdateFormset = CheckTestUpdateFormset(
                self.request.POST
            )
        else:
            check_tests: QuerySet[CheckTest] = self.object.test_check.filter(  # type: ignore
                type=TEST_TYPE_PDF
            )

            check_tests_formset: CheckTestUpdateFormset = CheckTestUpdateFormset(
                queryset=check_tests
            )
        for check_tests_form in check_tests_formset.forms:
            check_tests_form.fields["failed"].label = ""
            check_tests_form.fields["failed"].widget.attrs = {
                "label": check_tests_form.instance.wcag_test.name
            }
            check_tests_form.fields["notes"].label = ""
        context["check_tests_formset"] = check_tests_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        check_tests_formset: CheckTestUpdateFormset = context["check_tests_formset"]

        if check_tests_formset.is_valid():
            check_tests: List[Page] = check_tests_formset.save(commit=False)
            for check_test in check_tests:
                record_model_update_event(user=self.request.user, model_object=check_test)  # type: ignore
                check_test.save()
        else:
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_check_url(url_name="edit-check-pdf", check=self.object)  # type: ignore
        else:
            url: str = f'{get_check_url(url_name="check-detail", check=self.object)}#check-pdf'  # type: ignore
        return url
