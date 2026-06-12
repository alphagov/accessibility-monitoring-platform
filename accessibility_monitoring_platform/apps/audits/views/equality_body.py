"""
Views for audits app (called tests by users)
"""

from typing import Any

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ...cases.models import CaseFile
from ...common.mark_deleted_util import mark_object_as_deleted
from ...common.models import Boolean
from ...common.sitemap import PlatformPage, get_platform_page_by_url_name
from ...common.utils import list_to_dictionary_of_lists
from ...common.views import NextPlatformPageMixin
from ...simplified.models import SimplifiedCase
from ...simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from ..forms import (
    EqualityBodyRetestStatementCheckResultRoundFormset,
    EqualityBodyRetestStatementOverviewUpdateForm,
    EqualityBodyWcagPageRetestUpdateForm,
    RetestAddStatementPageUpdateForm,
    RetestComparisonUpdateForm,
    RetestComplianceUpdateForm,
    RetestDisproportionateBurdenUpdateForm,
    RetestStatementBackupUpdateForm,
    RetestStatementComplianceUpdateForm,
    RetestStatementCustomCheckResultFormset,
    RetestStatementCustomCheckResultFormsetOneExtra,
    RetestStatementCustomUpdateForm,
    RetestStatementDecisionUpdateForm,
    RetestStatementDisproportionateUpdateForm,
    RetestStatementFeedbackUpdateForm,
    RetestStatementNonAccessibleUpdateForm,
    RetestStatementPreparationUpdateForm,
    RetestStatementResultsUpdateForm,
    RetestStatementWebsiteUpdateForm,
    StatementBackupForm,
    WcagAuditRetestUpdateForm,
    WcagCheckResultRetestFormset,
)
from ..models import (
    AuditOverview,
    Retest,
    RetestStatementCheckResult,
    StatementAudit,
    StatementCheck,
    StatementCheckResultRound,
    WcagAudit,
    WcagCheckResultRetest,
    WcagPageInitial,
    WcagPageRetest,
)
from ..utils import (
    add_to_check_result_restest_notes_history,
    build_equality_body_retest_context_data,
    create_checkresults_for_wcag_audit_retest,
    create_statement_audit_and_check_results,
    get_next_platform_page_equality_body,
)
from .base import (
    AddStatementLinkUpdateView,
    DeleteStatementPageUpdateView,
    StatementBackupMixin,
)


def create_equality_body_retest(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create retest requested by equality body.

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    simplified_case: SimplifiedCase = get_object_or_404(SimplifiedCase, id=case_id)
    wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
    )
    record_simplified_model_create_event(
        user=request.user, model_object=wcag_audit, simplified_case=simplified_case
    )
    create_checkresults_for_wcag_audit_retest(wcag_audit=wcag_audit)
    statement_audit: StatementAudit = create_statement_audit_and_check_results(
        audit_overview=simplified_case.audit_overview,
        audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY,
    )
    record_simplified_model_create_event(
        user=request.user,
        model_object=statement_audit,
        simplified_case=simplified_case,
    )
    return redirect(
        reverse("audits:retest-metadata-update", kwargs={"pk": wcag_audit.id})
    )


def mark_retest_as_deleted(request: HttpRequest, pk: int) -> HttpResponse:
    """Set Retest.is_deleted to True"""
    retest: Retest = get_object_or_404(Retest, id=pk)
    retest.is_deleted = True
    record_simplified_model_update_event(
        user=request.user, model_object=retest, simplified_case=retest.simplified_case
    )
    retest.save()
    return redirect(
        reverse(
            "simplified:edit-retest-overview", kwargs={"pk": retest.simplified_case.id}
        )
    )


class EqualityBodyRetestWcagAuditUpdateView(NextPlatformPageMixin, UpdateView):

    model: type[WcagAudit] = WcagAudit
    context_object_name: str = "wcag_audit"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        wcag_audit: WcagAudit = self.object
        context.update(build_equality_body_retest_context_data(wcag_audit=wcag_audit))
        return context

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: WcagAudit = form.save(commit=False)
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestMetadataUpdateView(EqualityBodyRetestWcagAuditUpdateView):
    """
    View to update a equality body retest metadata
    """

    form_class: type[WcagAuditRetestUpdateForm] = WcagAuditRetestUpdateForm
    template_name: str = "audits/forms/equality_body_retest_metadata_update.html"

    def get_next_platform_page(self) -> PlatformPage:
        return get_next_platform_page_equality_body(wcag_audit=self.object)


class RetestPageChecksFormView(NextPlatformPageMixin, UpdateView):
    """
    View to update check results for a page in a retest requested by an equality body
    """

    model: type[WcagPageRetest] = WcagPageRetest
    form_class: type[EqualityBodyWcagPageRetestUpdateForm] = (
        EqualityBodyWcagPageRetestUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_page_checks.html"
    context_object_name: str = "wcag_page_retest"

    def get_next_platform_page(self):
        wcag_page_retest: WcagPageRetest = self.object
        return get_next_platform_page_equality_body(
            wcag_audit=wcag_page_retest.wcag_audit, current_page=wcag_page_retest
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        wcag_page_retest: WcagPageRetest = self.object
        wcag_audit: WcagAudit = wcag_page_retest.wcag_audit
        audit_overview: AuditOverview = wcag_audit.simplified_case.audit_overview

        context["case"] = wcag_audit.simplified_case
        context["wcag_audit_initial"] = audit_overview.wcag_audit_initial
        context["first_wcag_audit_12_week_retest"] = (
            audit_overview.first_wcag_audit_12_week_retest
        )
        context["wcag_audit"] = wcag_audit
        context["statement_audit"] = (
            wcag_audit.equivalent_equality_body_statement_retest
        )

        if self.request.POST:
            retest_check_results_formset: WcagCheckResultRetestFormset = (
                WcagCheckResultRetestFormset(self.request.POST)
            )
        else:
            retest_check_results_formset: WcagCheckResultRetestFormset = (
                WcagCheckResultRetestFormset(
                    queryset=wcag_page_retest.all_wcag_check_result_retests
                )
            )

        context["retest_check_results_formset"] = retest_check_results_formset

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        if form.changed_data:
            wcag_page_retest: WcagPageRetest = form.save(commit=False)
            if form.cleaned_data["page_missing_date"]:
                wcag_page_initial: WcagPageInitial = wcag_page_retest.wcag_page_initial
                wcag_page_initial.not_found = Boolean.YES
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=wcag_page_initial,
                    simplified_case=wcag_page_initial.wcag_audit.simplified_case,
                )
                wcag_page_initial.save()
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=wcag_page_retest,
                simplified_case=wcag_page_retest.wcag_audit.simplified_case,
            )

        retest_check_results_formset: WcagCheckResultRetestFormset = context[
            "retest_check_results_formset"
        ]
        if retest_check_results_formset.is_valid():
            for retest_check_result_form in retest_check_results_formset.forms:
                if retest_check_result_form.changed_data:
                    wcag_check_result_retest: WcagCheckResultRetest = (
                        retest_check_result_form.save(commit=False)
                    )
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

        return super().form_valid(form)


class RetestComparisonUpdateView(EqualityBodyRetestWcagAuditUpdateView):

    form_class: type[RetestComparisonUpdateForm] = RetestComparisonUpdateForm
    template_name: str = "audits/forms/equality_body_retest_comparison_update.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        wcag_audit: WcagAudit = self.object

        hide_fixed = "hide-fixed" in self.request.GET
        context["hide_fixed"] = hide_fixed

        retest_check_results: QuerySet[WcagCheckResultRetest] = (
            wcag_audit.wcag_unfixed_check_result_retests
            if hide_fixed
            else wcag_audit.wcag_check_result_retests
        )

        view_url_param: str | None = self.request.GET.get("view")
        show_failures_by_wcag: bool = view_url_param == "WCAG view"
        context["show_failures_by_wcag"] = show_failures_by_wcag

        if show_failures_by_wcag:
            context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                items=retest_check_results, group_by_attr="wcag_definition"
            )

        context["missing_pages"] = wcag_audit.missing_wcag_page_retests

        return context

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)

            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestComplianceUpdateView(EqualityBodyRetestWcagAuditUpdateView):
    """
    View to update a equality body retest compliance
    """

    form_class: type[RetestComplianceUpdateForm] = RetestComplianceUpdateForm
    template_name: str = "audits/forms/equality_body_retest_compliance_update.html"


class EqualityBodyRetestStatementAuditUpdateView(NextPlatformPageMixin, UpdateView):

    model: type[StatementAudit] = StatementAudit
    context_object_name: str = "wcag_audit"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = self.object
        context.update(
            build_equality_body_retest_context_data(statement_audit=statement_audit)
        )
        return context

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: StatementAudit = form.save(commit=False)
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestAddStatementPageUpdateView(
    EqualityBodyRetestStatementAuditUpdateView, AddStatementLinkUpdateView
):
    """
    View to add statement link in equality body-requested retest
    """

    form_class: type[RetestAddStatementPageUpdateForm] = (
        RetestAddStatementPageUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_add_statement_link.html"


class RetestDeleteStatementPageUpdateView(DeleteStatementPageUpdateView):
    """View to delete statement link in equality body-requested retest"""

    template_name: str = "audits/forms/equality_body_retest_statement_page_delete.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add retest to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = get_object_or_404(
            StatementAudit, id=self.kwargs.get("statement_audit_id")
        )
        context.update(
            build_equality_body_retest_context_data(statement_audit=statement_audit)
        )
        return context

    def get_success_url(self) -> str:
        """Return to the list of statement links"""
        statement_audit: StatementAudit = get_object_or_404(
            StatementAudit, id=self.kwargs.get("statement_audit_id")
        )
        return reverse(
            "audits:edit-equality-body-statement-pages",
            kwargs={"pk": statement_audit.id},
        )


class RetestStatementBackupUpdateView(
    StatementBackupMixin, EqualityBodyRetestStatementAuditUpdateView
):
    """View to add statement backup in equality body-requested retest"""

    form_class: type[RetestStatementBackupUpdateForm] = RetestStatementBackupUpdateForm
    template_name: str = "audits/forms/equality_body_retest_statement_backup.html"

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Populate two forms from post request"""
        self.object: Retest = self.get_object()
        form: Form = self.form_class(request.POST, instance=self.object)
        statement_backup_form: StatementBackupForm = StatementBackupForm(
            self.request.POST, self.request.FILES
        )
        if form.is_valid() and statement_backup_form.is_valid():
            form.save()
            retest: Retest = self.object
            uploaded_file: InMemoryUploadedFile | None = (
                statement_backup_form.cleaned_data.get("file_to_upload")
            )
            if uploaded_file is not None:
                self.case_file_upload(
                    uploaded_file=uploaded_file,
                    user=self.request.user,
                    base_case=retest.simplified_case,
                    file_type=CaseFile.Type.STATEMENT,
                )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    statement_backup_form=statement_backup_form,
                )
            )


class StatementAuditUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update equality body retest
    """

    model: type[StatementAudit] = StatementAudit
    context_object_name: str = "statement_audit"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of retest"""
        if form.changed_data:
            self.object: StatementAudit = form.save(commit=False)
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=self.object.simplified_case,
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class EqualityBodyRetestStatementCheckingView(StatementAuditUpdateView):
    """
    View to do statement checks as part of an equality body-requested retest
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = self.object

        if self.request.POST:
            retest_statement_check_results_formset: (
                EqualityBodyRetestStatementCheckResultRoundFormset
            ) = EqualityBodyRetestStatementCheckResultRoundFormset(self.request.POST)
        else:
            retest_statement_check_results_formset: (
                EqualityBodyRetestStatementCheckResultRoundFormset
            ) = EqualityBodyRetestStatementCheckResultRoundFormset(
                queryset=StatementCheckResultRound.objects.filter(
                    statement_audit=statement_audit, type=self.statement_check_type
                )
            )

        context["retest_statement_check_results_formset"] = (
            retest_statement_check_results_formset
        )

        context.update(
            build_equality_body_retest_context_data(statement_audit=statement_audit)
        )

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        statement_audit: StatementAudit = self.object
        retest_statement_check_results_formset: (
            EqualityBodyRetestStatementCheckResultRoundFormset
        ) = context["retest_statement_check_results_formset"]
        if retest_statement_check_results_formset.is_valid():
            for (
                retest_statement_check_results_form
            ) in retest_statement_check_results_formset.forms:
                retest_statement_check_result: StatementCheckResultRound = (
                    retest_statement_check_results_form.save(commit=False)
                )
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=retest_statement_check_result,
                    simplified_case=statement_audit.simplified_case,
                )
                retest_statement_check_result.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class RetestStatementOverviewFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement overview check results retest
    """

    form_class: type[EqualityBodyRetestStatementOverviewUpdateForm] = (
        EqualityBodyRetestStatementOverviewUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_overview.html"
    )
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_next_platform_page(self) -> PlatformPage:
        statement_audit: StatementAudit = self.object
        if statement_audit.all_overview_statement_checks_have_passed:
            return get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-website",
                instance=statement_audit,
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-equality-body-statement-results",
            instance=statement_audit,
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = self.object
        context["next_platform_pages"] = [
            get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-website",
                instance=statement_audit,
            ),
            get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-results",
                instance=statement_audit,
            ),
        ]
        return context


class RetestStatementWebsiteFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement information check results retest
    """

    form_class: type[RetestStatementWebsiteUpdateForm] = (
        RetestStatementWebsiteUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_website.html"
    )
    statement_check_type: str = StatementCheck.Type.WEBSITE


class RetestStatementComplianceFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement compliance check results retest
    """

    form_class: type[RetestStatementComplianceUpdateForm] = (
        RetestStatementComplianceUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_compliance.html"
    )
    statement_check_type: str = StatementCheck.Type.COMPLIANCE


class RetestStatementNonAccessibleFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement non-accessible check results retest
    """

    form_class: type[RetestStatementNonAccessibleUpdateForm] = (
        RetestStatementNonAccessibleUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_non_accessible.html"
    )
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE


class RetestStatementPreparationFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement preparation check results retest
    """

    form_class: type[RetestStatementPreparationUpdateForm] = (
        RetestStatementPreparationUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_preparation.html"
    )
    statement_check_type: str = StatementCheck.Type.PREPARATION


class RetestStatementFeedbackFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement feedback check results retest
    """

    form_class: type[RetestStatementFeedbackUpdateForm] = (
        RetestStatementFeedbackUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_feedback.html"
    )
    statement_check_type: str = StatementCheck.Type.FEEDBACK


class RetestStatementDisproportionateFormView(EqualityBodyRetestStatementCheckingView):
    """
    View to update statement disproportionate burden check results retest
    """

    form_class: type[RetestStatementDisproportionateUpdateForm] = (
        RetestStatementDisproportionateUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_disproportionate.html"
    )
    statement_check_type: str = StatementCheck.Type.DISPROPORTIONATE


class RetestStatementCustomFormView(StatementAuditUpdateView):
    """
    View to update statement custom check results retest
    """

    form_class: type[RetestStatementCustomUpdateForm] = RetestStatementCustomUpdateForm
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_custom.html"
    )
    statement_check_type: str = StatementCheck.Type.CUSTOM

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        statement_audit: StatementAudit = self.object
        if self.request.POST:
            retest_statement_check_results_formset = (
                RetestStatementCustomCheckResultFormset(self.request.POST)
            )
        else:
            retest_statement_check_results: QuerySet[StatementCheckResultRound] = (
                statement_audit.custom_statement_check_results
            )
            if "add_custom" in self.request.GET:
                retest_statement_check_results_formset = (
                    RetestStatementCustomCheckResultFormsetOneExtra(
                        queryset=retest_statement_check_results
                    )
                )
            else:
                retest_statement_check_results_formset = (
                    RetestStatementCustomCheckResultFormset(
                        queryset=retest_statement_check_results
                    )
                )
        context["retest_statement_check_results_formset"] = (
            retest_statement_check_results_formset
        )
        context.update(
            build_equality_body_retest_context_data(statement_audit=statement_audit)
        )
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        retest_statement_check_results_formset = context[
            "retest_statement_check_results_formset"
        ]
        retest: Retest = form.save(commit=False)
        if retest_statement_check_results_formset.is_valid():
            retest_statement_check_results: list[StatementCheckResultRound] = (
                retest_statement_check_results_formset.save(commit=False)
            )
            for retest_statement_check_result in retest_statement_check_results:
                if not retest_statement_check_result.id:
                    retest_statement_check_result.retest = retest
                    retest_statement_check_result.check_result_state = (
                        RetestStatementCheckResult.Result.NO
                    )
                    retest_statement_check_result.save()
                    record_simplified_model_create_event(
                        user=self.request.user,
                        model_object=retest_statement_check_result,
                        simplified_case=retest_statement_check_result.retest.simplified_case,
                    )
                else:
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=retest_statement_check_result,
                        simplified_case=retest_statement_check_result.retest.simplified_case,
                    )
                    retest_statement_check_result.save()
        else:
            return super().form_invalid(form)
        mark_object_as_deleted(
            request=self.request,
            delete_button_prefix="remove_custom_",
            object_to_delete_model=StatementCheckResultRound,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "add_custom" in self.request.POST:
            retest: Retest = self.object
            retest_pk: dict[str, int] = {"pk": retest.id}
            current_url: str = reverse(
                "audits:edit-equality-body-statement-custom", kwargs=retest_pk
            )
            return f"{current_url}?add_custom=true#custom-None"
        return super().get_success_url()


class RetestStatementResultsUpdateView(StatementAuditUpdateView):
    """
    View to show results of statement content checks
    """

    form_class: type[RetestStatementResultsUpdateForm] = (
        RetestStatementResultsUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_statement_results.html"


class RetestDisproportionateBurdenUpdateView(StatementAuditUpdateView):
    """
    View to update equality body-requested retest disproportionate burden fields
    """

    form_class: type[RetestDisproportionateBurdenUpdateForm] = (
        RetestDisproportionateBurdenUpdateForm
    )
    template_name: str = (
        "audits/forms/equality_body_retest_disproportionate_burden.html"
    )


class RetestStatementDecisionUpdateView(StatementAuditUpdateView):
    """
    View to update equality body-requested retest statement decsion
    """

    form_class: type[RetestStatementDecisionUpdateForm] = (
        RetestStatementDecisionUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_statement_decision.html"
