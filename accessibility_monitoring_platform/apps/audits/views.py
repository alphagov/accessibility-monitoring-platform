"""
Views for audits app (called tests by users)
"""
from functools import partial
from typing import Any, Callable, Dict, List, Type, Union

from django.forms.models import ModelForm
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.detail import DetailView

from ..cases.models import Case
from ..common.utils import (
    FieldLabelAndValue,
    get_id_from_button_name,
    record_model_update_event,
    record_model_create_event,
)

from .forms import (
    AuditCreateForm,
    AuditUpdateMetadataForm,
    AuditUpdatePagesForm,
    AuditStandardPageFormset,
    AuditExtraPageFormset,
    AuditExtraPageFormsetOneExtra,
    AuditUpdateByPageManualForm,
    AuditUpdateAxeForm,
    AuditUpdatePdfForm,
    CheckResultUpdateFormset,
)
from .models import (
    Audit,
    Page,
    CheckResult,
    TEST_TYPE_MANUAL,
    TEST_TYPE_PDF,
    EXEMPTION_DEFAULT,
    PAGE_TYPE_EXTRA,
    PAGE_TYPE_PDF,
)
from .utils import create_pages_and_tests_for_new_audit, extract_labels_and_values

STANDARD_PAGE_HEADERS: List[str] = [
    "Home Page",
    "Contact Page",
    "Accessibility Statement",
    "PDF",
    "A Form",
]


def get_audit_url(url_name: str, audit: Audit) -> str:
    """Return url string for name and audit"""
    return reverse_lazy(
        f"audits:{url_name}",
        kwargs={
            "pk": audit.id,  # type: ignore
            "case_id": audit.case.id,  # type: ignore
        },
    )


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
    return redirect(reverse_lazy("cases:edit-test-results", kwargs={"pk": case_id}))  # type: ignore


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
    return redirect(reverse_lazy("audits:audit-detail", kwargs={"case_id": case_id, "pk": audit.id}))  # type: ignore


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
        form.fields["type"].initial = PAGE_TYPE_EXTRA
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        record_model_create_event(user=self.request.user, model_object=self.object)  # type: ignore
        create_pages_and_tests_for_new_audit(audit=self.object, user=self.request.user)  # type: ignore
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-metadata", audit=self.object)  # type: ignore
        else:
            url: str = reverse_lazy("cases:edit-test-results", kwargs={"pk": self.object.case.id})  # type: ignore
        return url


class AuditDetailView(DetailView):
    """
    View of details of a single audit
    """

    model: Type[Audit] = Audit
    context_object_name: str = "audit"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        get_rows: Callable = partial(extract_labels_and_values, audit=self.object)  # type: ignore

        audit_metadata_rows: List[FieldLabelAndValue] = get_rows(
            form=AuditUpdateMetadataForm()
        )
        if self.object.case.auditor:  # type: ignore
            audit_metadata_rows.insert(
                1,
                FieldLabelAndValue(
                    label="Auditor",
                    value=self.object.case.auditor.get_full_name(),  # type: ignore
                ),
            )

        context["audit_metadata_rows"] = audit_metadata_rows
        context["standard_pages"] = self.object.page_audit.filter(  # type: ignore
            is_deleted=False
        ).exclude(type=PAGE_TYPE_EXTRA)
        context["extra_pages"] = self.object.page_audit.filter(  # type: ignore
            is_deleted=False, type=PAGE_TYPE_EXTRA
        )

        pdf_audit_manual_tests: QuerySet[CheckResult] = CheckResult.objects.filter(
            audit=self.object, type=TEST_TYPE_MANUAL, failed="yes"  # type: ignore
        )
        context["audit_manual_rows"] = [
            FieldLabelAndValue(
                label=check_result.wcag_definition.name, value=check_result.notes
            )
            for check_result in pdf_audit_manual_tests
        ]

        pdf_audit_pdf_tests: QuerySet[CheckResult] = CheckResult.objects.filter(
            audit=self.object, type=TEST_TYPE_PDF, failed="yes"  # type: ignore
        )
        context["audit_pdf_rows"] = [
            FieldLabelAndValue(
                label=check_result.wcag_definition.name, value=check_result.notes
            )
            for check_result in pdf_audit_pdf_tests
        ]

        return context


class AuditMetadataUpdateView(AuditUpdateView):
    """
    View to update audit metadata
    """

    form_class: Type[AuditUpdateMetadataForm] = AuditUpdateMetadataForm
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

    form_class: Type[AuditUpdatePagesForm] = AuditUpdatePagesForm
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
            standard_pages: QuerySet[Page] = self.object.page_audit.exclude(  # type: ignore
                type=PAGE_TYPE_EXTRA
            )
            extra_pages: QuerySet[Page] = self.object.page_audit.filter(  # type: ignore
                is_deleted=False, type=PAGE_TYPE_EXTRA
            )

            standard_pages_formset: AuditStandardPageFormset = AuditStandardPageFormset(
                queryset=standard_pages, prefix="standard"
            )
            if "add_extra" in self.request.GET:
                extra_pages_formset: AuditExtraPageFormsetOneExtra = (
                    AuditExtraPageFormsetOneExtra(queryset=extra_pages, prefix="extra")
                )
            else:
                extra_pages_formset: AuditExtraPageFormset = AuditExtraPageFormset(
                    queryset=extra_pages, prefix="extra"
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
            url: str = reverse_lazy(
                "audits:edit-audit-manual-by-page",
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


class AuditManualByPageUpdateView(FormView):
    """
    View to update manual audits grouped by page
    """

    form_class: Type[AuditUpdateByPageManualForm] = AuditUpdateByPageManualForm
    template_name: str = "audits/forms/manual_by_page.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = Audit.objects.get(pk=self.kwargs["audit_id"])
        context["audit"] = audit
        page: Page = Page.objects.get(pk=self.kwargs["page_id"])
        context["page"] = page
        if self.request.POST:
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                self.request.POST
            )
        else:
            check_results: QuerySet[CheckResult] = CheckResult.objects.filter(  # type: ignore
                page=page, type=TEST_TYPE_MANUAL
            )
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                queryset=check_results
            )
        for check_results_form in check_results_formset.forms:
            check_results_form.fields["failed"].label = ""
            check_results_form.fields["failed"].widget.attrs = {
                "label": check_results_form.instance.wcag_definition.name
            }
        context["check_results_formset"] = check_results_formset
        return context

    def get_form(self):
        """Populate page choices and labels"""
        form = super().get_form()
        audit: Audit = Audit.objects.get(pk=self.kwargs["audit_id"])
        form.fields["next_page"].queryset = Page.objects.filter(audit=audit)
        form.fields["next_page"].initial = audit.next_page
        page: Page = Page.objects.get(pk=self.kwargs["page_id"])
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

        audit: Audit = Audit.objects.get(pk=self.kwargs["audit_id"])
        page: Page = Page.objects.get(pk=self.kwargs["page_id"])

        if (
            "audit_manual_complete_date" in form.cleaned_data
            or "next_page" in form.cleaned_data
        ):
            audit.audit_manual_complete_date = form.cleaned_data[
                "audit_manual_complete_date"
            ]
            audit.next_page = form.cleaned_data["next_page"]
            audit.save()

        if "page_manual_checks_complete_date" in form.cleaned_data:
            page.manual_checks_complete_date = form.cleaned_data[
                "page_manual_checks_complete_date"
            ]
            page.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = Audit.objects.get(pk=self.kwargs["audit_id"])
        if "save_get_next_page" in self.request.POST:
            url: str = reverse_lazy(
                "audits:edit-audit-manual-by-page",
                kwargs={
                    "page_id": audit.next_page.id,  # type: ignore
                    "audit_id": audit.id,  # type: ignore
                    "case_id": audit.case.id,  # type: ignore
                },
            )
        elif "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-axe", audit=audit)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=audit)}#audit-manual'  # type: ignore
        return url


class AuditAxeUpdateView(AuditUpdateView):
    """
    View to update axe audits
    """

    form_class: Type[AuditUpdateAxeForm] = AuditUpdateAxeForm
    template_name: str = "audits/forms/axe.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_audit_url(url_name="edit-audit-pdf", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-axe'  # type: ignore
        return url


class AuditPdfUpdateView(AuditUpdateView):
    """
    View to update pdf audits
    """

    form_class: Type[AuditUpdatePdfForm] = AuditUpdatePdfForm
    template_name: str = "audits/forms/pdf.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                self.request.POST
            )
        else:
            page: Page = Page.objects.get(audit=self.object, type=PAGE_TYPE_PDF)
            check_results: QuerySet[CheckResult] = CheckResult.objects.filter(  # type: ignore
                page=page, type=TEST_TYPE_PDF
            )

            check_results_formset: CheckResultUpdateFormset = CheckResultUpdateFormset(
                queryset=check_results
            )
        for check_results_form in check_results_formset.forms:
            check_results_form.fields["failed"].label = ""
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
            url: str = get_audit_url(url_name="edit-audit-pdf", audit=self.object)  # type: ignore
        else:
            url: str = f'{get_audit_url(url_name="audit-detail", audit=self.object)}#audit-pdf'  # type: ignore
        return url
