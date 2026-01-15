"""
Views for audits app (called tests by users)
"""

from datetime import date
from typing import Any

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ...common.sitemap import PlatformPage, get_platform_page_by_url_name
from ...simplified.models import CaseEvent
from ...simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from ..forms import (
    AuditRetestCheckResultFilterForm,
    AuditRetestCheckResultFormset,
    AuditRetestMetadataUpdateForm,
    AuditRetestNew12WeekCustomIssueCreateForm,
    AuditRetestPageChecksForm,
    AuditRetestPageFormset,
    AuditRetestPagesUpdateForm,
    AuditRetestStatementCheckResultFormset,
    AuditRetestStatementComplianceUpdateForm,
    AuditRetestStatementCustomUpdateForm,
    AuditRetestStatementDecisionUpdateForm,
    AuditRetestStatementDisproportionateUpdateForm,
    AuditRetestStatementFeedbackUpdateForm,
    AuditRetestStatementInitialCustomIssueUpdateForm,
    AuditRetestStatementNonAccessibleUpdateForm,
    AuditRetestStatementOverviewUpdateForm,
    AuditRetestStatementPreparationUpdateForm,
    AuditRetestStatementSummaryUpdateForm,
    AuditRetestStatementWebsiteUpdateForm,
    AuditRetestWcagSummaryUpdateForm,
    AuditRetestWebsiteDecisionUpdateForm,
    AuditTwelveWeekDisproportionateBurdenUpdateForm,
    CaseComplianceStatement12WeekUpdateForm,
    CaseComplianceWebsite12WeekUpdateForm,
    New12WeekCustomStatementCheckResultUpdateForm,
    TwelveWeekStatementPagesUpdateForm,
)
from ..models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
)
from ..utils import (
    add_to_check_result_restest_notes_history,
    get_audit_summary_context,
    get_next_platform_page_twelve_week,
    get_other_pages_with_retest_notes,
)
from .base import (
    AuditCaseComplianceUpdateView,
    AuditPageChecksBaseFormView,
    AuditUpdateView,
    StatementPageFormsetUpdateView,
)


class AuditRetestMetadataUpdateView(AuditUpdateView):
    """
    View to update audit retest metadata
    """

    form_class: type[AuditRetestMetadataUpdateForm] = AuditRetestMetadataUpdateForm
    template_name: str = "audits/forms/twelve_week_retest_metadata.html"

    def get_next_platform_page(self):
        audit: Audit = self.object
        if not audit.simplified_case.psb_response:
            return get_platform_page_by_url_name(
                url_name="audits:edit-audit-retest-statement-pages", instance=audit
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-pages", instance=audit
        )


class AuditRetestPagesView(AuditUpdateView):
    """View to retest pages"""

    form_class: type[AuditRetestPagesUpdateForm] = AuditRetestPagesUpdateForm
    template_name: str = "audits/forms/twelve_week_pages.html"

    def get_next_platform_page(self):
        audit: Audit = self.object
        return get_next_platform_page_twelve_week(audit=audit)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object
        if self.request.POST:
            audit_retest_pages_formset: AuditRetestPageFormset = AuditRetestPageFormset(
                self.request.POST
            )
        else:
            audit_retest_pages_formset: AuditRetestPageFormset = AuditRetestPageFormset(
                queryset=audit.testable_pages
            )
        context["audit_retest_pages_formset"] = audit_retest_pages_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        audit_retest_pages_formset: AuditRetestPageFormset = context[
            "audit_retest_pages_formset"
        ]

        if audit_retest_pages_formset.is_valid():
            pages: list[Page] = audit_retest_pages_formset.save(commit=False)
            for page in pages:
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=page,
                    simplified_case=page.audit.simplified_case,
                )
                page.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class AuditRetestPageChecksFormView(AuditPageChecksBaseFormView):
    """
    View to retest check results for a page
    """

    form_class: type[AuditRetestPageChecksForm] = AuditRetestPageChecksForm
    template_name: str = "audits/forms/twelve_week_retest_page_checks.html"

    def get_next_platform_page(self):
        page: Page = self.page
        return get_next_platform_page_twelve_week(audit=page.audit, current_page=page)

    def get_form(self, form_class=None):
        """Populate next page fields"""
        form = super().get_form()
        form.fields["retest_complete_date"].initial = self.page.retest_complete_date
        form.fields["retest_page_missing_date"].initial = (
            self.page.retest_page_missing_date
        )
        form.fields["retest_notes"].initial = self.page.retest_notes
        return form

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["filter_form"] = AuditRetestCheckResultFilterForm(
            initial={
                "fixed": False,
                "not-fixed": False,
                "not-tested": False,
            }
        )
        if self.request.POST:
            check_results_formset: AuditRetestCheckResultFormset = (
                AuditRetestCheckResultFormset(
                    self.request.POST,
                    initial=[
                        check_result.retest_form_initial
                        for check_result in self.page.failed_check_results
                    ],
                )
            )
        else:
            check_results_formset: AuditRetestCheckResultFormset = (
                AuditRetestCheckResultFormset(
                    initial=[
                        check_result.retest_form_initial
                        for check_result in self.page.failed_check_results
                    ]
                )
            )

        context["check_results_formset"] = check_results_formset
        context["other_pages_with_retest_notes"] = get_other_pages_with_retest_notes(
            page=self.page
        )

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        page: Page = self.page
        if form.changed_data:
            page.retest_complete_date = form.cleaned_data["retest_complete_date"]
            page.retest_page_missing_date = form.cleaned_data[
                "retest_page_missing_date"
            ]
            page.retest_notes = form.cleaned_data["retest_notes"]
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=page,
                simplified_case=page.audit.simplified_case,
            )
            page.save()

        check_results_formset: AuditRetestCheckResultFormset = context[
            "check_results_formset"
        ]
        if check_results_formset.is_valid():
            for form in check_results_formset.forms:
                if form.changed_data:
                    check_result: CheckResult = CheckResult.objects.get(
                        id=form.cleaned_data["id"]
                    )
                    check_result.retest_state = form.cleaned_data["retest_state"]
                    check_result.retest_notes = form.cleaned_data["retest_notes"]
                    add_to_check_result_restest_notes_history(
                        check_result=check_result, user=self.request.user
                    )
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=check_result,
                        simplified_case=check_result.audit.simplified_case,
                    )
                    check_result.save()
        else:
            return super().form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())


class AuditRetestCaseComplianceWebsite12WeekUpdateView(AuditCaseComplianceUpdateView):
    """
    View to retest website compliance fields
    """

    form_class: type[AuditRetestWebsiteDecisionUpdateForm] = (
        AuditRetestWebsiteDecisionUpdateForm
    )
    case_compliance_form_class: type[CaseComplianceWebsite12WeekUpdateForm] = (
        CaseComplianceWebsite12WeekUpdateForm
    )
    template_name: str = "audits/forms/retest_website_decision.html"


class AuditRetestSummaryUpdateView(AuditUpdateView):
    """
    View to update audit 12-week retest summary page
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        return {
            **context,
            **get_audit_summary_context(request=self.request, audit=self.object),
        }


class AuditRetestWcagSummaryUpdateView(AuditRetestSummaryUpdateView):
    """
    View to update audit summary for 12-week WCAG test
    """

    form_class: type[AuditRetestWcagSummaryUpdateForm] = (
        AuditRetestWcagSummaryUpdateForm
    )
    template_name: str = "audits/forms/test_summary_wcag.html"


class TwelveWeekStatementPageFormsetUpdateView(StatementPageFormsetUpdateView):
    """
    View to update statement pages in 12-week retest
    """

    form_class: type[TwelveWeekStatementPagesUpdateForm] = (
        TwelveWeekStatementPagesUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_statement_pages_formset.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        for form in context["statement_pages_formset"]:
            if form.instance.id is None:
                form.fields["added_stage"].initial = (
                    StatementPage.AddedStage.TWELVE_WEEK
                )
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "add_statement_page" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            current_url: str = reverse(
                "audits:edit-audit-retest-statement-pages", kwargs=audit_pk
            )
            return f"{current_url}?add_extra=true#statement-page-None"
        return super().get_success_url()


class AuditRetestStatementCheckingView(AuditUpdateView):
    """
    View to do statement checks as part of an audit retest
    """

    template_name: str = "audits/statement_checks/retest_statement_formset_form.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object

        if self.request.POST:
            retest_statement_check_results_formset: (
                AuditRetestStatementCheckResultFormset
            ) = AuditRetestStatementCheckResultFormset(self.request.POST)
        else:
            retest_statement_check_results_formset: (
                AuditRetestStatementCheckResultFormset
            ) = AuditRetestStatementCheckResultFormset(
                queryset=StatementCheckResult.objects.filter(
                    audit=audit, type=self.statement_check_type
                )
            )

        context["retest_statement_check_results_formset"] = (
            retest_statement_check_results_formset
        )

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        audit: Audit = self.object
        if audit.accessibility_statement_found:
            retest_statement_check_results_formset: (
                AuditRetestStatementCheckResultFormset
            ) = context["retest_statement_check_results_formset"]
            if retest_statement_check_results_formset.is_valid():
                for (
                    retest_statement_check_results_form
                ) in retest_statement_check_results_formset.forms:
                    statement_check_result: StatementCheckResult = (
                        retest_statement_check_results_form.save(commit=False)
                    )
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=statement_check_result,
                        simplified_case=statement_check_result.audit.simplified_case,
                    )
                    statement_check_result.save()
            else:
                return super().form_invalid(form)

        return super().form_valid(form)


class AuditRetestStatementOverviewFormView(AuditRetestStatementCheckingView):
    """
    View to update statement overview check results retest
    """

    form_class: type[AuditRetestStatementOverviewUpdateForm] = (
        AuditRetestStatementOverviewUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_next_platform_page(self) -> PlatformPage:
        audit: Audit = self.object
        if audit.all_overview_statement_checks_have_passed:
            return get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-website", instance=audit
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-retest-statement-custom", instance=audit
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        audit: Audit = self.object
        context["next_platform_pages"] = [
            get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-website", instance=audit
            ),
            get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-custom",
                instance=audit,
            ),
        ]
        return context


class AuditRetestStatementWebsiteFormView(AuditRetestStatementCheckingView):
    """
    View to update statement information check results retest
    """

    form_class: type[AuditRetestStatementWebsiteUpdateForm] = (
        AuditRetestStatementWebsiteUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.WEBSITE


class AuditRetestStatementComplianceFormView(AuditRetestStatementCheckingView):
    """
    View to update statement compliance check results retest
    """

    form_class: type[AuditRetestStatementComplianceUpdateForm] = (
        AuditRetestStatementComplianceUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.COMPLIANCE


class AuditRetestStatementNonAccessibleFormView(AuditRetestStatementCheckingView):
    """
    View to update statement non-accessible check results retest
    """

    form_class: type[AuditRetestStatementNonAccessibleUpdateForm] = (
        AuditRetestStatementNonAccessibleUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE


class AuditRetestStatementPreparationFormView(AuditRetestStatementCheckingView):
    """
    View to update statement preparation check results retest
    """

    form_class: type[AuditRetestStatementPreparationUpdateForm] = (
        AuditRetestStatementPreparationUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.PREPARATION


class AuditRetestStatementFeedbackFormView(AuditRetestStatementCheckingView):
    """
    View to update statement feedback check results retest
    """

    form_class: type[AuditRetestStatementFeedbackUpdateForm] = (
        AuditRetestStatementFeedbackUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.FEEDBACK


class AuditRetestStatementDisproportionateFormView(AuditRetestStatementCheckingView):
    """
    View to update statement disproportionate burden check results retest
    """

    form_class: type[AuditRetestStatementDisproportionateUpdateForm] = (
        AuditRetestStatementDisproportionateUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.DISPROPORTIONATE


class AuditRetestStatementCustomFormView(AuditUpdateView):
    """
    View to add/update custom statement issues check results at 12-weeks
    """

    form_class: type[AuditRetestStatementCustomUpdateForm] = (
        AuditRetestStatementCustomUpdateForm
    )
    template_name: str = "audits/statement_checks/retest_statement_other.html"


class AuditRetestInitialCustomIssueUpdateView(UpdateView):
    """
    View to update an initial custom issue
    """

    model: type[StatementCheckResult] = StatementCheckResult
    context_object_name: str = "custom_issue"
    form_class: type[AuditRetestStatementInitialCustomIssueUpdateForm] = (
        AuditRetestStatementInitialCustomIssueUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/retest_initial_custom_issue_update.html"
    )

    def form_valid(self, form: AuditRetestStatementInitialCustomIssueUpdateForm):
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
            "audits:edit-retest-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
        return f"{url}#{custom_issue.issue_identifier}"


class AuditRetestNew12WeekCustomIssueCreateView(CreateView):
    """
    View to create new 12-week custom issue
    """

    model: type[StatementCheckResult] = StatementCheckResult
    form_class: type[AuditRetestNew12WeekCustomIssueCreateForm] = (
        AuditRetestNew12WeekCustomIssueCreateForm
    )
    template_name: str = "audits/forms/custom_issue_create.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["audit"] = get_object_or_404(Audit, id=self.kwargs.get("audit_id"))
        return context

    def form_valid(self, form: AuditRetestNew12WeekCustomIssueCreateForm):
        """Populate custom issue"""
        audit: Audit = get_object_or_404(Audit, id=self.kwargs.get("audit_id"))
        statement_check_result: StatementCheckResult = form.save(commit=False)
        statement_check_result.audit = audit
        statement_check_result.type = StatementCheck.Type.TWELVE_WEEK
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
            "audits:edit-retest-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
        return f"{url}#{custom_issue.issue_identifier}"


class AuditRetestNew12WeekCustomIssueUpdateView(UpdateView):
    """
    View to update a custom issue
    """

    model: type[StatementCheckResult] = StatementCheckResult
    context_object_name: str = "custom_issue"
    form_class: type[New12WeekCustomStatementCheckResultUpdateForm] = (
        New12WeekCustomStatementCheckResultUpdateForm
    )
    template_name: str = "audits/forms/new_12_week_custom_issue_update.html"

    def form_valid(self, form: New12WeekCustomStatementCheckResultUpdateForm):
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
            "audits:edit-retest-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
        return f"{url}#{custom_issue.issue_identifier}"


class New12WeekCustomIssueDeleteTemplateView(TemplateView):
    template_name: str = "audits/statement_checks/new_12_week_custom_issue_delete.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add custom issue to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        custom_issue: StatementCheckResult = get_object_or_404(
            StatementCheckResult, id=kwargs.get("pk")
        )
        context["custom_issue"] = custom_issue
        return context


def delete_new_12_week_custom_issue(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark new 12-week custom issue (StatementCheckResult) as deleted"""
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
        reverse(
            "audits:edit-retest-statement-custom", kwargs={"pk": custom_issue.audit.id}
        )
    )


class TwelveWeekDisproportionateBurdenUpdateView(AuditUpdateView):
    """
    View to update 12-week disproportionate burden fields
    """

    form_class: type[AuditTwelveWeekDisproportionateBurdenUpdateForm] = (
        AuditTwelveWeekDisproportionateBurdenUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_disproportionate_burden.html"


class AuditRetestCaseComplianceStatement12WeekUpdateView(AuditCaseComplianceUpdateView):
    """
    View to retest statement decsion
    """

    form_class: type[AuditRetestStatementDecisionUpdateForm] = (
        AuditRetestStatementDecisionUpdateForm
    )
    case_compliance_form_class: type[CaseComplianceStatement12WeekUpdateForm] = (
        CaseComplianceStatement12WeekUpdateForm
    )
    template_name: str = "audits/forms/retest_statement_decision.html"


class AuditRetestStatementSummaryUpdateView(AuditRetestSummaryUpdateView):
    """
    View to update audit summary for 12-week WCAG test
    """

    form_class: type[AuditRetestStatementSummaryUpdateForm] = (
        AuditRetestStatementSummaryUpdateForm
    )
    template_name: str = "audits/forms/test_summary_statement.html"


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
    record_simplified_model_update_event(
        user=request.user, model_object=audit, simplified_case=audit.simplified_case
    )
    audit.save()
    CaseEvent.objects.create(
        simplified_case=audit.simplified_case,
        done_by=request.user,
        event_type=CaseEvent.EventType.START_RETEST,
        message="Started retest",
    )
    return redirect(reverse("audits:edit-audit-retest-metadata", kwargs={"pk": pk}))
