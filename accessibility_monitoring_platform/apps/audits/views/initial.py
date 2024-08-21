"""
Views for audits app (called tests by users)
"""

from functools import partial
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView

from ...cases.models import Contact
from ...common.case_nav import CaseNavContextMixin
from ...common.form_extract_utils import extract_form_labels_and_values
from ...common.forms import AMPChoiceCheckboxWidget
from ...common.utils import (
    list_to_dictionary_of_lists,
    mark_object_as_deleted,
    record_model_create_event,
    record_model_update_event,
)
from ..forms import (
    ArchiveAuditReportOptionsUpdateForm,
    ArchiveAuditStatement1UpdateForm,
    ArchiveAuditStatement2UpdateForm,
    AuditExtraPageFormset,
    AuditExtraPageFormsetOneExtra,
    AuditExtraPageFormsetTwoExtra,
    AuditMetadataUpdateForm,
    AuditPageChecksForm,
    AuditPagesUpdateForm,
    AuditStandardPageFormset,
    AuditStatementComplianceUpdateForm,
    AuditStatementCustomUpdateForm,
    AuditStatementDecisionUpdateForm,
    AuditStatementFeedbackUpdateForm,
    AuditStatementNonAccessibleUpdateForm,
    AuditStatementOverviewUpdateForm,
    AuditStatementPagesUpdateForm,
    AuditStatementPreparationUpdateForm,
    AuditStatementSummaryUpdateForm,
    AuditStatementWebsiteUpdateForm,
    AuditWcagSummaryUpdateForm,
    AuditWebsiteDecisionUpdateForm,
    CaseComplianceStatementInitialUpdateForm,
    CaseComplianceWebsiteInitialUpdateForm,
    CheckResultFilterForm,
    CheckResultForm,
    CheckResultFormset,
    CustomStatementCheckResultFormset,
    CustomStatementCheckResultFormsetOneExtra,
    InitialDisproportionateBurdenUpdateForm,
)
from ..models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)
from ..utils import (
    create_or_update_check_results_for_page,
    get_all_possible_check_results_for_page,
    get_initial_test_view_sections,
    get_next_page_url,
    other_page_failed_check_results,
    report_data_updated,
)
from .base import (
    AuditCaseComplianceUpdateView,
    AuditStatementCheckingView,
    AuditUpdateView,
    StatementPageFormsetUpdateView,
)

STANDARD_PAGE_HEADERS: List[str] = [
    "Home",
    "Contact",
    "A Form",
    "PDF",
    "Accessibility Statement",
]


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
            **{"view_sections": get_initial_test_view_sections(audit=audit)},
            **context,
        }


class AuditInitialWcagUpdateView(AuditUpdateView, CaseNavContextMixin):
    """Populate context for initial WCAG test views"""

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["current_section_name"] = "Initial WCAG test"
        return context


class AuditMetadataUpdateView(AuditInitialWcagUpdateView):
    """
    View to update audit metadata
    """

    form_class: Type[AuditMetadataUpdateForm] = AuditMetadataUpdateForm
    template_name: str = "common/case_form.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-pages", kwargs=audit_pk)
        return super().get_success_url()


class AuditPagesUpdateView(AuditInitialWcagUpdateView):
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
            if form.instance.page_type == Page.Type.FORM:
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
                if page.page_type == Page.Type.STATEMENT and page.url:
                    if audit.statement_pages.count() == 0:
                        # Create first statement link
                        statement_page: StatementPage = StatementPage.objects.create(
                            audit=audit,
                            url=page.url,
                        )
                        record_model_create_event(
                            user=self.request.user, model_object=statement_page
                        )
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

        mark_object_as_deleted(
            request=self.request,
            delete_button_prefix="remove_extra_page_",
            object_to_delete_model=Page,
        )

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


class AuditPageChecksFormView(CaseNavContextMixin, FormView):
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
        context["case"] = self.page.audit.case
        context["filter_form"] = CheckResultFilterForm(
            initial={"manual": False, "axe": False, "pdf": False, "not_tested": False}
        )
        other_pages_failed_check_results: Dict[WcagDefinition, List[CheckResult]] = (
            other_page_failed_check_results(page=self.page)
        )
        wcag_definitions: List[WcagDefinition] = list(
            WcagDefinition.objects.on_date(self.page.audit.date_of_test)
        )

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
        if form.changed_data:
            page.complete_date = form.cleaned_data["complete_date"]
            page.no_errors_date = form.cleaned_data["no_errors_date"]
            record_model_update_event(user=self.request.user, model_object=page)
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


class AuditCaseComplianceWebsiteInitialUpdateView(AuditCaseComplianceUpdateView):
    """
    View to update website compliance fields
    """

    form_class: Type[AuditWebsiteDecisionUpdateForm] = AuditWebsiteDecisionUpdateForm
    case_compliance_form_class: Type[CaseComplianceWebsiteInitialUpdateForm] = (
        CaseComplianceWebsiteInitialUpdateForm
    )
    template_name: str = "audits/forms/website_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: Dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-audit-wcag-summary", kwargs=audit_pk)
        return super().get_success_url()


class AuditSummaryUpdateView(AuditUpdateView):
    """
    View to update audit summary
    """

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
            form=ArchiveAuditStatement1UpdateForm()
        ) + get_audit_rows(form=ArchiveAuditStatement2UpdateForm())

        return context


class AuditWcagSummaryUpdateView(AuditInitialWcagUpdateView, AuditSummaryUpdateView):
    """
    View to update audit summary
    """

    form_class: Type[AuditWcagSummaryUpdateForm] = AuditWcagSummaryUpdateForm
    template_name: str = "audits/forms/test_summary.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            return reverse("audits:edit-statement-pages", kwargs={"pk": audit.id})
        return super().get_success_url()


class AuditInitialStatementUpdateView(AuditUpdateView, CaseNavContextMixin):
    """Populate context for initial statement test views"""

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["current_section_name"] = "Initial statement"
        return context


class InitialStatementPageFormsetUpdateView(StatementPageFormsetUpdateView):
    """
    View to update statement pages in initial test
    """

    form_class: Type[AuditStatementPagesUpdateForm] = AuditStatementPagesUpdateForm
    template_name: str = "audits/forms/statement_pages_formset.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        for form in context["statement_pages_formset"]:
            if form.instance.id is None:
                form.fields["added_stage"].initial = StatementPage.AddedStage.INITIAL
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.object
        audit_pk: Dict[str, int] = {"pk": audit.id}
        current_url: str = reverse("audits:edit-statement-pages", kwargs=audit_pk)
        if "save_continue" in self.request.POST:
            if audit.uses_statement_checks:
                return reverse("audits:edit-statement-overview", kwargs=audit_pk)
            return reverse("audits:edit-audit-statement-1", kwargs=audit_pk)
        elif "add_statement_page" in self.request.POST:
            return f"{current_url}?add_extra=true#statement-page-None"
        else:
            return current_url


class AuditStatementOverviewFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement overview check results
    """

    form_class: Type[AuditStatementOverviewUpdateForm] = (
        AuditStatementOverviewUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit: Audit = self.object
        audit.case.status.calculate_and_save_status()
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": audit.id}
            if audit.all_overview_statement_checks_have_passed:
                return reverse("audits:edit-statement-website", kwargs=audit_pk)
            return reverse(
                "audits:edit-initial-disproportionate-burden", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditStatementWebsiteFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement information check results
    """

    form_class: Type[AuditStatementWebsiteUpdateForm] = AuditStatementWebsiteUpdateForm
    template_name: str = "audits/statement_checks/statement_subpage_formset_form.html"
    statement_check_type: str = StatementCheck.Type.WEBSITE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-compliance", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementComplianceFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement compliance check results
    """

    form_class: Type[AuditStatementComplianceUpdateForm] = (
        AuditStatementComplianceUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_subpage_formset_form.html"
    statement_check_type: str = StatementCheck.Type.COMPLIANCE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-non-accessible", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementNonAccessibleFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement non-accessible check results
    """

    form_class: Type[AuditStatementNonAccessibleUpdateForm] = (
        AuditStatementNonAccessibleUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_subpage_formset_form.html"
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-preparation", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementPreparationFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement preparation check results
    """

    form_class: Type[AuditStatementPreparationUpdateForm] = (
        AuditStatementPreparationUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_subpage_formset_form.html"
    statement_check_type: str = StatementCheck.Type.PREPARATION

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-feedback", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementFeedbackFormView(
    AuditInitialStatementUpdateView, AuditStatementCheckingView
):
    """
    View to update statement feedback check results
    """

    form_class: Type[AuditStatementFeedbackUpdateForm] = (
        AuditStatementFeedbackUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_subpage_formset_form.html"
    statement_check_type: str = StatementCheck.Type.FEEDBACK

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-custom", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementCustomFormsetView(AuditInitialStatementUpdateView, AuditUpdateView):
    """
    View to add/update custom statement issues check results
    """

    form_class: Type[AuditStatementCustomUpdateForm] = AuditStatementCustomUpdateForm
    template_name: str = "audits/statement_checks/statement_custom.html"
    statement_check_type: str = StatementCheck.Type.CUSTOM

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            custom_formset = CustomStatementCheckResultFormset(self.request.POST)
        else:
            statement_check_results: QuerySet[Contact] = (
                self.object.custom_statement_check_results
            )
            if "add_custom" in self.request.GET:
                custom_formset = CustomStatementCheckResultFormsetOneExtra(
                    queryset=statement_check_results
                )
            else:
                custom_formset = CustomStatementCheckResultFormset(
                    queryset=statement_check_results
                )
        context["custom_formset"] = custom_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        custom_formset = context["custom_formset"]
        audit: Audit = form.save(commit=False)
        if custom_formset.is_valid():
            custom_statement_check_results: List[StatementCheckResult] = (
                custom_formset.save(commit=False)
            )
            for custom_statement_check_result in custom_statement_check_results:
                if not custom_statement_check_result.audit_id:
                    custom_statement_check_result.audit = audit
                    custom_statement_check_result.check_result_state = (
                        StatementCheckResult.Result.NO
                    )
                    custom_statement_check_result.save()
                    record_model_create_event(
                        user=self.request.user,
                        model_object=custom_statement_check_result,
                    )
                else:
                    record_model_update_event(
                        user=self.request.user,
                        model_object=custom_statement_check_result,
                    )
                    custom_statement_check_result.save()
        else:
            return super().form_invalid(form)
        mark_object_as_deleted(
            request=self.request,
            delete_button_prefix="remove_custom_",
            object_to_delete_model=StatementCheckResult,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        audit_pk: Dict[str, int] = {"pk": self.object.id}
        if "save" in self.request.POST:
            return super().get_success_url()
        if "save_continue" in self.request.POST:
            return reverse(
                "audits:edit-initial-disproportionate-burden", kwargs=audit_pk
            )
        elif "add_custom" in self.request.POST:
            return f"{reverse('audits:edit-statement-custom', kwargs=audit_pk)}?add_custom=true#custom-None"
        return f"{reverse('audits:edit-statement-custom', kwargs=audit_pk)}"


class InitialDisproportionateBurdenUpdateView(
    AuditInitialStatementUpdateView, AuditUpdateView
):
    """
    View to update initial disproportionate burden fields
    """

    form_class: Type[InitialDisproportionateBurdenUpdateForm] = (
        InitialDisproportionateBurdenUpdateForm
    )
    template_name: str = "audits/forms/statement_form.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: Dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-statement-decision", kwargs=audit_pk)
        return super().get_success_url()


class AuditCaseComplianceStatementInitialUpdateView(
    AuditInitialStatementUpdateView, AuditCaseComplianceUpdateView
):
    """
    View to update statement decision fields
    """

    form_class: Type[AuditStatementDecisionUpdateForm] = (
        AuditStatementDecisionUpdateForm
    )
    case_compliance_form_class: Type[CaseComplianceStatementInitialUpdateForm] = (
        CaseComplianceStatementInitialUpdateForm
    )
    template_name: str = "audits/forms/statement_decision.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-statement-summary", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatement1UpdateView(AuditInitialStatementUpdateView, AuditUpdateView):
    """
    View to update accessibility statement 1 audit fields
    """

    form_class: Type[ArchiveAuditStatement1UpdateForm] = (
        ArchiveAuditStatement1UpdateForm
    )
    template_name: str = "audits/forms/statement_1.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        if "add_contact_email" in form.changed_data:
            contact: Contact = Contact.objects.create(
                case=self.object.case,
                email=form.cleaned_data["add_contact_email"],
            )
            record_model_create_event(user=self.request.user, model_object=contact)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-statement-2", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatement2UpdateView(AuditInitialStatementUpdateView, AuditUpdateView):
    """
    View to update accessibility statement 2 audit fields
    """

    form_class: Type[ArchiveAuditStatement2UpdateForm] = (
        ArchiveAuditStatement2UpdateForm
    )
    template_name: str = "audits/forms/statement_2.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-statement-decision", kwargs=audit_pk)
        return super().get_success_url()


class AuditReportOptionsUpdateView(AuditUpdateView):
    """
    View to update report options
    """

    form_class: Type[ArchiveAuditReportOptionsUpdateForm] = (
        ArchiveAuditReportOptionsUpdateForm
    )
    template_name: str = "audits/forms/report_options.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        changed_report_data: List[str] = [
            field_name
            for field_name in form.changed_data
            if field_name != "archive_audit_report_options_complete_date"
        ]
        if changed_report_data:
            report_data_updated(audit=self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-wcag-summary", kwargs=audit_pk)
        return super().get_success_url()


class AuditStatementSummaryUpdateView(
    AuditInitialStatementUpdateView, AuditSummaryUpdateView
):
    """
    View to update audit summary
    """

    form_class: Type[AuditStatementSummaryUpdateForm] = AuditStatementSummaryUpdateForm
    template_name: str = "audits/forms/test_summary.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            case_pk: Dict[str, int] = {"pk": audit.case.id}
            return reverse("cases:edit-report-details", kwargs=case_pk)
        return super().get_success_url()
