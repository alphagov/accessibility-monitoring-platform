"""
Views for audits app (called tests by users)
"""
from functools import partial
from typing import Any, Callable, Dict, List, Type, Union

from django.forms.models import ModelForm
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.detail import DetailView

from ..cases.models import Case
from ..common.models import BOOLEAN_TRUE
from ..common.utils import (
    get_id_from_button_name,
    record_model_update_event,
    record_model_create_event,
)
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
)

from .forms import (
    AuditCreateForm,
    AuditMetadataUpdateForm,
    AuditPagesUpdateForm,
    AuditStandardPageFormset,
    AuditExtraPageFormset,
    AuditExtraPageFormsetOneExtra,
    AuditManualUpdateForm,
    AuditAxeUpdateForm,
    AxeCheckResultUpdateFormset,
    AuditPdfUpdateForm,
    AuditStatement1UpdateForm,
    AuditStatement2UpdateForm,
    AuditSummaryUpdateForm,
    CheckResultUpdateFormset,
    AuditReportOptionsUpdateForm,
    AuditReportTextUpdateForm,
)
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    AUDIT_TYPE_DEFAULT,
    TEST_TYPE_AXE,
    TEST_TYPE_MANUAL,
    TEST_TYPE_PDF,
    EXEMPTION_DEFAULT,
    PAGE_TYPE_PDF,
    PAGE_TYPE_ALL,
)
from .utils import (
    get_audit_url,
    create_check_results_for_new_page,
    create_pages_and_checks_for_new_audit,
    copy_all_pages_check_results,
    get_audit_metadata_rows,
    get_audit_check_results_by_wcag,
    get_audit_pdf_rows,
    get_audit_statement_rows,
    get_audit_report_options_rows,
    group_check_results_by_wcag_sub_type_labels,
)

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


def delete_audit(request: HttpRequest, case_id: int, pk: int) -> HttpResponse:
    """
    Delete audit

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of case
        pk (int): Id of audit to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.is_deleted = True
    record_model_update_event(user=request.user, model_object=audit)  # type: ignore
    audit.save()
    return redirect(reverse("cases:edit-test-results", kwargs={"pk": case_id}))  # type: ignore


def restore_audit(request: HttpRequest, case_id: int, pk: int) -> HttpResponse:
    """
    Restore deleted audit

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of case
        pk (int): Id of audit to restore

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit: Audit = get_object_or_404(Audit, id=pk)
    audit.is_deleted = False
    record_model_update_event(user=request.user, model_object=audit)  # type: ignore
    audit.save()
    return redirect(reverse("audits:audit-detail", kwargs={"case_id": case_id, "pk": audit.id}))  # type: ignore


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


class AuditCreateView(CreateView):
    """
    View to create a audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"
    form_class: Type[AuditCreateForm] = AuditCreateForm
    template_name: str = "audits/forms/create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        audit: Audit = form.save(commit=False)
        audit.case = Case.objects.get(pk=self.kwargs["case_id"])
        return super().form_valid(form)

    def get_form(self):
        """Initialise form fields"""
        form: ModelForm = super().get_form()  # type: ignore
        form.fields["is_exemption"].initial = EXEMPTION_DEFAULT
        form.fields["type"].initial = AUDIT_TYPE_DEFAULT
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        record_model_create_event(user=self.request.user, model_object=self.object)  # type: ignore
        create_pages_and_checks_for_new_audit(audit=self.object)  # type: ignore
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-metadata", audit=self.object)  # type: ignore
        else:
            url: str = reverse("cases:edit-test-results", kwargs={"pk": self.object.case.id})  # type: ignore
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
        context["audit_manual_wcag_failures"] = get_audit_check_results_by_wcag(
            audit=audit, test_type=TEST_TYPE_MANUAL
        )
        context["audit_axe_wcag_failures"] = get_audit_check_results_by_wcag(
            audit=audit, test_type=TEST_TYPE_AXE
        )
        context["audit_pdf_rows"] = get_audit_pdf_rows(audit)
        context["audit_statement_rows"] = get_audit_statement_rows(audit)
        context["audit_report_options_rows"] = get_audit_report_options_rows(audit)

        return context


class AuditMetadataUpdateView(AuditUpdateView):
    """
    View to update audit metadata
    """

    form_class: Type[AuditMetadataUpdateForm] = AuditMetadataUpdateForm
    template_name: str = "audits/forms/metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-pages", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-metadata'  # type: ignore
        return url


class AuditPagesUpdateView(AuditUpdateView):
    """
    View to update audit pages
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
        audit: Audit = form.save()

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
                    create_check_results_for_new_page(page=page)
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
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-pages'  # type: ignore
        elif "save_continue" in self.request.POST:
            url: str = reverse(
                "audits:edit-audit-manual",
                kwargs={
                    "page_id": self.object.next_page.id,  # type: ignore
                    "audit_id": self.object.id,  # type: ignore
                    "case_id": self.object.case.id,  # type: ignore
                },
            )
        elif "add_extra" in self.request.POST:
            url: str = f'{get_audit_url(url_name="edit-audit-pages", audit=self.object)}?add_extra=true'  # type: ignore
        else:
            url: str = get_audit_url(url_name="edit-audit-pages", audit=self.object)  # type: ignore
        return url


class AuditPageFormView(FormView):
    """
    View to update an audit page
    """

    audit: Audit
    page: Page

    def setup(self, request, *args, **kwargs):
        """Add audit and page objects to view"""
        super().setup(request, *args, **kwargs)
        self.audit = Audit.objects.get(pk=kwargs["audit_id"])
        self.page = Page.objects.get(pk=kwargs["page_id"])

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Add audit and page to context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["audit"] = self.audit
        context["page"] = self.page
        return context

    def get_form(self):
        """Populate page choices"""
        form = super().get_form()
        form.fields["next_page"].queryset = self.audit.all_pages
        form.fields["next_page"].initial = self.audit.next_page
        return form


class AuditManualFormView(AuditPageFormView):
    """
    View to update manual check results for a page
    """

    form_class: Type[AuditManualUpdateForm] = AuditManualUpdateForm
    template_name: str = "audits/forms/manual.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                self.request.POST
            )
        else:
            check_results: QuerySet[CheckResult] = CheckResult.objects.filter(  # type: ignore
                page=self.page, type=TEST_TYPE_MANUAL
            )
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                queryset=check_results
            )
        for check_results_form in check_results_formset.forms:
            check_results_form.fields["failed"].widget.attrs = {
                "label": f"{check_results_form.instance.wcag_definition.name}: "
                f"{check_results_form.instance.wcag_definition.description}"
            }
        context["check_results_formset"] = check_results_formset

        context[
            "check_result_forms_by_wcag_sub_type"
        ] = group_check_results_by_wcag_sub_type_labels(
            check_result_update_forms=check_results_formset.forms
        )

        return context

    def get_form(self):
        """Populate labels"""
        form = super().get_form()
        audit: Audit = self.audit
        page: Page = self.page
        form.fields[
            "audit_manual_complete_date"
        ].initial = audit.audit_manual_complete_date
        form.fields[
            "page_manual_checks_complete_date"
        ].label = f"Mark the test on {page} as complete?"
        form.fields["page_manual_checks_complete_date"].widget.attrs = {
            "label": f"Record if the test on {page} is complete"
        }
        form.fields[
            "page_manual_checks_complete_date"
        ].initial = page.manual_checks_complete_date
        return form

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        audit: Audit = self.audit
        page: Page = self.page
        check_results_formset: CheckResultUpdateFormset = context[
            "check_results_formset"
        ]
        check_results: List[CheckResult] = []

        if check_results_formset.is_valid():
            check_results = check_results_formset.save(commit=False)
            for check_result in check_results:
                record_model_update_event(user=self.request.user, model_object=check_result)  # type: ignore
                check_result.save()
        else:
            return super().form_invalid(form)

        if page.type == PAGE_TYPE_ALL and check_results:
            copy_all_pages_check_results(user=self.request.user, audit=audit, check_results=check_results)  # type: ignore

        audit.audit_manual_complete_date = form.cleaned_data[
            "audit_manual_complete_date"
        ]
        audit.next_page = form.cleaned_data["next_page"]
        audit.save()

        page.manual_checks_complete_date = form.cleaned_data[
            "page_manual_checks_complete_date"
        ]
        page.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.audit
        if "save_change_test_page" in self.request.POST:
            url: str = reverse(
                "audits:edit-audit-manual",
                kwargs={
                    "page_id": audit.next_page.id,  # type: ignore
                    "audit_id": audit.id,  # type: ignore
                    "case_id": audit.case.id,  # type: ignore
                },
            )
        elif "save_continue" in self.request.POST:
            url: str = reverse(
                "audits:edit-audit-axe",
                kwargs={
                    "page_id": audit.next_page.id,  # type: ignore
                    "audit_id": audit.id,  # type: ignore
                    "case_id": audit.case.id,  # type: ignore
                },
            )
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=audit)}#audit-manual'  # type: ignore
        return url


class AuditAxeFormView(AuditPageFormView):
    """
    View to update axe audits for a page
    """

    form_class: Type[AuditAxeUpdateForm] = AuditAxeUpdateForm
    template_name: str = "audits/forms/axe.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            check_results_formset: AxeCheckResultUpdateFormset = (
                AxeCheckResultUpdateFormset(self.request.POST)
            )
        else:
            check_results: QuerySet[CheckResult] = CheckResult.objects.filter(  # type: ignore
                page=self.page, type=TEST_TYPE_AXE, is_deleted=False
            )
            check_results_formset: AxeCheckResultUpdateFormset = (
                AxeCheckResultUpdateFormset(queryset=check_results)
            )
        context["check_results_formset"] = check_results_formset
        return context

    def get_form(self):
        """Populate page choices and labels"""
        form = super().get_form()
        audit: Audit = self.audit
        page: Page = self.page
        form.fields["audit_axe_complete_date"].initial = audit.audit_axe_complete_date
        form.fields[
            "page_axe_checks_complete_date"
        ].label = f"Mark the test on {page} as complete?"
        form.fields["page_axe_checks_complete_date"].widget.attrs = {
            "label": f"Record if the test on {page} is complete"
        }
        form.fields[
            "page_axe_checks_complete_date"
        ].initial = page.axe_checks_complete_date
        return form

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        check_results_formset: AxeCheckResultUpdateFormset = context[
            "check_results_formset"
        ]

        audit: Audit = self.audit
        page: Page = self.page

        if check_results_formset.is_valid():
            check_results: List[CheckResult] = check_results_formset.save(commit=False)
            for check_result in check_results:
                if check_result.id:  # type: ignore
                    record_model_update_event(user=self.request.user, model_object=check_result)  # type: ignore
                    check_result.save()
                else:
                    check_result.audit = audit
                    check_result.page = page
                    check_result.type = TEST_TYPE_AXE
                    check_result.failed = BOOLEAN_TRUE
                    check_result.save()
                    record_model_create_event(user=self.request.user, model_object=check_result)  # type: ignore
        else:
            return super().form_invalid(form)

        if page.type == PAGE_TYPE_ALL and check_results:
            copy_all_pages_check_results(user=self.request.user, audit=audit, check_results=check_results)  # type: ignore

        audit.audit_axe_complete_date = form.cleaned_data["audit_axe_complete_date"]
        audit.next_page = form.cleaned_data["next_page"]
        audit.save()

        page.axe_checks_complete_date = form.cleaned_data[
            "page_axe_checks_complete_date"
        ]
        page.save()

        check_result_id_to_delete: Union[int, None] = get_id_from_button_name(
            button_name_prefix="remove_check_result_",
            querydict=self.request.POST,
        )
        if check_result_id_to_delete is not None:
            check_result_to_delete: CheckResult = CheckResult.objects.get(
                id=check_result_id_to_delete
            )
            check_result_to_delete.is_deleted = True
            record_model_update_event(user=self.request.user, model_object=check_result_to_delete)  # type: ignore
            check_result_to_delete.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.audit
        if "save_exit" in self.request.POST:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=audit)}#audit-axe'  # type: ignore
        elif "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-pdf", audit=audit)
        else:
            url: str = reverse(
                "audits:edit-audit-axe",
                kwargs={
                    "page_id": audit.next_page.id,  # type: ignore
                    "audit_id": audit.id,  # type: ignore
                    "case_id": audit.case.id,  # type: ignore
                },
            )
        return url


class AuditPdfUpdateView(AuditUpdateView):
    """
    View to update pdf audits
    """

    form_class: Type[AuditPdfUpdateForm] = AuditPdfUpdateForm
    template_name: str = "audits/forms/pdf.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        page: Page = Page.objects.get(audit=self.object, type=PAGE_TYPE_PDF)
        context["page"] = page
        if self.request.POST:
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                self.request.POST
            )
        else:
            check_results: QuerySet[CheckResult] = CheckResult.objects.filter(  # type: ignore
                page=page, type=TEST_TYPE_PDF
            )

            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                queryset=check_results
            )
        for check_results_form in check_results_formset.forms:
            check_results_form.fields["failed"].widget.attrs = {
                "label": check_results_form.instance.wcag_definition.name
            }
            check_results_form.fields["notes"].label = ""
        context["check_results_formset"] = check_results_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        check_results_formset: CheckResultUpdateFormset = context[
            "check_results_formset"
        ]
        if check_results_formset.is_valid():
            check_results: List[Page] = check_results_formset.save(commit=False)
            for check_result in check_results:
                record_model_update_event(user=self.request.user, model_object=check_result)  # type: ignore
                check_result.save()
        else:
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-statement-1", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-pdf'  # type: ignore
        return url


class AuditStatement1UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 1 audit fields
    """

    form_class: Type[AuditStatement1UpdateForm] = AuditStatement1UpdateForm
    template_name: str = "audits/forms/statement-1.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-statement-2", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-statement'  # type: ignore
        return url


class AuditStatement2UpdateView(AuditUpdateView):
    """
    View to update accessibility statement 2 audit fields
    """

    form_class: Type[AuditStatement2UpdateForm] = AuditStatement2UpdateForm
    template_name: str = "audits/forms/statement-2.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-summary", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-statement'  # type: ignore
        return url


class AuditSummaryUpdateView(AuditUpdateView):
    """
    View to update audit summary
    """

    form_class: Type[AuditSummaryUpdateForm] = AuditSummaryUpdateForm
    template_name: str = "audits/forms/summary.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        view_url_param: Union[str, None] = self.request.GET.get("view")
        context["show_failures_by_page"] = view_url_param == "Page view"

        check_failures: QuerySet[CheckResult] = (
            CheckResult.objects.filter(audit=self.object, failed=BOOLEAN_TRUE)  # type: ignore
            .exclude(page__type=PAGE_TYPE_ALL)
            .order_by("wcag_definition__id")
        )

        audit_failures_by_wcag: Dict[WcagDefinition, List[CheckResult]] = {}
        audit_failures_by_page: Dict[Page, List[CheckResult]] = {}

        for check_failure in check_failures:
            if check_failure.wcag_definition in audit_failures_by_wcag:
                audit_failures_by_wcag[check_failure.wcag_definition].append(
                    check_failure
                )
            else:
                audit_failures_by_wcag[check_failure.wcag_definition] = [check_failure]
            if check_failure.page in audit_failures_by_page:
                audit_failures_by_page[check_failure.page].append(check_failure)
            else:
                audit_failures_by_page[check_failure.page] = [check_failure]

        context["audit_failures_by_wcag"] = [
            (key, value) for key, value in audit_failures_by_wcag.items()
        ]
        context["audit_failures_by_page"] = [
            (key, value) for key, value in audit_failures_by_page.items()
        ]

        get_rows: Callable = partial(extract_form_labels_and_values, instance=self.object)  # type: ignore
        context["audit_statement_rows"] = get_rows(
            form=AuditStatement1UpdateForm()
        ) + get_rows(form=AuditStatement2UpdateForm())

        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-report-options", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}'  # type: ignore
        return url


class AuditReportOptionsUpdateView(AuditUpdateView):
    """
    View to update report options
    """

    form_class: Type[AuditReportOptionsUpdateForm] = AuditReportOptionsUpdateForm
    template_name: str = "audits/forms/report-options.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-report-text", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-report-options'  # type: ignore
        return url


class AuditReportTextUpdateView(AuditUpdateView):
    """
    View to update report text
    """

    form_class: Type[AuditReportTextUpdateForm] = AuditReportTextUpdateForm
    template_name: str = "audits/forms/report-text.html"

    def get_success_url(self) -> str:
        """Return to audit view page"""
        return f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-report-text'  # type: ignore
