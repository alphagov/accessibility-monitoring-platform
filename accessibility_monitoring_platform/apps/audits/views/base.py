"""
Views for audits app (called tests by users)
"""
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.db.models.query import Q, QuerySet
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ...cases.models import (
    Case,
    CaseEvent,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_START_RETEST,
)
from ...common.utils import (
    record_model_update_event,
    record_model_create_event,
    amp_format_date,
    get_url_parameters_for_pagination,
    get_id_from_button_name,
)

from ..forms import (
    StatementCheckResultFormset,
    WcagDefinitionSearchForm,
    WcagDefinitionCreateUpdateForm,
    StatementCheckSearchForm,
    StatementCheckCreateUpdateForm,
    StatementPageFormset,
    StatementPageFormsetOneExtra,
)
from ..models import (
    Audit,
    Page,
    WcagDefinition,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
)
from ..utils import (
    create_mandatory_pages_for_new_audit,
    create_statement_checks_for_new_audit,
    report_data_updated,
)


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
    create_statement_checks_for_new_audit(audit=audit)
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


class AuditCaseComplianceUpdateView(AuditUpdateView):
    """
    View to update audit and case compliance fields
    """

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if "case_compliance_form" not in context:
            if self.request.POST:
                case_compliance_form: Form = self.case_compliance_form_class(
                    self.request.POST,
                    instance=self.object.case.compliance,
                    prefix="case-compliance",
                )
            else:
                case_compliance_form: Form = self.case_compliance_form_class(
                    instance=self.object.case.compliance, prefix="case-compliance"
                )
            context["case_compliance_form"] = case_compliance_form
        return context

    def post(
        self, request: HttpRequest, *args: Tuple[str], **kwargs: Dict[str, Any]
    ) -> Union[HttpResponseRedirect, HttpResponse]:
        """Populate two forms from post request"""
        self.object: Audit = self.get_object()
        form: Form = self.form_class(request.POST, instance=self.object)  # type: ignore
        case_compliance_form: Form = self.case_compliance_form_class(
            request.POST, instance=self.object.case.compliance, prefix="case-compliance"
        )
        if form.is_valid() and case_compliance_form.is_valid():
            form.save()
            case_compliance_form.save()
            if "website_compliance_state_initial" in case_compliance_form.changed_data:
                report_data_updated(audit=self.object)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form, case_compliance_form=case_compliance_form
                )
            )


class AuditStatementCheckingView(AuditUpdateView):
    """
    View to do statement checks as part of an audit
    """

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            statement_check_results_formset: StatementCheckResultFormset = (
                StatementCheckResultFormset(self.request.POST)
            )
        else:
            statement_check_results_formset: StatementCheckResultFormset = (
                StatementCheckResultFormset(
                    queryset=StatementCheckResult.objects.filter(
                        audit=self.object, type=self.statement_check_type
                    )
                )
            )

        context["statement_check_results_formset"] = statement_check_results_formset

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()

        statement_check_results_formset: StatementCheckResultFormset = context[
            "statement_check_results_formset"
        ]
        if statement_check_results_formset.is_valid():
            for statement_check_results_form in statement_check_results_formset.forms:
                record_model_update_event(
                    user=self.request.user,
                    model_object=statement_check_results_form.instance,
                )
                statement_check_results_form.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


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
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
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
        record_model_create_event(user=self.request.user, model_object=self.object)
        return reverse("audits:wcag-definition-list")


class WcagDefinitionUpdateView(UpdateView):
    """
    View to update a WCAG definition
    """

    model: Type[WcagDefinition] = WcagDefinition
    form_class: Type[WcagDefinitionCreateUpdateForm] = WcagDefinitionCreateUpdateForm
    template_name: str = "audits/forms/wcag_definition_update.html"
    context_object_name: str = "wcag_definition"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change of WCAG definition"""
        if form.changed_data:
            wcag_definition: WcagDefinition = form.save(commit=False)
            record_model_update_event(
                user=self.request.user, model_object=wcag_definition
            )
        return super().form_valid(form)


class StatementCheckListView(ListView):
    """
    View of list of statement checks
    """

    model: Type[StatementCheck] = StatementCheck
    template_name: str = "audits/statement_check_list.html"
    context_object_name: str = "statement_checks"
    paginate_by: int = 10

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.statement_check_search_form: StatementCheckSearchForm = (
                StatementCheckSearchForm(self.request.GET)
            )
            self.statement_check_search_form.is_valid()
        else:
            self.statement_check_search_form = StatementCheckSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[StatementCheck]:
        """Add filters to queryset"""
        if self.statement_check_search_form.errors:
            return StatementCheck.objects.none()

        if hasattr(self.statement_check_search_form, "cleaned_data"):
            search_str: Optional[
                str
            ] = self.statement_check_search_form.cleaned_data.get(
                "statement_check_search"
            )

            if search_str:
                return StatementCheck.objects.filter(
                    Q(  # pylint: disable=unsupported-binary-operation
                        label__icontains=search_str
                    )
                    | Q(type__icontains=search_str)
                    | Q(success_criteria__icontains=search_str)
                    | Q(report_text__icontains=search_str)
                )

        return StatementCheck.objects.all()

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["statement_check_search_form"] = self.statement_check_search_form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context


class StatementCheckCreateView(CreateView):
    """
    View to create a statement check
    """

    model: Type[StatementCheck] = StatementCheck
    form_class: Type[StatementCheckCreateUpdateForm] = StatementCheckCreateUpdateForm
    template_name: str = "audits/forms/statement_check_create.html"
    context_object_name: str = "statement_check"

    def get_success_url(self) -> str:
        """Return to list of statement checks"""
        record_model_create_event(user=self.request.user, model_object=self.object)
        return reverse("audits:statement-check-list")


class StatementCheckUpdateView(UpdateView):
    """
    View to update a WCAG definition
    """

    model: Type[StatementCheck] = StatementCheck
    form_class: Type[StatementCheckCreateUpdateForm] = StatementCheckCreateUpdateForm
    template_name: str = "audits/forms/statement_check_update.html"
    context_object_name: str = "statement_check"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change of statement check"""
        if form.changed_data:
            self.object: StatementCheck = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)
        return super().form_valid(form)


class StatementPageFormsetUpdateView(AuditUpdateView):
    """
    View to update statement pages
    """

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            statement_pages_formset = StatementPageFormset(self.request.POST)
        else:
            statement_pages: QuerySet[
                StatementPage
            ] = self.object.statementpage_set.filter(is_deleted=False)
            if "add_extra" in self.request.GET:
                statement_pages_formset = StatementPageFormsetOneExtra(
                    queryset=statement_pages
                )
            else:
                statement_pages_formset = StatementPageFormset(queryset=statement_pages)
        context["statement_pages_formset"] = statement_pages_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        statement_pages_formset = context["statement_pages_formset"]
        audit: Audit = form.save(commit=False)
        if statement_pages_formset.is_valid():
            statement_pages: List[StatementPage] = statement_pages_formset.save(
                commit=False
            )
            for statement_page in statement_pages:
                if not statement_page.audit_id:
                    statement_page.audit = audit
                    statement_page.save()
                    record_model_create_event(
                        user=self.request.user, model_object=statement_page
                    )
                else:
                    record_model_update_event(
                        user=self.request.user, model_object=statement_page
                    )
                    statement_page.save()
        else:
            return super().form_invalid(form)
        statement_page_id_to_delete: Optional[int] = get_id_from_button_name(
            button_name_prefix="remove_statement_page_",
            querydict=self.request.POST,
        )
        if statement_page_id_to_delete is not None:
            statement_page_to_delete: statement_page = StatementPage.objects.get(
                id=statement_page_id_to_delete
            )
            statement_page_to_delete.is_deleted = True
            record_model_update_event(
                user=self.request.user, model_object=statement_page_to_delete
            )
            statement_page_to_delete.save()
        return super().form_valid(form)
