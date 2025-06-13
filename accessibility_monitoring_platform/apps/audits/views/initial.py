"""
Views for audits app (called tests by users)
"""

from typing import Any

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ...common.forms import AMPChoiceCheckboxWidget
from ...common.mark_deleted_util import mark_object_as_deleted
from ...common.sitemap import PlatformPage, get_platform_page_by_url_name
from ...simplified.models import SimplifiedCase
from ...simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from ..forms import (
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
    CheckResultFormset,
    InitialCustomIssueCreateUpdateForm,
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
    get_audit_summary_context,
    get_next_platform_page_initial,
    get_page_check_results_formset_initial,
    other_page_failed_check_results,
)
from .base import (
    AuditCaseComplianceUpdateView,
    AuditPageChecksBaseFormView,
    AuditStatementCheckingView,
    AuditUpdateView,
    StatementPageFormsetUpdateView,
)


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
    record_simplified_model_update_event(
        user=request.user, model_object=audit, simplified_case=audit.simplified_case
    )
    audit.save()
    redirect_destination: str = request.GET.get(
        "redirect_destination",
        reverse("simplified:case-detail", kwargs={"pk": audit.simplified_case.id}),
    )
    return redirect(redirect_destination)


class AuditMetadataUpdateView(AuditUpdateView):
    """
    View to update audit metadata
    """

    form_class: type[AuditMetadataUpdateForm] = AuditMetadataUpdateForm
    template_name: str = "common/case_form.html"


class AuditPagesUpdateView(AuditUpdateView):
    """
    View to update audit pages page
    """

    form_class: type[AuditPagesUpdateForm] = AuditPagesUpdateForm
    template_name: str = "audits/forms/pages.html"

    def get_next_platform_page(self):
        audit: Audit = self.object
        return get_next_platform_page_initial(audit=audit)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
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
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        standard_pages_formset: AuditStandardPageFormset = context[
            "standard_pages_formset"
        ]
        extra_pages_formset: AuditExtraPageFormset = context["extra_pages_formset"]
        audit: Audit = form.save(commit=False)

        if standard_pages_formset.is_valid():
            pages: list[Page] = standard_pages_formset.save(commit=False)
            for page in pages:
                if page.page_type == Page.Type.STATEMENT and page.url:
                    if audit.statement_pages.count() == 0:
                        # Create first statement link
                        statement_page: StatementPage = StatementPage.objects.create(
                            audit=audit,
                            url=page.url,
                        )
                        record_simplified_model_create_event(
                            user=self.request.user,
                            model_object=statement_page,
                            simplified_case=audit.simplified_case,
                        )
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=page,
                    simplified_case=audit.simplified_case,
                )
                page.save()
        else:
            return super().form_invalid(form)

        if extra_pages_formset.is_valid():
            pages: list[Page] = extra_pages_formset.save(commit=False)
            for page in pages:
                if not page.audit_id:
                    page.audit = audit
                    page.save()
                    record_simplified_model_create_event(
                        user=self.request.user,
                        model_object=page,
                        simplified_case=audit.simplified_case,
                    )
                else:
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=page,
                        simplified_case=audit.simplified_case,
                    )
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
        if "add_extra" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            url: str = reverse("audits:edit-audit-pages", kwargs=audit_pk)
            return f"{url}?add_extra=true#extra-page-1"
        return super().get_success_url()


class AuditPageChecksFormView(AuditPageChecksBaseFormView):
    """View to update check results for a page"""

    form_class: type[AuditPageChecksForm] = AuditPageChecksForm
    template_name: str = "audits/forms/page_checks.html"

    def get_next_platform_page(self):
        page: Page = self.page
        return get_next_platform_page_initial(audit=page.audit, current_page=page)

    def get_form(self):
        """Populate page form"""
        form = super().get_form()
        if "complete_date" in form.fields:
            form.fields["complete_date"].initial = self.page.complete_date
        if "no_errors_date" in form.fields:
            form.fields["no_errors_date"].initial = self.page.no_errors_date
        return form

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Populate formset of all possible WCAGDefinitions, some of which will
        have marching CheckResults
        """
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["filter_form"] = CheckResultFilterForm(
            initial={"manual": False, "axe": False, "pdf": False, "not_tested": False}
        )
        other_pages_failed_check_results: dict[WcagDefinition, list[CheckResult]] = (
            other_page_failed_check_results(page=self.page)
        )
        wcag_definitions: list[WcagDefinition] = list(
            WcagDefinition.objects.on_date(self.page.audit.date_of_test)
        )

        if self.request.POST:
            check_results_formset: CheckResultFormset = CheckResultFormset(
                self.request.POST,
                initial=get_page_check_results_formset_initial(
                    page=self.page, wcag_definitions=wcag_definitions
                ),
            )
        else:
            check_results_formset: CheckResultFormset = CheckResultFormset(
                initial=get_page_check_results_formset_initial(
                    page=self.page, wcag_definitions=wcag_definitions
                )
            )

        for check_results_form in check_results_formset.forms:
            wcag_definition: WcagDefinition = check_results_form.initial[
                "wcag_definition"
            ]
            check_results_form.fields["check_result_state"].label = wcag_definition
            setattr(
                check_results_form,
                "other_pages_failed_check_results",
                other_pages_failed_check_results.get(wcag_definition, []),
            )

        context["check_results_formset"] = check_results_formset

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        page: Page = self.page
        if form.changed_data:
            page.complete_date = form.cleaned_data["complete_date"]
            page.no_errors_date = form.cleaned_data["no_errors_date"]
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=page,
                simplified_case=page.audit.simplified_case,
            )
            page.save()

        check_results_formset: CheckResultFormset = CheckResultFormset(
            self.request.POST
        )
        if check_results_formset.is_valid():
            create_or_update_check_results_for_page(
                user=self.request.user,
                page=page,
                check_result_forms=check_results_formset.forms,
            )
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class AuditCaseComplianceWebsiteInitialUpdateView(AuditCaseComplianceUpdateView):
    """
    View to update website compliance fields
    """

    form_class: type[AuditWebsiteDecisionUpdateForm] = AuditWebsiteDecisionUpdateForm
    case_compliance_form_class: type[CaseComplianceWebsiteInitialUpdateForm] = (
        CaseComplianceWebsiteInitialUpdateForm
    )
    template_name: str = "audits/forms/website_decision.html"


class AuditSummaryUpdateView(AuditUpdateView):
    """
    View to update audit summary
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        return {
            **context,
            **get_audit_summary_context(request=self.request, audit=self.object),
        }


class AuditWcagSummaryUpdateView(AuditSummaryUpdateView):
    """
    View to update audit summary
    """

    form_class: type[AuditWcagSummaryUpdateForm] = AuditWcagSummaryUpdateForm
    template_name: str = "audits/forms/test_summary_wcag.html"


class InitialStatementPageFormsetUpdateView(StatementPageFormsetUpdateView):
    """
    View to update statement pages in initial test
    """

    form_class: type[AuditStatementPagesUpdateForm] = AuditStatementPagesUpdateForm
    template_name: str = "audits/forms/statement_pages_formset.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        for form in context["statement_pages_formset"]:
            if form.instance.id is None:
                form.fields["added_stage"].initial = StatementPage.AddedStage.INITIAL
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "add_statement_page" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            current_url: str = reverse("audits:edit-statement-pages", kwargs=audit_pk)
            return f"{current_url}?add_extra=true#statement-page-None"
        return super().get_success_url()


class AuditStatementOverviewFormView(AuditStatementCheckingView):
    """
    View to update statement overview check results
    """

    form_class: type[AuditStatementOverviewUpdateForm] = (
        AuditStatementOverviewUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_next_platform_page(self) -> PlatformPage:
        audit: Audit = self.object
        if audit.all_overview_statement_checks_have_passed:
            return get_platform_page_by_url_name(
                url_name="audits:edit-statement-website", instance=audit
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-statement-custom", instance=audit
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object
        context["next_platform_pages"] = [
            get_platform_page_by_url_name(
                url_name="audits:edit-statement-website", instance=audit
            ),
            get_platform_page_by_url_name(
                url_name="audits:edit-statement-custom", instance=audit
            ),
        ]
        return context

    def get_success_url(self) -> str:
        """Recalculate Case status"""
        audit: Audit = self.object
        audit.simplified_case.update_case_status()
        return super().get_success_url()


class AuditStatementWebsiteFormView(AuditStatementCheckingView):
    """
    View to update statement information check results
    """

    form_class: type[AuditStatementWebsiteUpdateForm] = AuditStatementWebsiteUpdateForm
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.WEBSITE


class AuditStatementComplianceFormView(AuditStatementCheckingView):
    """
    View to update statement compliance check results
    """

    form_class: type[AuditStatementComplianceUpdateForm] = (
        AuditStatementComplianceUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.COMPLIANCE


class AuditStatementNonAccessibleFormView(AuditStatementCheckingView):
    """
    View to update statement non-accessible check results
    """

    form_class: type[AuditStatementNonAccessibleUpdateForm] = (
        AuditStatementNonAccessibleUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE


class AuditStatementPreparationFormView(AuditStatementCheckingView):
    """
    View to update statement preparation check results
    """

    form_class: type[AuditStatementPreparationUpdateForm] = (
        AuditStatementPreparationUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.PREPARATION


class AuditStatementFeedbackFormView(AuditStatementCheckingView):
    """
    View to update statement feedback check results
    """

    form_class: type[AuditStatementFeedbackUpdateForm] = (
        AuditStatementFeedbackUpdateForm
    )
    template_name: str = "audits/statement_checks/statement_formset_form.html"
    statement_check_type: str = StatementCheck.Type.FEEDBACK


class AuditStatementCustomFormView(AuditUpdateView):
    """
    View to add/update custom statement issues check results
    """

    form_class: type[AuditStatementCustomUpdateForm] = AuditStatementCustomUpdateForm
    template_name: str = "audits/statement_checks/statement_custom.html"


class CustomIssueCreateView(CreateView):
    """
    View to create custom issue
    """

    model: type[StatementCheckResult] = StatementCheckResult
    form_class: type[InitialCustomIssueCreateUpdateForm] = (
        InitialCustomIssueCreateUpdateForm
    )
    template_name: str = "audits/forms/custom_issue_create.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["audit"] = get_object_or_404(Audit, id=self.kwargs.get("audit_id"))
        return context

    def form_valid(self, form: InitialCustomIssueCreateUpdateForm):
        """Populate custom issue"""
        audit: Audit = get_object_or_404(Audit, id=self.kwargs.get("audit_id"))
        statement_check_result: StatementCheckResult = form.save(commit=False)
        statement_check_result.audit = audit
        if statement_check_result.type == StatementCheck.Type.CUSTOM:
            statement_check_result.check_result_state = StatementCheckResult.Result.NO
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of custom issues"""
        custom_issue: StatementCheckResult = self.object
        record_simplified_model_create_event(
            user=self.request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.audit.simplified_case,
        )
        url: str = reverse(
            "audits:edit-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
        return f"{url}#{custom_issue.issue_identifier}"


class InitialCustomIssueUpdateView(UpdateView):
    """
    View to update a custom issue
    """

    model: type[StatementCheckResult] = StatementCheckResult
    context_object_name: str = "custom_issue"
    form_class: type[InitialCustomIssueCreateUpdateForm] = (
        InitialCustomIssueCreateUpdateForm
    )
    template_name: str = "audits/forms/initial_custom_issue_update.html"

    def form_valid(self, form: InitialCustomIssueCreateUpdateForm):
        """Populate custom issue"""
        custom_issue: StatementCheckResult = form.save(commit=False)
        record_simplified_model_update_event(
            user=self.request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.audit.simplified_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of custom issues"""
        custom_issue: StatementCheckResult = self.object
        url: str = reverse(
            "audits:edit-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
        return f"{url}#{custom_issue.issue_identifier}"


class InitialCustomIssueDeleteTemplateView(TemplateView):
    template_name: str = "audits/statement_checks/initial_custom_issue_delete.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add custom issue to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        custom_issue: StatementCheckResult = get_object_or_404(
            StatementCheckResult, id=kwargs.get("pk")
        )
        context["custom_issue"] = custom_issue
        return context


def delete_custom_issue(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark custom issue (StatementCheckResult) as deleted"""
    if request.method == "POST":
        custom_issue: StatementCheckResult = get_object_or_404(
            StatementCheckResult, id=pk
        )
        custom_issue.is_deleted = True
        record_simplified_model_update_event(
            user=request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.audit.simplified_case,
        )
        custom_issue.save()
    return redirect(
        reverse("audits:edit-statement-custom", kwargs={"pk": custom_issue.audit.id})
    )


class InitialDisproportionateBurdenUpdateView(AuditUpdateView):
    """
    View to update initial disproportionate burden fields
    """

    form_class: type[InitialDisproportionateBurdenUpdateForm] = (
        InitialDisproportionateBurdenUpdateForm
    )
    template_name: str = "audits/forms/statement_form.html"


class AuditCaseComplianceStatementInitialUpdateView(AuditCaseComplianceUpdateView):
    """
    View to update statement decision fields
    """

    form_class: type[AuditStatementDecisionUpdateForm] = (
        AuditStatementDecisionUpdateForm
    )
    case_compliance_form_class: type[CaseComplianceStatementInitialUpdateForm] = (
        CaseComplianceStatementInitialUpdateForm
    )
    template_name: str = "audits/forms/statement_decision.html"


class AuditStatementSummaryUpdateView(AuditSummaryUpdateView):
    """
    View to update audit summary
    """

    form_class: type[AuditStatementSummaryUpdateForm] = AuditStatementSummaryUpdateForm
    template_name: str = "audits/forms/test_summary_statement.html"

    def get_next_platform_page(self) -> PlatformPage:
        case: SimplifiedCase = self.object.simplified_case
        next_page_url_name: str = (
            "simplified:edit-create-report"
            if case.report is None
            else "simplified:edit-report-ready-for-qa"
        )
        return get_platform_page_by_url_name(url_name=next_page_url_name, instance=case)
