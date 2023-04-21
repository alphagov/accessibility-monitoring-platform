"""
Views for audits app (called tests by users)
"""
from datetime import date
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
import urllib

from django.db.models.query import Q, QuerySet
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from ..cases.models import (
    Case,
    CaseEvent,
    Contact,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_START_RETEST,
)
from ..common.forms import AMPChoiceCheckboxWidget
from ..common.utils import (
    record_model_update_event,
    record_model_create_event,
    list_to_dictionary_of_lists,
    get_id_from_button_name,
    amp_format_date,
)
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
)

from .forms import (
    AuditMetadataUpdateForm,
    AuditStandardPageFormset,
    AuditExtraPageFormset,
    AuditExtraPageFormsetOneExtra,
    AuditExtraPageFormsetTwoExtra,
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
    Audit12WeekStatementUpdateForm,
    AuditRetestStatement1UpdateForm,
    AuditRetestStatement2UpdateForm,
    AuditRetestStatementComparisonUpdateForm,
    AuditRetestStatementDecisionUpdateForm,
    CaseFinalStatementDecisionUpdateForm,
    WcagDefinitionSearchForm,
    WcagDefinitionCreateUpdateForm,
)
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    PAGE_TYPE_FORM,
)
from .utils import (
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    create_mandatory_pages_for_new_audit,
    get_next_page_url,
    get_next_retest_page_url,
    other_page_failed_check_results,
    report_data_updated,
    get_test_view_tables_context,
    get_retest_view_tables_context,
)

STANDARD_PAGE_HEADERS: List[str] = [
    "Home",
    "Contact",
    "Accessibility Statement",
    "A Form",
    "PDF",
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
    Create audit. If one already exists use that instead.

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: Case = get_object_or_404(Case, id=case_id)
    if case.audit:
        return redirect(
            reverse("audits:edit-audit-metadata", kwargs={"pk": case.audit.id})
        )
    audit: Audit = Audit.objects.create(case=case)
    record_model_create_event(user=request.user, model_object=audit)
    create_mandatory_pages_for_new_audit(audit=audit)
    CaseEvent.objects.create(
        case=case,
        done_by=request.user,
        event_type=CASE_EVENT_CREATE_AUDIT,
        message="Started test",
    )
    return redirect(reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id}))


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
    record_model_update_event(user=request.user, model_object=page)
    page.save()
    return redirect(reverse("audits:edit-audit-pages", kwargs={"pk": page.audit.id}))


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
    record_model_update_event(user=request.user, model_object=page)
    page.save()
    return redirect(reverse("audits:edit-audit-pages", kwargs={"pk": page.audit.id}))


class AuditDetailView(DetailView):
    """
    View of details of a single audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add table rows to context for each section of page"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object

        return {
            **get_test_view_tables_context(audit=audit),
            **context,
        }


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
            record_model_update_event(user=self.request.user, model_object=self.object)
            old_audit: Audit = Audit.objects.get(id=self.object.id)
            if old_audit.retest_date != self.object.retest_date:
                CaseEvent.objects.create(
                    case=self.object.case,
                    done_by=self.request.user,
                    event_type=CASE_EVENT_START_RETEST,
                    message=f"Started retest (date set to {amp_format_date(self.object.retest_date)})",
                )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class AuditCaseUpdateView(AuditUpdateView):
    """
    View to update audit and case fields
    """

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if "case_form" not in context:
            if self.request.POST:
                case_form: Form = self.case_form_class(
                    self.request.POST, instance=self.object.case, prefix="case"
                )
            else:
                case_form: Form = self.case_form_class(
                    instance=self.object.case, prefix="case"
                )
            context["case_form"] = case_form
        return context

    def post(
        self, request: HttpRequest, *args: Tuple[str], **kwargs: Dict[str, Any]
    ) -> Union[HttpResponseRedirect, HttpResponse]:
        """Populate two forms from post request"""
        self.object: Audit = self.get_object()
        form: Form = self.form_class(request.POST, instance=self.object)  # type: ignore
        case_form: Form = self.case_form_class(
            request.POST, instance=self.object.case, prefix="case"
        )
        if form.is_valid() and case_form.is_valid():
            form.save()
            case_form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(form=form, case_form=case_form)
            )


class AuditMetadataUpdateView(AuditUpdateView):
    """
    View to update audit metadata
    """

    form_class: Type[AuditMetadataUpdateForm] = AuditMetadataUpdateForm
    template_name: str = "audits/forms/metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
        audit: Audit = self.object
        if self.request.POST:
            standard_pages_formset: AuditStandardPageFormset = AuditStandardPageFormset(
                self.request.POST, prefix="standard"
            )
            extra_pages_formset: AuditExtraPageFormset = AuditExtraPageFormset(
                self.request.POST, prefix="extra"
            )
        else:
            standard_pages_formset: AuditStandardPageFormset = AuditStandardPageFormset(
                queryset=audit.standard_pages, prefix="standard"
            )
            if "add_extra" in self.request.GET:
                extra_pages_formset: AuditExtraPageFormsetOneExtra = (
                    AuditExtraPageFormsetOneExtra(
                        queryset=audit.extra_pages, prefix="extra"
                    )
                )
            else:
                if audit.extra_pages:
                    extra_pages_formset: AuditExtraPageFormset = AuditExtraPageFormset(
                        queryset=audit.extra_pages, prefix="extra"
                    )
                else:
                    extra_pages_formset: AuditExtraPageFormset = (
                        AuditExtraPageFormsetTwoExtra(
                            queryset=audit.extra_pages, prefix="extra"
                        )
                    )
        for form in standard_pages_formset:
            if form.instance.page_type == PAGE_TYPE_FORM:
                form.fields["is_contact_page"].label = "Form is on contact page"
                form.fields["is_contact_page"].widget = AMPChoiceCheckboxWidget(
                    attrs={"label": "Mark as on contact page"}
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
                record_model_update_event(user=self.request.user, model_object=page)
                page.save()
        else:
            return super().form_invalid(form)

        if extra_pages_formset.is_valid():
            pages: List[Page] = extra_pages_formset.save(commit=False)
            for page in pages:
                if not page.audit_id:
                    page.audit = audit
                    page.save()
                    record_model_create_event(user=self.request.user, model_object=page)
                else:
                    record_model_update_event(user=self.request.user, model_object=page)
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
            record_model_update_event(
                user=self.request.user, model_object=page_to_delete
            )
            page_to_delete.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.object
        audit_pk: Dict[str, int] = {"pk": audit.id}
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
                user=self.request.user,
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


class AuditWebsiteDecisionUpdateView(AuditCaseUpdateView):
    """
    View to update website compliance fields
    """

    form_class: Type[AuditWebsiteDecisionUpdateForm] = AuditWebsiteDecisionUpdateForm
    case_form_class: Type[CaseWebsiteDecisionUpdateForm] = CaseWebsiteDecisionUpdateForm
    template_name: str = "audits/forms/website_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-statement-1", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatement1UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 1 audit fields
    """

    form_class: Type[AuditStatement1UpdateForm] = AuditStatement1UpdateForm
    template_name: str = "audits/forms/statement_1.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        if "add_contact_email" in form.changed_data:
            contact: Contact = Contact.objects.create(
                case=self.object.case,
                email=form.cleaned_data["add_contact_email"],
                created_by=self.request.user,
            )
            record_model_create_event(user=self.request.user, model_object=contact)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-decision", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementDecisionUpdateView(AuditCaseUpdateView):
    """
    View to update statement decision fields
    """

    form_class: Type[
        AuditStatementDecisionUpdateForm
    ] = AuditStatementDecisionUpdateForm
    case_form_class: Type[
        CaseStatementDecisionUpdateForm
    ] = CaseStatementDecisionUpdateForm
    template_name: str = "audits/forms/statement_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-report-options", kwargs=audit_pk)
        return super().get_success_url()


class AuditReportOptionsUpdateView(AuditUpdateView):
    """
    View to update report options
    """

    form_class: Type[AuditReportOptionsUpdateForm] = AuditReportOptionsUpdateForm
    template_name: str = "audits/forms/report_options.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        changed_report_data: List[str] = [
            field_name
            for field_name in form.changed_data
            if field_name != "audit_report_options_complete_date"
        ]
        if changed_report_data:
            report_data_updated(audit=self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
                items=audit.failed_check_results, group_by_attr="page"
            )
        else:
            context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                items=audit.failed_check_results, group_by_attr="wcag_definition"
            )

        get_audit_rows: Callable = partial(
            extract_form_labels_and_values, instance=audit
        )
        context["audit_statement_rows"] = get_audit_rows(
            form=AuditStatement1UpdateForm()
        ) + get_audit_rows(form=AuditStatement2UpdateForm())

        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            audit: Audit = self.object
            case_pk: Dict[str, int] = {"pk": audit.case.id}
            return reverse("cases:edit-test-results", kwargs=case_pk)
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
            audit: Audit = self.object
            case_pk: Dict[str, int] = {"pk": audit.case.id}
            return reverse("cases:edit-test-results", kwargs=case_pk)
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
        audit: Audit = self.object

        return {
            **get_retest_view_tables_context(case=audit.case),
            **context,
        }


class AuditRetestMetadataUpdateView(AuditUpdateView):
    """
    View to update audit retest metadata
    """

    form_class: Type[AuditRetestMetadataUpdateForm] = AuditRetestMetadataUpdateForm
    template_name: str = "audits/forms/retest_metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            if not audit.case.psb_response:
                audit_pk: Dict[str, int] = {"pk": self.object.id}
                return reverse("audits:edit-audit-retest-statement-1", kwargs=audit_pk)
            return get_next_retest_page_url(audit=audit)
        return super().get_success_url()


class AuditRetestPagesUpdateView(AuditUpdateView):
    """
    View to update audit retest pages page
    """

    form_class: Type[AuditRetestPagesUpdateForm] = AuditRetestPagesUpdateForm
    template_name: str = "audits/forms/retest_pages.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["hide_fixed"] = "hide-fixed" in self.request.GET
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-retest-website-decision", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestPageChecksFormView(AuditPageChecksFormView):
    """
    View to retest check results for a page
    """

    form_class: Type[AuditRetestPageChecksForm] = AuditRetestPageChecksForm
    template_name: str = "audits/forms/retest_page_checks.html"
    page: Page

    def get_form(self):
        """Populate next page fields"""
        form = super().get_form()
        form.fields["retest_complete_date"].initial = self.page.retest_complete_date
        form.fields[
            "retest_page_missing_date"
        ].initial = self.page.retest_page_missing_date
        form.fields["retest_notes"].initial = self.page.retest_notes
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
        page.retest_notes = form.cleaned_data["retest_notes"]
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


class AuditRetestWebsiteDecisionUpdateView(AuditCaseUpdateView):
    """
    View to retest website compliance fields
    """

    form_class: Type[
        AuditRetestWebsiteDecisionUpdateForm
    ] = AuditRetestWebsiteDecisionUpdateForm
    case_form_class: Type[
        CaseFinalWebsiteDecisionUpdateForm
    ] = CaseFinalWebsiteDecisionUpdateForm
    template_name: str = "audits/forms/retest_website_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-retest-statement-2", kwargs=audit_pk)
        return super().get_success_url()


class Audit12WeekStatementUpdateView(AuditUpdateView):
    """
    View to add a statement at 12-weeks (no initial statement)
    """

    form_class: Type[Audit12WeekStatementUpdateForm] = Audit12WeekStatementUpdateForm
    template_name: str = "audits/forms/twelve_week_statement.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_return" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-retest-statement-1", kwargs=audit_pk)
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
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse(
                "audits:edit-audit-retest-statement-comparison", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementComparisonUpdateView(AuditUpdateView):
    """
    View to retest statement comparison
    """

    form_class: Type[
        AuditRetestStatementComparisonUpdateForm
    ] = AuditRetestStatementComparisonUpdateForm
    template_name: str = "audits/forms/retest_statement_comparison.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse(
                "audits:edit-audit-retest-statement-decision", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementDecisionUpdateView(AuditCaseUpdateView):
    """
    View to retest statement decsion
    """

    form_class: Type[
        AuditRetestStatementDecisionUpdateForm
    ] = AuditRetestStatementDecisionUpdateForm
    case_form_class: Type[
        CaseFinalStatementDecisionUpdateForm
    ] = CaseFinalStatementDecisionUpdateForm
    template_name: str = "audits/forms/retest_statement_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
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
    record_model_update_event(user=request.user, model_object=audit)
    audit.save()
    CaseEvent.objects.create(
        case=audit.case,
        done_by=request.user,
        event_type=CASE_EVENT_START_RETEST,
        message="Started retest",
    )
    return redirect(reverse("audits:edit-audit-retest-metadata", kwargs={"pk": pk}))


class WcagDefinitionListView(ListView):
    """
    View of list of WCAG definitions
    """

    model: Type[WcagDefinition] = WcagDefinition
    template_name: str = "audits/wcag_definition_list.html"
    context_object_name: str = "wcag_definitions"
    paginate_by: int = 10

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.wcag_definition_search_form: WcagDefinitionSearchForm = (
                WcagDefinitionSearchForm(self.request.GET)
            )
            self.wcag_definition_search_form.is_valid()
        else:
            self.wcag_definition_search_form = WcagDefinitionSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[WcagDefinition]:
        """Add filters to queryset"""
        if self.wcag_definition_search_form.errors:
            return WcagDefinition.objects.none()

        if hasattr(self.wcag_definition_search_form, "cleaned_data"):
            search_str: Optional[
                str
            ] = self.wcag_definition_search_form.cleaned_data.get(
                "wcag_definition_search"
            )

            if search_str:
                return WcagDefinition.objects.filter(
                    Q(  # pylint: disable=unsupported-binary-operation
                        name__icontains=search_str
                    )
                    | Q(type__icontains=search_str)
                    | Q(description__icontains=search_str)
                    | Q(url_on_w3__icontains=search_str)
                    | Q(report_boilerplate__icontains=search_str)
                )

        return WcagDefinition.objects.all()

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["wcag_definition_search_form"] = self.wcag_definition_search_form

        get_without_page: Dict[str, Union[str, List[object]]] = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }
        context["url_parameters"] = urllib.parse.urlencode(get_without_page)
        return context


class WcagDefinitionCreateView(CreateView):
    """
    View to create a WCAG definition
    """

    model: Type[WcagDefinition] = WcagDefinition
    form_class: Type[WcagDefinitionCreateUpdateForm] = WcagDefinitionCreateUpdateForm
    template_name: str = "audits/forms/wcag_definition_create.html"
    context_object_name: str = "wcag_definition"

    def get_success_url(self) -> str:
        """Return to list of WCAG definitions"""
        return reverse("audits:wcag-definition-list")


class WcagDefinitionUpdateView(UpdateView):
    """
    View to update a WCAG definition
    """

    model: Type[WcagDefinition] = WcagDefinition
    form_class: Type[WcagDefinitionCreateUpdateForm] = WcagDefinitionCreateUpdateForm
    template_name: str = "audits/forms/wcag_definition_update.html"
    context_object_name: str = "wcag_definition"

    def get_success_url(self) -> str:
        """Return to list of WCAG definitions"""
        return reverse("audits:wcag-definition-list")


def clear_published_report_data_updated_time(
    request: HttpRequest, pk: int
) -> HttpResponse:
    """
    Remove value from published_report_data_updated_time to hide notification

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of audit to update

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.published_report_data_updated_time = None
    record_model_update_event(user=request.user, model_object=audit)
    audit.save()
    redirect_destination: str = request.GET.get(
        "redirect_destination",
        reverse("cases:case-detail", kwargs={"pk": audit.case.id}),
    )
    return redirect(redirect_destination)
