"""
Views for audits app (called tests by users)
"""

from typing import Any

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ...common.sitemap import PlatformPage, get_platform_page_by_url_name
from ...common.views import NextPlatformPageMixin
from ...simplified.models import CaseEvent, SimplifiedCase
from ...simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from ..forms import (
    AuditRetestCheckResultFilterForm,
    AuditRetestWcagSummaryUpdateForm,
    AuditStatementSummaryUpdateForm,
    AuditTwelveWeekDisproportionateBurdenUpdateForm,
    StatementAuditComplianceUpdateForm,
    StatementAuditStatementBackupUpdateForm,
    StatementAuditStatementComplianceUpdateForm,
    StatementAuditStatementCustomUpdateForm,
    StatementAuditStatementDisproportionateUpdateForm,
    StatementAuditStatementFeedbackUpdateForm,
    StatementAuditStatementNonAccessibleUpdateForm,
    StatementAuditStatementOverviewUpdateForm,
    StatementAuditStatementPagesUpdateForm,
    StatementAuditStatementPreparationUpdateForm,
    StatementAuditStatementWebsiteUpdateForm,
    StatementCheckResultRetestCreateForm,
    StatementCheckResultRetestCustomUpdateForm,
    StatementCheckResultRetestFormset,
    StatementCheckResultRetestUpdateForm,
    WcagAuditComplianceUpdateForm,
    WcagAuditRetestMetadataUpdateForm,
    WcagAuditRetestPagesUpdateForm,
    WcagAuditWcagSummaryUpdateForm,
    WcagCheckResultRetestFormset,
    WcagPageRetestFormset,
    WcagPageRetestUpdateForm,
)
from ..models import (
    Audit,
    AuditOverview,
    Page,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementCheckResultInitial,
    StatementCheckResultRetest,
    StatementPage,
    WcagAudit,
    WcagCheckResultRetest,
    WcagPageRetest,
)
from ..utils import (
    add_to_check_result_restest_notes_history,
    create_first_twelve_week_statement_audit,
    create_first_twelve_week_wcag_audit,
    get_audit_summary_context,
    get_next_platform_page_twelve_week,
    get_other_pages_with_retest_notes,
)
from .base import (
    AddStatementLinkUpdateView,
    AuditCaseComplianceUpdateView,
    AuditSummaryFirstMixin,
    AuditUpdateView,
    DeleteStatementPageUpdateView,
    StatementAuditUpdateView,
    StatementBackupUpdateView,
    WcagAuditUpdateView,
)


class WcagAuditRetestMetadataUpdateView(WcagAuditUpdateView):

    form_class: type[WcagAuditRetestMetadataUpdateForm] = (
        WcagAuditRetestMetadataUpdateForm
    )
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


class WcagAuditRetestPagesView(WcagAuditUpdateView):

    form_class: type[WcagAuditRetestPagesUpdateForm] = WcagAuditRetestPagesUpdateForm
    template_name: str = "audits/forms/twelve_week_pages.html"

    def get_next_platform_page(self):
        wcag_audit: WcagAudit = self.object
        return get_next_platform_page_twelve_week(wcag_audit=wcag_audit)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        wcag_audit: WcagAudit = self.object
        if self.request.POST:
            audit_retest_pages_formset: WcagPageRetestFormset = WcagPageRetestFormset(
                self.request.POST
            )
        else:
            audit_retest_pages_formset: WcagPageRetestFormset = WcagPageRetestFormset(
                queryset=wcag_audit.wcag_page_retests
            )
        context["audit_retest_pages_formset"] = audit_retest_pages_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        wcag_page_retests_formset: WcagPageRetestFormset = context[
            "audit_retest_pages_formset"
        ]

        if wcag_page_retests_formset.is_valid():
            wcag_page_retests: list[Page] = wcag_page_retests_formset.save(commit=False)
            for wcag_page_retest in wcag_page_retests:
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=wcag_page_retest,
                    simplified_case=wcag_page_retest.wcag_audit.simplified_case,
                )
                wcag_page_retest.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class WcagPageRetestCheckResultsUpdateView(NextPlatformPageMixin, UpdateView):

    model: type[WcagPageRetest] = WcagPageRetest
    form_class: type[WcagPageRetestUpdateForm] = WcagPageRetestUpdateForm
    template_name: str = "audits/forms/twelve_week_wcag_page_retest_checks.html"
    context_object_name: str = "wcag_page_retest"

    def get_next_platform_page(self):
        wcag_page_retest: WcagPageRetest = self.object
        return get_next_platform_page_twelve_week(
            wcag_audit=wcag_page_retest.wcag_audit, current_page=wcag_page_retest
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        wcag_page_retest: WcagPageRetest = self.object
        context["filter_form"] = AuditRetestCheckResultFilterForm(
            initial={
                "fixed": False,
                "not-fixed": False,
                "not-tested": False,
            }
        )
        if self.request.POST:
            check_results_formset: WcagCheckResultRetestFormset = (
                WcagCheckResultRetestFormset(
                    self.request.POST,
                    initial=[
                        check_result.retest_form_initial
                        for check_result in wcag_page_retest.all_wcag_check_result_retests
                    ],
                )
            )
        else:
            check_results_formset: WcagCheckResultRetestFormset = (
                WcagCheckResultRetestFormset(
                    initial=[
                        check_result.retest_form_initial
                        for check_result in wcag_page_retest.all_wcag_check_result_retests
                    ]
                )
            )

        context["check_results_formset"] = check_results_formset
        context["other_pages_with_retest_notes"] = get_other_pages_with_retest_notes(
            wcag_page_retest=wcag_page_retest
        )

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        wcag_page_retest: WcagPageRetest = self.object
        if form.changed_data:
            wcag_page_retest.complete_date = form.cleaned_data["complete_date"]
            wcag_page_retest.page_missing_date = form.cleaned_data["page_missing_date"]
            wcag_page_retest.notes = form.cleaned_data["notes"]
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=wcag_page_retest,
                simplified_case=wcag_page_retest.wcag_audit.simplified_case,
            )
            wcag_page_retest.save()

        check_results_formset: WcagCheckResultRetestFormset = context[
            "check_results_formset"
        ]
        if check_results_formset.is_valid():
            for form in check_results_formset.forms:
                if form.changed_data:
                    wcag_check_result_retest: WcagCheckResultRetest = (
                        WcagCheckResultRetest.objects.get(id=form.cleaned_data["id"])
                    )
                    wcag_check_result_retest.retest_state = form.cleaned_data[
                        "retest_state"
                    ]
                    wcag_check_result_retest.notes = form.cleaned_data["notes"]
                    add_to_check_result_restest_notes_history(
                        wcag_check_result_retest=wcag_check_result_retest,
                        user=self.request.user,
                    )
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=wcag_check_result_retest,
                        simplified_case=wcag_check_result_retest.wcag_audit.simplified_case,
                    )
                    wcag_check_result_retest.save()
        else:
            return super().form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())


class WcagAuditComplianceRetestUpdateView(WcagAuditUpdateView):
    """
    View to retest website compliance fields
    """

    form_class: type[WcagAuditComplianceUpdateForm] = WcagAuditComplianceUpdateForm
    template_name: str = "audits/forms/retest_website_decision.html"

    def get_form(self, form_class=None):
        form = super().get_form()
        form.fields["compliance_state"].label = "12-week website compliance decision"
        return form


class TwelveWeekWcagAuditSummaryFirstUpdateView(
    AuditSummaryFirstMixin, WcagAuditUpdateView
):

    form_class: type[WcagAuditWcagSummaryUpdateForm] = WcagAuditWcagSummaryUpdateForm
    template_name: str = "audits/forms/test_summary_wcag.html"


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


class TwelveWeekAddStatementPageUpdateView(AddStatementLinkUpdateView):
    """View to add statement page in 12-week retest"""

    form_class: type[StatementAuditStatementPagesUpdateForm] = (
        StatementAuditStatementPagesUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_add_statement_link.html"


class TwelveWeekDeleteStatementPageUpdateView(DeleteStatementPageUpdateView):
    """View to delete statement link in 12-week retest"""

    template_name: str = "audits/forms/twelve_week_statement_page_delete.html"

    def get_success_url(self) -> str:
        """Return to the list of statement links"""
        statement_page: StatementPage = self.object
        return reverse(
            "audits:edit-audit-retest-statement-pages",
            kwargs={"pk": statement_page.audit.id},
        )


class TwelveWeekStatementBackupUpdateView(StatementBackupUpdateView):
    """View to backup statement in 12-week retest"""

    form_class: type[StatementAuditStatementBackupUpdateForm] = (
        StatementAuditStatementBackupUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_statement_backup.html"


class StatementCheckResultRetestFormsetView(StatementAuditUpdateView):
    """
    View to do statement checks as part of an audit
    """

    template_name: str = "audits/statement_checks/retest_statement_formset_form.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = self.object

        if self.request.POST:
            statement_check_results_formset: StatementCheckResultRetestFormset = (
                StatementCheckResultRetestFormset(self.request.POST)
            )
        else:
            statement_check_results_formset: StatementCheckResultRetestFormset = (
                StatementCheckResultRetestFormset(
                    queryset=StatementCheckResultRetest.objects.filter(
                        statement_audit=statement_audit,
                        statement_check_result_initial__type=self.statement_check_type,
                    )
                )
            )

        context["statement_check_results_formset"] = statement_check_results_formset

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()

        statement_check_results_formset: StatementCheckResultRetestFormset = context[
            "statement_check_results_formset"
        ]
        if statement_check_results_formset.is_valid():
            for statement_check_results_form in statement_check_results_formset.forms:
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=statement_check_results_form.instance,
                    simplified_case=statement_check_results_form.instance.statement_audit.simplified_case,
                )
                statement_check_results_form.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class TwelveWeekStatementAuditOverviewUpdateView(StatementCheckResultRetestFormsetView):

    form_class: type[StatementAuditStatementOverviewUpdateForm] = (
        StatementAuditStatementOverviewUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_next_platform_page(self) -> PlatformPage:
        statement_audit: StatementAudit = self.object
        if statement_audit.all_overview_statement_checks_have_passed:
            return get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-website",
                instance=statement_audit,
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-retest-statement-custom", instance=statement_audit
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_check_results_formset: StatementCheckResultRetestFormset = context[
            "statement_check_results_formset"
        ]
        for form in statement_check_results_formset.forms:
            form.fields["auditor_information"].label = "12-week retest information"

        statement_audit: StatementAudit = self.object
        context["next_platform_pages"] = [
            get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-website",
                instance=statement_audit,
            ),
            get_platform_page_by_url_name(
                url_name="audits:edit-retest-statement-custom",
                instance=statement_audit,
            ),
        ]
        return context


class AuditRetestStatementWebsiteFormView(StatementCheckResultRetestFormsetView):

    form_class: type[StatementAuditStatementWebsiteUpdateForm] = (
        StatementAuditStatementWebsiteUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.WEBSITE


class AuditRetestStatementComplianceFormView(StatementCheckResultRetestFormsetView):
    """
    View to update statement compliance check results retest
    """

    form_class: type[StatementAuditStatementComplianceUpdateForm] = (
        StatementAuditStatementComplianceUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.COMPLIANCE


class AuditRetestStatementNonAccessibleFormView(StatementCheckResultRetestFormsetView):
    """
    View to update statement non-accessible check results retest
    """

    form_class: type[StatementAuditStatementNonAccessibleUpdateForm] = (
        StatementAuditStatementNonAccessibleUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE


class AuditRetestStatementPreparationFormView(StatementCheckResultRetestFormsetView):
    """
    View to update statement preparation check results retest
    """

    form_class: type[StatementAuditStatementPreparationUpdateForm] = (
        StatementAuditStatementPreparationUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.PREPARATION


class AuditRetestStatementFeedbackFormView(StatementCheckResultRetestFormsetView):
    """
    View to update statement feedback check results retest
    """

    form_class: type[StatementAuditStatementFeedbackUpdateForm] = (
        StatementAuditStatementFeedbackUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.FEEDBACK


class AuditRetestStatementDisproportionateFormView(
    StatementCheckResultRetestFormsetView
):
    """
    View to update statement disproportionate burden check results retest
    """

    form_class: type[StatementAuditStatementDisproportionateUpdateForm] = (
        StatementAuditStatementDisproportionateUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.DISPROPORTIONATE


class AuditRetestStatementCustomFormView(StatementAuditUpdateView):
    """
    View to add/update custom statement issues check results at 12-weeks
    """

    form_class: type[StatementAuditStatementCustomUpdateForm] = (
        StatementAuditStatementCustomUpdateForm
    )
    template_name: str = "audits/statement_checks/retest_statement_other.html"


class StatementCheckResultRetestCustomUpdateView(UpdateView):
    """
    View to update an initial custom issue
    """

    model: type[StatementCheckResultRetest] = StatementCheckResultRetest
    context_object_name: str = "custom_issue"
    form_class: type[StatementCheckResultRetestCustomUpdateForm] = (
        StatementCheckResultRetestCustomUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/retest_initial_custom_issue_update.html"
    )

    def form_valid(self, form: StatementCheckResultRetestCustomUpdateForm):
        """Populate custom issue"""
        custom_issue: StatementCheckResult = form.save(commit=False)
        record_simplified_model_update_event(
            user=self.request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.statement_audit.simplified_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of custom issues"""
        custom_issue: StatementCheckResult = self.object
        url: str = reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": custom_issue.statement_audit.id},
        )
        return f"{url}#{custom_issue.issue_identifier}"


class AuditRetestNew12WeekCustomIssueCreateView(CreateView):
    """
    View to create new 12-week custom issue
    """

    model: type[StatementCheckResultRetest] = StatementCheckResultRetest
    form_class: type[StatementCheckResultRetestCreateForm] = (
        StatementCheckResultRetestCreateForm
    )
    template_name: str = "audits/forms/twelve_week_custom_issue_create.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["statement_audit"] = get_object_or_404(
            StatementAudit, id=self.kwargs.get("statement_audit_id")
        )
        return context

    def form_valid(self, form: StatementCheckResultRetestCreateForm):
        """Populate custom issue"""
        statement_audit: StatementAudit = get_object_or_404(
            StatementAudit, id=self.kwargs.get("statement_audit_id")
        )
        statement_check_result_retest: StatementCheckResultRetest = form.save(
            commit=False
        )
        statement_check_result_retest.statement_audit = statement_audit
        statement_check_result_retest.type = StatementCheck.Type.TWELVE_WEEK
        statement_check_result_retest.check_result_state = (
            StatementCheckResultRetest.Result.NO
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of custom issues"""
        custom_issue: StatementCheckResultRetest = self.object
        record_simplified_model_create_event(
            user=self.request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.statement_audit.simplified_case,
        )
        url: str = reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": custom_issue.statement_audit.id},
        )
        return f"{url}#{custom_issue.issue_identifier}"


class AuditRetestNew12WeekCustomIssueUpdateView(UpdateView):
    """
    View to update a custom issue entered at 12-weeks
    """

    model: type[StatementCheckResultRetest] = StatementCheckResultRetest
    context_object_name: str = "custom_issue"
    form_class: type[StatementCheckResultRetestUpdateForm] = (
        StatementCheckResultRetestUpdateForm
    )
    template_name: str = "audits/forms/new_12_week_custom_issue_update.html"

    def form_valid(self, form: StatementCheckResultRetestUpdateForm):
        """Populate custom issue"""
        custom_issue: StatementCheckResultRetest = form.save(commit=False)
        record_simplified_model_update_event(
            user=self.request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.statement_audit.simplified_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of custom issues"""
        custom_issue: StatementCheckResultRetest = self.object
        url: str = reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": custom_issue.statement_audit.id},
        )
        return f"{url}#{custom_issue.issue_identifier}"


class New12WeekCustomIssueDeleteTemplateView(TemplateView):
    template_name: str = "audits/statement_checks/new_12_week_custom_issue_delete.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add custom issue to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        custom_issue: StatementCheckResultRetest = get_object_or_404(
            StatementCheckResultRetest, id=kwargs.get("pk")
        )
        context["custom_issue"] = custom_issue
        return context


def delete_new_12_week_custom_issue(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark new 12-week custom issue (StatementCheckResult) as deleted"""
    if request.method == "POST":
        custom_issue: StatementCheckResultRetest = get_object_or_404(
            StatementCheckResultRetest, id=pk
        )
        custom_issue.is_deleted = True
        record_simplified_model_update_event(
            user=request.user,
            model_object=custom_issue,
            simplified_case=custom_issue.statement_audit.simplified_case,
        )
        custom_issue.save()
    return redirect(
        reverse(
            "audits:edit-retest-statement-custom",
            kwargs={"pk": custom_issue.statement_audit.id},
        )
    )


class TwelveWeekDisproportionateBurdenUpdateView(StatementAuditUpdateView):

    form_class: type[AuditTwelveWeekDisproportionateBurdenUpdateForm] = (
        AuditTwelveWeekDisproportionateBurdenUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_disproportionate_burden.html"


class AuditRetestCaseComplianceStatement12WeekUpdateView(StatementAuditUpdateView):
    """
    View to retest statement decsion
    """

    form_class: type[StatementAuditComplianceUpdateForm] = (
        StatementAuditComplianceUpdateForm
    )
    template_name: str = "audits/forms/statement_decision.html"


class TwelveWeekStatementSummaryFirstUpdateView(
    AuditSummaryFirstMixin, StatementAuditUpdateView
):
    """
    View to update audit summary for 12-week statement test
    """

    form_class: type[AuditStatementSummaryUpdateForm] = AuditStatementSummaryUpdateForm
    template_name: str = "audits/forms/test_summary_statement.html"


def start_retest(
    request: HttpRequest, pk: int  # pylint: disable=unused-argument
) -> HttpResponse:
    """
    Start audit retest; Redirect to retest metadata page

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of audit_pverview to start retest of

    Returns:
        HttpResponse: Django HttpResponse
    """
    audit_overview: AuditOverview = get_object_or_404(AuditOverview, id=pk)
    simplified_case: SimplifiedCase = audit_overview.simplified_case

    wcag_audit: WcagAudit = create_first_twelve_week_wcag_audit(
        audit_overview=audit_overview
    )
    record_simplified_model_create_event(
        user=request.user, model_object=wcag_audit, simplified_case=simplified_case
    )
    statement_audit: StatementAudit = create_first_twelve_week_statement_audit(
        audit_overview=audit_overview
    )
    record_simplified_model_create_event(
        user=request.user, model_object=statement_audit, simplified_case=simplified_case
    )

    CaseEvent.objects.create(
        simplified_case=simplified_case,
        done_by=request.user,
        event_type=CaseEvent.EventType.START_RETEST,
        message="Started retest",
    )
    return redirect(
        reverse("audits:edit-audit-retest-metadata", kwargs={"pk": wcag_audit.id})
    )
