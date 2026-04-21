"""
Views for audits app (called tests by users)
"""

from typing import Any

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import Q, QuerySet
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from ...cases.models import CaseFile
from ...cases.views import CaseFileUploadMixin
from ...common.utils import (
    amp_format_date,
    get_url_parameters_for_pagination,
    record_common_model_create_event,
    record_common_model_update_event,
)
from ...common.views import NextPlatformPageMixin
from ...simplified.models import CaseEvent, SimplifiedCase
from ...simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from ..forms import (
    DeleteStatementPageUpdateForm,
    StatementBackupForm,
    StatementCheckCreateUpdateForm,
    StatementCheckResultFormset,
    StatementCheckSearchForm,
    StatementLinkForm,
    WcagDefinitionCreateUpdateForm,
    WcagDefinitionSearchForm,
)
from ..models import (
    Audit,
    Page,
    Retest,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagAudit,
    WcagDefinition,
)
from ..utils import (
    create_mandatory_pages_for_new_audit,
    create_statement_checks_for_new_audit,
    report_data_updated,
)


class StatementBackupMixin(CaseFileUploadMixin):
    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            statement_backup_form: StatementBackupForm = StatementBackupForm(
                self.request.POST
            )
        else:
            statement_backup_form: StatementBackupForm = StatementBackupForm()
        context["statement_backup_form"] = statement_backup_form
        return context


def create_audit(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create audit. If one already exists use that instead.

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    simplified_case: SimplifiedCase = get_object_or_404(SimplifiedCase, id=case_id)
    if simplified_case.audit:
        return redirect(
            reverse(
                "audits:edit-audit-metadata", kwargs={"pk": simplified_case.audit.id}
            )
        )
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    record_simplified_model_create_event(
        user=request.user, model_object=audit, simplified_case=simplified_case
    )
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    record_simplified_model_create_event(
        user=request.user, model_object=wcag_audit, simplified_case=simplified_case
    )
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    record_simplified_model_create_event(
        user=request.user, model_object=statement_audit, simplified_case=simplified_case
    )
    create_mandatory_pages_for_new_audit(wcag_audit=wcag_audit)
    create_statement_checks_for_new_audit(audit=audit, statement_audit=statement_audit)
    CaseEvent.objects.create(
        simplified_case=simplified_case,
        done_by=request.user,
        event_type=CaseEvent.EventType.CREATE_AUDIT,
        message="Started test",
    )
    return redirect(reverse("audits:edit-audit-metadata", kwargs={"pk": audit.id}))


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
    record_simplified_model_update_event(
        user=request.user, model_object=page, simplified_case=page.audit.simplified_case
    )
    page.save()
    return redirect(reverse("audits:edit-audit-pages", kwargs={"pk": page.audit.id}))


class AuditUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update audit
    """

    model: type[Audit] = Audit
    context_object_name: str = "audit"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of audit"""
        if form.changed_data:
            self.object: Audit = form.save(commit=False)
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
            old_audit: Audit = Audit.objects.get(id=self.object.id)
            if old_audit.retest_date != self.object.retest_date:
                CaseEvent.objects.create(
                    simplified_case=self.object.simplified_case,
                    done_by=self.request.user,
                    event_type=CaseEvent.EventType.START_RETEST,
                    message=f"Started retest (date set to {amp_format_date(self.object.retest_date)})",
                )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class WcagAuditUpdateView(AuditUpdateView):

    model: type[WcagAudit] = WcagAudit
    context_object_name: str = "wcag_audit"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of audit"""
        if form.changed_data:
            self.object: WcagAudit = form.save(commit=False)
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class AuditPageChecksBaseFormView(NextPlatformPageMixin, FormView):
    """
    View to update check results for a page
    """

    page: Page

    def setup(self, request, *args, **kwargs):
        """Add audit and page objects to view"""
        super().setup(request, *args, **kwargs)
        self.page = Page.objects.get(pk=kwargs["pk"])


class AuditCaseComplianceUpdateView(AuditUpdateView):
    """
    View to update audit and case compliance fields
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        if "case_compliance_form" not in context:
            if self.request.POST:
                case_compliance_form: Form = self.case_compliance_form_class(
                    self.request.POST,
                    instance=self.object.simplified_case.compliance,
                    prefix="case-compliance",
                )
            else:
                case_compliance_form: Form = self.case_compliance_form_class(
                    instance=self.object.simplified_case.compliance,
                    prefix="case-compliance",
                )
            context["case_compliance_form"] = case_compliance_form
        return context

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Populate two forms from post request"""
        self.object: Audit = self.get_object()
        form: Form = self.form_class(request.POST, instance=self.object)  # type: ignore
        case_compliance_form: Form = self.case_compliance_form_class(
            request.POST,
            instance=self.object.simplified_case.compliance,
            prefix="case-compliance",
        )
        if form.is_valid() and case_compliance_form.is_valid():
            form.save()
            case_compliance_form.save()
            audit: Audit = self.object
            audit.simplified_case.update_case_status()
            if "website_compliance_state_initial" in case_compliance_form.changed_data:
                report_data_updated(audit=self.object)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    case_compliance_form=case_compliance_form,
                )
            )


class AuditStatementCheckingView(AuditUpdateView):
    """
    View to do statement checks as part of an audit
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

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
        context: dict[str, Any] = self.get_context_data()

        statement_check_results_formset: StatementCheckResultFormset = context[
            "statement_check_results_formset"
        ]
        if statement_check_results_formset.is_valid():
            for statement_check_results_form in statement_check_results_formset.forms:
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=statement_check_results_form.instance,
                    simplified_case=statement_check_results_form.instance.audit.simplified_case,
                )
                statement_check_results_form.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class WcagDefinitionListView(ListView):
    """
    View of list of WCAG definitions
    """

    model: type[WcagDefinition] = WcagDefinition
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
            search_str: str | None = self.wcag_definition_search_form.cleaned_data.get(
                "wcag_definition_search"
            )

            if search_str:
                return WcagDefinition.objects.filter(
                    Q(  # pylint: disable=unsupported-binary-operation
                        name__icontains=search_str
                    )
                    | Q(type__icontains=search_str)
                    | Q(description__icontains=search_str)
                    | Q(hint__icontains=search_str)
                    | Q(url_on_w3__icontains=search_str)
                    | Q(report_boilerplate__icontains=search_str)
                )

        return WcagDefinition.objects.all()

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["wcag_definition_search_form"] = self.wcag_definition_search_form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context


class WcagDefinitionCreateView(CreateView):
    """
    View to create a WCAG definition
    """

    model: type[WcagDefinition] = WcagDefinition
    form_class: type[WcagDefinitionCreateUpdateForm] = WcagDefinitionCreateUpdateForm
    template_name: str = "audits/forms/wcag_definition_create.html"
    context_object_name: str = "wcag_definition"

    def get_success_url(self) -> str:
        """Return to list of WCAG definitions"""
        record_common_model_create_event(
            user=self.request.user, model_object=self.object
        )
        return reverse("audits:wcag-definition-list")


class WcagDefinitionUpdateView(UpdateView):
    """
    View to update a WCAG definition
    """

    model: type[WcagDefinition] = WcagDefinition
    form_class: type[WcagDefinitionCreateUpdateForm] = WcagDefinitionCreateUpdateForm
    template_name: str = "audits/forms/wcag_definition_update.html"
    context_object_name: str = "wcag_definition"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change of WCAG definition"""
        if form.changed_data:
            wcag_definition: WcagDefinition = form.save(commit=False)
            record_common_model_update_event(
                user=self.request.user, model_object=wcag_definition
            )
        return super().form_valid(form)


class StatementCheckListView(ListView):
    """
    View of list of statement checks
    """

    model: type[StatementCheck] = StatementCheck
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
            search_str: str | None = self.statement_check_search_form.cleaned_data.get(
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

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["statement_check_search_form"] = self.statement_check_search_form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context


class StatementCheckCreateView(CreateView):
    """
    View to create a statement check
    """

    model: type[StatementCheck] = StatementCheck
    form_class: type[StatementCheckCreateUpdateForm] = StatementCheckCreateUpdateForm
    template_name: str = "audits/forms/statement_check_create.html"
    context_object_name: str = "statement_check"

    def get_success_url(self) -> str:
        """Return to list of statement checks"""
        record_common_model_create_event(
            user=self.request.user, model_object=self.object
        )
        return reverse("audits:statement-check-list")


class StatementCheckUpdateView(UpdateView):
    """
    View to update a WCAG definition
    """

    model: type[StatementCheck] = StatementCheck
    form_class: type[StatementCheckCreateUpdateForm] = StatementCheckCreateUpdateForm
    template_name: str = "audits/forms/statement_check_update.html"
    context_object_name: str = "statement_check"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change of statement check"""
        if form.changed_data:
            self.object: StatementCheck = form.save(commit=False)
            record_common_model_update_event(
                user=self.request.user, model_object=self.object
            )
        return super().form_valid(form)


class AddStatementLinkUpdateView(AuditUpdateView):
    """View to add statement page"""

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Add second form to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            statement_link_form: StatementLinkForm = StatementLinkForm(
                self.request.POST
            )
        else:
            statement_link_form: StatementLinkForm = StatementLinkForm()
        context["statement_link_form"] = statement_link_form
        return context

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Populate two forms from post request"""
        self.object: Audit | Retest = self.get_object()
        form: Form = self.form_class(request.POST, instance=self.object)  # type: ignore
        statement_link_form: StatementLinkForm = StatementLinkForm(
            self.request.POST, self.request.FILES
        )
        if form.is_valid() and statement_link_form.is_valid():
            form.save()
            if isinstance(self.object, Retest):
                audit: Audit = self.object.simplified_case.audit
            else:
                audit: Audit = self.object
            statement_url: str = statement_link_form.cleaned_data["statement_url"]
            if statement_url and statement_url != audit.latest_statement_link:
                statement_page: StatementPage = StatementPage.objects.create(
                    audit=audit, url=statement_url
                )
                user: User = self.request.user
                record_simplified_model_create_event(
                    user=user,
                    model_object=statement_page,
                    simplified_case=audit.simplified_case,
                )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    statement_link_form=statement_link_form,
                )
            )


class DeleteStatementPageUpdateView(UpdateView):
    """Mark statement link as deleted"""

    model: type[StatementPage] = StatementPage
    form_class: type[DeleteStatementPageUpdateForm] = DeleteStatementPageUpdateForm
    context_object_name: str = "statement_page"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change of statement check"""
        self.object: StatementPage = form.save(commit=False)
        self.object.is_deleted = True
        record_simplified_model_update_event(
            user=self.request.user,
            model_object=self.object,
            simplified_case=self.object.audit.simplified_case,
        )
        return super().form_valid(form)


class StatementBackupUpdateView(StatementBackupMixin, AuditUpdateView):
    """View to backup statements"""

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Save statement backup and add create event"""
        statement_backup_form: StatementBackupForm = StatementBackupForm(
            self.request.POST, self.request.FILES
        )
        if statement_backup_form.is_valid():
            audit: Audit = self.object
            uploaded_file: InMemoryUploadedFile | None = (
                statement_backup_form.cleaned_data.get("file_to_upload")
            )
            if uploaded_file is not None:
                self.case_file_upload(
                    uploaded_file=uploaded_file,
                    user=self.request.user,
                    base_case=audit.simplified_case,
                    file_type=CaseFile.Type.STATEMENT,
                )
        return super().form_valid(form)
