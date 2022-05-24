"""
Views for audits app (called tests by users)
"""
from datetime import date
from functools import partial
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from ..cases.models import Case
from ..common.utils import (
    record_model_update_event,
    record_model_create_event,
    list_to_dictionary_of_lists,
    get_id_from_button_name,
)
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
)

from .forms import (
    AuditMetadataUpdateForm,
    AuditStandardPageFormset,
    AuditExtraPageFormset,
    AuditExtraPageFormsetOneExtra,
    AuditPagesUpdateForm,
    AuditPageChecksForm,
    CheckResultFilterForm,
    CheckResultForm,
    CheckResultFormset,
    AuditWebsiteDecisionUpdateForm,
    CaseWebsiteDecisionUpdateForm,
    AuditStatement1UpdateForm,
    AuditStatement2UpdateForm,
    AuditStatementDecisionUpdateForm,
    CaseStatementDecisionUpdateForm,
    AuditSummaryUpdateForm,
    AuditReportOptionsUpdateForm,
    AuditReportTextUpdateForm,
    AuditRetestMetadataUpdateForm,
    AuditRetestPagesUpdateForm,
    AuditRetestPageChecksForm,
    RetestCheckResultFilterForm,
    RetestCheckResultFormset,
    AuditRetestWebsiteDecisionUpdateForm,
    CaseFinalWebsiteDecisionUpdateForm,
    AuditRetestStatement1UpdateForm,
    AuditRetestStatement2UpdateForm,
    AuditRetestStatementDecisionUpdateForm,
    CaseFinalStatementDecisionUpdateForm,
)
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
)
from .utils import (
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    get_audit_metadata_rows,
    get_website_decision_rows,
    get_audit_statement_rows,
    get_statement_decision_rows,
    get_audit_report_options_rows,
    create_mandatory_pages_for_new_audit,
    get_next_page_url,
    get_next_retest_page_url,
    other_page_failed_check_results,
)

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


class AuditAllIssuesListView(ListView):
    """
    View of list WCAG definitions
    """

    model: Type[WcagDefinition] = WcagDefinition
    context_object_name: str = "wcag_definitions"
    template_name: str = "audits/all_issues.html"


def create_audit(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create audit

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: Case = get_object_or_404(Case, id=case_id)
    audit: Audit = Audit.objects.create(case=case)
    record_model_create_event(user=request.user, model_object=audit)  # type: ignore
    create_mandatory_pages_for_new_audit(audit=audit)
    return redirect(reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id}))  # type: ignore


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
    return redirect(reverse("audits:edit-audit-pages", kwargs={"pk": page.audit.id}))  # type: ignore


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
    return redirect(reverse("audits:edit-audit-pages", kwargs={"pk": page.audit.id}))  # type: ignore


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

        context["audit_metadata_rows"] = get_audit_metadata_rows(audit=audit)
        context["website_decision_rows"] = get_website_decision_rows(audit=audit)
        context["audit_statement_rows"] = get_audit_statement_rows(audit=audit)
        context["statement_decision_rows"] = get_statement_decision_rows(audit=audit)
        context["audit_report_options_rows"] = get_audit_report_options_rows(
            audit=audit
        )

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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-pages", kwargs=audit_pk)
        return super().get_success_url()


class AuditPagesUpdateView(AuditUpdateView):
    """
    View to update audit pages page
    """

    form_class: Type[AuditPagesUpdateForm] = AuditPagesUpdateForm
    template_name: str = "audits/forms/pages.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            standard_pages_formset: AuditStandardPageFormset = AuditStandardPageFormset(
                self.request.POST, prefix="standard"
            )
            extra_pages_formset: AuditExtraPageFormset = AuditExtraPageFormset(
                self.request.POST, prefix="extra"
            )
        else:
            standard_pages_formset: AuditStandardPageFormset = AuditStandardPageFormset(
                queryset=self.object.standard_pages, prefix="standard"
            )
            if "add_extra" in self.request.GET:
                extra_pages_formset: AuditExtraPageFormsetOneExtra = (
                    AuditExtraPageFormsetOneExtra(
                        queryset=self.object.extra_pages, prefix="extra"
                    )
                )
            else:
                extra_pages_formset: AuditExtraPageFormset = AuditExtraPageFormset(
                    queryset=self.object.extra_pages, prefix="extra"
                )
        context["standard_pages_formset"] = standard_pages_formset
        context["extra_pages_formset"] = extra_pages_formset
        context["standard_page_headers"] = STANDARD_PAGE_HEADERS
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        standard_pages_formset: AuditStandardPageFormset = context[
            "standard_pages_formset"
        ]
        extra_pages_formset: AuditExtraPageFormset = context["extra_pages_formset"]
        audit: Audit = form.save(commit=False)

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
                if not page.audit_id:  # type: ignore
                    page.audit = audit
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
        audit: Audit = self.object
        audit_pk: Dict[str, int] = {"pk": audit.id}  # type: ignore
        url: str = reverse("audits:edit-audit-pages", kwargs=audit_pk)
        if "add_extra" in self.request.POST:
            url: str = f"{url}?add_extra=true#extra-page-1"
        elif "save_continue" in self.request.POST:
            url: str = get_next_page_url(audit=audit)
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
        if "complete_date" in form.fields:
            form.fields["complete_date"].initial = self.page.complete_date
        if "no_errors_date" in form.fields:
            form.fields["no_errors_date"].initial = self.page.no_errors_date
        return form

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["filter_form"] = CheckResultFilterForm(
            initial={"manual": False, "axe": False, "pdf": False, "not_tested": False}
        )
        other_pages_failed_check_results: Dict[
            WcagDefinition, List[CheckResult]
        ] = other_page_failed_check_results(page=self.page)
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

        definitions_forms_errors: List[
            Tuple[WcagDefinition, CheckResultForm, List[CheckResult]]
        ] = []
        for count, check_results_form in enumerate(check_results_formset.forms):
            wcag_definition: WcagDefinition = wcag_definitions[count]
            check_results_form.fields["check_result_state"].label = wcag_definition
            definitions_forms_errors.append(
                (
                    wcag_definition,
                    check_results_form,
                    other_pages_failed_check_results.get(wcag_definition, []),
                )
            )

        context["check_results_formset"] = check_results_formset
        context["definitions_forms_errors"] = definitions_forms_errors

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        page: Page = self.page
        page.complete_date = form.cleaned_data["complete_date"]
        page.no_errors_date = form.cleaned_data["no_errors_date"]
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

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            page: Page = self.page
            return get_next_page_url(audit=page.audit, current_page=page)
        return self.request.path


class AuditWebsiteDecisionUpdateView(AuditUpdateView):
    """
    View to update website compliance fields
    """

    form_class: Type[AuditWebsiteDecisionUpdateForm] = AuditWebsiteDecisionUpdateForm
    template_name: str = "audits/forms/website_decision.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            case_form: CaseWebsiteDecisionUpdateForm = CaseWebsiteDecisionUpdateForm(
                self.request.POST, instance=self.object.case, prefix="case"
            )
        else:
            case_form: CaseWebsiteDecisionUpdateForm = CaseWebsiteDecisionUpdateForm(
                instance=self.object.case, prefix="case"
            )
        context["case_form"] = case_form
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        case_form: CaseStatementDecisionUpdateForm = context["case_form"]

        if case_form.is_valid():
            case_form.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-statement-1", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatement1UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 1 audit fields
    """

    form_class: Type[AuditStatement1UpdateForm] = AuditStatement1UpdateForm
    template_name: str = "audits/forms/statement_1.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-statement-2", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatement2UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 2 audit fields
    """

    form_class: Type[AuditStatement2UpdateForm] = AuditStatement2UpdateForm
    template_name: str = "audits/forms/statement_2.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-statement-decision", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementDecisionUpdateView(AuditUpdateView):
    """
    View to update statement decision fields
    """

    form_class: Type[
        AuditStatementDecisionUpdateForm
    ] = AuditStatementDecisionUpdateForm
    template_name: str = "audits/forms/statement_decision.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            case_form: CaseStatementDecisionUpdateForm = (
                CaseStatementDecisionUpdateForm(
                    self.request.POST, instance=self.object.case, prefix="case"
                )
            )
        else:
            case_form: CaseStatementDecisionUpdateForm = (
                CaseStatementDecisionUpdateForm(
                    instance=self.object.case, prefix="case"
                )
            )
        context["case_form"] = case_form
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        case_form: CaseStatementDecisionUpdateForm = context["case_form"]

        if case_form.is_valid():
            case_form.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-report-options", kwargs=audit_pk)
        return super().get_success_url()


class AuditReportOptionsUpdateView(AuditUpdateView):
    """
    View to update report options
    """

    form_class: Type[AuditReportOptionsUpdateForm] = AuditReportOptionsUpdateForm
    template_name: str = "audits/forms/report_options.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-summary", kwargs=audit_pk)
        return super().get_success_url()


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
            form=AuditStatement2UpdateForm()  # type: ignore
        )

        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-report-text", kwargs=audit_pk)
        return super().get_success_url()


class AuditReportTextUpdateView(AuditUpdateView):
    """
    View to update report text
    """

    form_class: Type[AuditReportTextUpdateForm] = AuditReportTextUpdateForm
    template_name: str = "audits/forms/report_text.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["wcag_definitions"] = WcagDefinition.objects.all()
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:audit-detail", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestDetailView(DetailView):
    """
    View of details of a single audit retest
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"
    template_name: str = "audits/audit_retest_detail.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add table rows to context for each section of page"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object  # type: ignore

        get_rows: Callable = partial(
            extract_form_labels_and_values, instance=audit.case
        )
        context["audit_retest_metadata_rows"] = get_audit_metadata_rows(audit=audit)
        context["audit_retest_website_decision_rows"] = get_rows(
            form=CaseFinalWebsiteDecisionUpdateForm()  # type: ignore
        )
        context["audit_retest_statement_decision_rows"] = get_rows(
            form=CaseFinalStatementDecisionUpdateForm()  # type: ignore
        )

        return context


class AuditRetestMetadataUpdateView(AuditUpdateView):
    """
    View to update audit retest metadata
    """

    form_class: Type[AuditRetestMetadataUpdateForm] = AuditRetestMetadataUpdateForm
    template_name: str = "audits/forms/retest_metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestPagesUpdateView(AuditUpdateView):
    """
    View to update audit retest pages page
    """

    form_class: Type[AuditRetestPagesUpdateForm] = AuditRetestPagesUpdateForm
    template_name: str = "audits/forms/retest_pages.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            return get_next_retest_page_url(audit=audit)
        return super().get_success_url()


class AuditRetestPageChecksFormView(AuditPageChecksFormView):
    """
    View to retest check results for a page
    """

    form_class: Type[AuditRetestPageChecksForm] = AuditRetestPageChecksForm
    template_name: str = "audits/forms/retest_page_checks.html"
    page: Page

    def get_form(self):
        """Populate next page select field"""
        form = super().get_form()
        form.fields["retest_complete_date"].initial = self.page.retest_complete_date
        form.fields[
            "retest_page_missing_date"
        ].initial = self.page.retest_page_missing_date
        return form

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["filter_form"] = RetestCheckResultFilterForm(
            initial={
                "fixed": False,
                "not-fixed": False,
                "not-tested": False,
            }
        )
        if self.request.POST:
            check_results_formset: RetestCheckResultFormset = RetestCheckResultFormset(
                self.request.POST
            )
        else:
            check_results_formset: RetestCheckResultFormset = RetestCheckResultFormset(
                initial=[
                    check_result.dict_for_retest
                    for check_result in self.page.failed_check_results
                ]
            )
        check_results_and_forms: List[Tuple[CheckResult, CheckResultForm]] = list(
            zip(self.page.failed_check_results, check_results_formset.forms)
        )

        context["check_results_formset"] = check_results_formset
        context["check_results_and_forms"] = check_results_and_forms

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        page: Page = self.page
        page.retest_complete_date = form.cleaned_data["retest_complete_date"]
        page.retest_page_missing_date = form.cleaned_data["retest_page_missing_date"]
        page.save()

        check_results_formset: CheckResultFormset = context["check_results_formset"]
        if check_results_formset.is_valid():
            for form in check_results_formset.forms:
                check_result: CheckResult = CheckResult.objects.get(
                    id=form.cleaned_data["id"]
                )
                check_result.retest_state = form.cleaned_data["retest_state"]
                check_result.retest_notes = form.cleaned_data["retest_notes"]
                check_result.save()
        else:
            return super().form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return get_next_retest_page_url(
                audit=self.page.audit, current_page=self.page
            )
        return super().get_success_url()


class AuditRetestWebsiteDecisionUpdateView(AuditWebsiteDecisionUpdateView):
    """
    View to retest website compliance fields
    """

    form_class: Type[
        AuditRetestWebsiteDecisionUpdateForm
    ] = AuditRetestWebsiteDecisionUpdateForm
    template_name: str = "audits/forms/retest_website_decision.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            case_form: CaseFinalWebsiteDecisionUpdateForm = (
                CaseFinalWebsiteDecisionUpdateForm(
                    self.request.POST, instance=self.object.case, prefix="case"
                )
            )
        else:
            case_form: CaseFinalWebsiteDecisionUpdateForm = (
                CaseFinalWebsiteDecisionUpdateForm(
                    instance=self.object.case, prefix="case"
                )
            )
        context["case_form"] = case_form
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-retest-statement-1", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatement1UpdateView(AuditUpdateView):
    """
    View to retest accessibility statement part one
    """

    form_class: Type[AuditRetestStatement1UpdateForm] = AuditRetestStatement1UpdateForm
    template_name: str = "audits/forms/retest_statement_1.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:edit-audit-retest-statement-2", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatement2UpdateView(AuditUpdateView):
    """
    View to retest accessibility statement part two
    """

    form_class: Type[AuditRetestStatement2UpdateForm] = AuditRetestStatement2UpdateForm
    template_name: str = "audits/forms/retest_statement_2.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse(
                "audits:edit-audit-retest-statement-decision", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementDecisionUpdateView(AuditStatementDecisionUpdateView):
    """
    View to retest statement decsion
    """

    form_class: Type[
        AuditRetestStatementDecisionUpdateForm
    ] = AuditRetestStatementDecisionUpdateForm
    template_name: str = "audits/forms/retest_statement_decision.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            case_form: CaseFinalStatementDecisionUpdateForm = (
                CaseFinalStatementDecisionUpdateForm(
                    self.request.POST, instance=self.object.case, prefix="case"
                )
            )
        else:
            case_form: CaseFinalStatementDecisionUpdateForm = (
                CaseFinalStatementDecisionUpdateForm(
                    instance=self.object.case, prefix="case"
                )
            )
        context["case_form"] = case_form
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}  # type: ignore
            return reverse("audits:audit-retest-detail", kwargs=audit_pk)
        return super().get_success_url()


def start_retest(
    request: HttpRequest, pk: int  # pylint: disable=unused-argument
) -> HttpResponse:
    """
    Start audit retest; Redirect to retest metadata page

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of audit to start retest of

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.retest_date = date.today()
    record_model_update_event(user=request.user, model_object=audit)  # type: ignore
    audit.save()
    return redirect(reverse("audits:edit-audit-retest-metadata", kwargs={"pk": pk}))
