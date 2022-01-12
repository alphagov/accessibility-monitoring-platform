"""
Views for audits app (called tests by users)
"""
from functools import partial
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from django.db.models import QuerySet
from django import forms
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.detail import DetailView

from ..cases.models import Case
from ..common.utils import (
    record_model_update_event,
    record_model_create_event,
    list_to_dictionary_of_lists,
)
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
)

from .forms import (
    AuditCreateForm,
    AuditMetadataUpdateForm,
    AuditWebsiteUpdateForm,
    AuditPageForm,
    AuditPageChecksForm,
    CheckResultFilterForm,
    CheckResultForm,
    CheckResultFormset,
    AuditStatement1UpdateForm,
    AuditStatement2UpdateForm,
    AuditSummaryUpdateForm,
    AuditReportOptionsUpdateForm,
    AuditReportTextUpdateForm,
)
from .models import (
    Audit,
    Page,
    AUDIT_TYPE_DEFAULT,
    PAGE_TYPE_ALL,
    WcagDefinition,
)
from .utils import (
    create_or_update_check_results_for_page,
    copy_all_pages_check_results,
    get_all_possible_check_results_for_page,
    get_audit_metadata_rows,
    get_audit_statement_rows,
    get_audit_report_options_rows,
)

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


def delete_audit(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Delete audit

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of audit to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.is_deleted = True
    record_model_update_event(user=request.user, model_object=audit)  # type: ignore
    audit.save()
    return redirect(reverse("cases:edit-test-results", kwargs={"pk": audit.case.id}))  # type: ignore


def restore_audit(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Restore deleted audit

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of audit to restore

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.is_deleted = False
    record_model_update_event(user=request.user, model_object=audit)  # type: ignore
    audit.save()
    return redirect(reverse("audits:audit-detail", kwargs={"pk": audit.id}))  # type: ignore


def delete_page(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Delete page

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of page to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    page: Page = get_object_or_404(Page, id=pk)
    page.is_deleted = True
    record_model_update_event(user=request.user, model_object=page)  # type: ignore
    page.save()
    return redirect(reverse("audits:edit-audit-website", kwargs={"pk": page.audit.id}))  # type: ignore


def restore_page(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Restore deleted page

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of page to restore

    Returns:
        HttpResponse: Django HttpResponse
    """
    page: Page = get_object_or_404(Page, id=pk)
    page.is_deleted = False
    record_model_update_event(user=request.user, model_object=page)  # type: ignore
    page.save()
    return redirect(reverse("audits:edit-audit-website", kwargs={"pk": page.audit.id}))  # type: ignore


class AuditCreateView(CreateView):
    """
    View to create a audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"
    form_class: Type[AuditCreateForm] = AuditCreateForm
    template_name: str = "audits/forms/create.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add table rows to context for each section of page"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        case: Case = Case.objects.get(pk=self.kwargs["case_id"])
        page_heading: str = "Edit case | Create test"
        page_title: str = f"{case.organisation_name} | {page_heading}"

        context["case"] = case
        context["page_heading"] = page_heading
        context["page_title"] = page_title

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        audit: Audit = form.save(commit=False)
        audit.case = Case.objects.get(pk=self.kwargs["case_id"])
        audit.save()
        Page.objects.create(
            audit=audit, page_type=PAGE_TYPE_ALL, name="All pages excluding PDF"
        )
        return super().form_valid(form)

    def get_form(self):
        """Initialise form fields"""
        form: ModelForm = super().get_form()  # type: ignore
        form.fields["type"].initial = AUDIT_TYPE_DEFAULT

        case: Case = Case.objects.get(pk=self.kwargs["case_id"])
        existing_audits: QuerySet[Audit] = Audit.objects.filter(case=case)
        form.fields["retest_of_audit"].queryset = existing_audits
        if not existing_audits:
            form.fields["retest_of_audit"].widget = forms.HiddenInput()  # type: ignore
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.object  # type: ignore
        record_model_create_event(user=self.request.user, model_object=audit)  # type: ignore
        url: str = reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id})  # type: ignore
        return url


class AuditDetailView(DetailView):
    """
    View of details of a single audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add table rows to context for each section of page"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object  # type: ignore

        context["audit_metadata_rows"] = get_audit_metadata_rows(audit)
        context["failed_check_results_by_page"] = list_to_dictionary_of_lists(
            items=audit.failed_check_results, group_by_attr="page"  # type: ignore
        )
        context["audit_statement_rows"] = get_audit_statement_rows(audit)
        context["audit_report_options_rows"] = get_audit_report_options_rows(audit)

        return context


class AuditUpdateView(UpdateView):
    """
    View to update audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of audit"""
        if form.changed_data:
            self.object: Audit = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class AuditMetadataUpdateView(AuditUpdateView):
    """
    View to update audit metadata
    """

    form_class: Type[AuditMetadataUpdateForm] = AuditMetadataUpdateForm
    template_name: str = "audits/forms/metadata.html"


class AuditWebsiteUpdateView(AuditUpdateView):
    """
    View to update audit website page
    """

    form_class: Type[AuditWebsiteUpdateForm] = AuditWebsiteUpdateForm
    template_name: str = "audits/forms/website.html"


class AuditPageCreateView(CreateView):
    """
    View to create a audit
    """

    model: Type[Page] = Page
    context_object_name: str = "page"
    form_class: Type[AuditPageForm] = AuditPageForm
    template_name: str = "audits/forms/page.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Include audit in context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["audit"] = Audit.objects.get(pk=self.kwargs["audit_id"])
        return context

    def form_valid(self, form: ModelForm):
        """Populate audit field of new Page"""
        page: Page = form.save(commit=False)
        page.audit = Audit.objects.get(pk=self.kwargs["audit_id"])
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Show website page of audit"""
        audit_pk: Dict[str, int] = {"pk": self.kwargs["audit_id"]}
        url: str = reverse("audits:edit-audit-website", kwargs=audit_pk)
        return url


class AuditPageUpdateView(UpdateView):
    """
    View to update audit page
    """

    model: Type[Page] = Page
    context_object_name: str = "page"
    form_class: Type[AuditPageForm] = AuditPageForm
    template_name: str = "audits/forms/page.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Include audit in context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["audit"] = self.object.audit  # type: ignore
        return context

    def get_success_url(self) -> str:
        """Show website page of audit"""
        page: Page = self.object  # type: ignore
        audit_pk: Dict[str, int] = {"pk": page.audit.id}
        url: str = reverse("audits:edit-audit-website", kwargs=audit_pk)
        return url


class AuditPageChecksFormView(FormView):
    """
    View to update check results for a page
    """

    form_class: Type[AuditPageChecksForm] = AuditPageChecksForm
    template_name: str = "audits/forms/page_checks.html"
    page: Page

    def setup(self, request, *args, **kwargs):
        """Add audit and page objects to view"""
        super().setup(request, *args, **kwargs)
        self.page = Page.objects.get(pk=kwargs["pk"])

    def get_form(self):
        """Populate next page select field"""
        form = super().get_form()
        form.fields["complete_date"].initial = self.page.complete_date
        return form

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["filter_form"] = CheckResultFilterForm(
            initial={"manual": False, "axe": False, "pdf": False, "not_tested": False}
        )
        wcag_definitions: List[WcagDefinition] = list(WcagDefinition.objects.all())

        if self.request.POST:
            check_results_formset: CheckResultFormset = CheckResultFormset(
                self.request.POST
            )
        else:

            check_results_formset: CheckResultFormset = CheckResultFormset(
                initial=get_all_possible_check_results_for_page(
                    page=self.page, wcag_definitions=wcag_definitions
                )
            )
        wcag_definitions_and_forms: List[Tuple[WcagDefinition, CheckResultForm]] = []
        for count, check_results_form in enumerate(check_results_formset.forms):
            wcag_definition: WcagDefinition = wcag_definitions[count]
            check_results_form.fields["check_result_state"].label = wcag_definition
            wcag_definitions_and_forms.append((wcag_definition, check_results_form))

        context["check_results_formset"] = check_results_formset
        context["wcag_definitions_and_forms"] = wcag_definitions_and_forms

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        page: Page = self.page
        page.complete_date = form.cleaned_data["complete_date"]
        page.save()

        check_results_formset: CheckResultFormset = context["check_results_formset"]
        if check_results_formset.is_valid():
            create_or_update_check_results_for_page(
                user=self.request.user,  # type: ignore
                page=page,
                check_result_forms=check_results_formset.forms,
            )
        else:
            return super().form_invalid(form)

        if page.page_type == PAGE_TYPE_ALL:
            copy_all_pages_check_results(user=self.request.user, page=page)  # type: ignore

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class AuditStatement1UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 1 audit fields
    """

    form_class: Type[AuditStatement1UpdateForm] = AuditStatement1UpdateForm
    template_name: str = "audits/forms/statement-1.html"


class AuditStatement2UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 2 audit fields
    """

    form_class: Type[AuditStatement2UpdateForm] = AuditStatement2UpdateForm
    template_name: str = "audits/forms/statement-2.html"


class AuditSummaryUpdateView(AuditUpdateView):
    """
    View to update audit summary
    """

    form_class: Type[AuditSummaryUpdateForm] = AuditSummaryUpdateForm
    template_name: str = "audits/forms/summary.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object

        view_url_param: Union[str, None] = self.request.GET.get("view")
        show_failures_by_page: bool = view_url_param == "Page view"
        context["show_failures_by_page"] = show_failures_by_page

        if show_failures_by_page:
            context["audit_failures_by_page"] = list_to_dictionary_of_lists(
                items=audit.failed_check_results, group_by_attr="page"  # type: ignore
            )
        else:
            context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                items=audit.failed_check_results, group_by_attr="wcag_definition"  # type: ignore
            )

        get_rows: Callable = partial(extract_form_labels_and_values, instance=audit)
        context["audit_statement_rows"] = get_rows(
            form=AuditStatement1UpdateForm()  # type: ignore
        ) + get_rows(
            form=AuditStatement2UpdateForm()
        )  # type: ignore

        return context


class AuditReportOptionsUpdateView(AuditUpdateView):
    """
    View to update report options
    """

    form_class: Type[AuditReportOptionsUpdateForm] = AuditReportOptionsUpdateForm
    template_name: str = "audits/forms/report-options.html"


class AuditReportTextUpdateView(AuditUpdateView):
    """
    View to update report text
    """

    form_class: Type[AuditReportTextUpdateForm] = AuditReportTextUpdateForm
    template_name: str = "audits/forms/report-text.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["wcag_definitions"] = WcagDefinition.objects.all()
        return context
