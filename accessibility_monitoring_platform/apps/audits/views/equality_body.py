"""
Views for audits app (called tests by users)
"""

from typing import Any

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ...common.mark_deleted_util import mark_object_as_deleted
from ...common.models import Boolean
from ...common.sitemap import PlatformPage, get_platform_page_by_url_name
from ...common.utils import list_to_dictionary_of_lists
from ...common.views import NextPlatformPageMixin
from ...simplified.models import SimplifiedCase
from ...simplified.utils import record_model_create_event, record_model_update_event
from ..forms import (
    RetestCheckResultFormset,
    RetestComparisonUpdateForm,
    RetestComplianceUpdateForm,
    RetestDisproportionateBurdenUpdateForm,
    RetestPageChecksForm,
    RetestStatementCheckResultFormset,
    RetestStatementComplianceUpdateForm,
    RetestStatementCustomCheckResultFormset,
    RetestStatementCustomCheckResultFormsetOneExtra,
    RetestStatementCustomUpdateForm,
    RetestStatementDecisionUpdateForm,
    RetestStatementFeedbackUpdateForm,
    RetestStatementNonAccessibleUpdateForm,
    RetestStatementOverviewUpdateForm,
    RetestStatementPagesUpdateForm,
    RetestStatementPreparationUpdateForm,
    RetestStatementResultsUpdateForm,
    RetestStatementWebsiteUpdateForm,
    RetestUpdateForm,
    StatementPageFormset,
    StatementPageFormsetOneExtra,
)
from ..models import (
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementPage,
)
from ..utils import create_checkresults_for_retest, get_next_platform_page_equality_body


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
    id_within_case: int = simplified_case.retests.count()
    if id_within_case == 0:
        id_within_case = 1
    retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=id_within_case
    )
    record_model_create_event(
        user=request.user, model_object=retest, case=simplified_case
    )
    create_checkresults_for_retest(retest=retest)
    return redirect(reverse("audits:retest-metadata-update", kwargs={"pk": retest.id}))


def mark_retest_as_deleted(request: HttpRequest, pk: int) -> HttpResponse:
    """Set Retest.is_deleted to True"""
    retest: Retest = get_object_or_404(Retest, id=pk)
    retest.is_deleted = True
    record_model_update_event(user=request.user, model_object=retest, case=retest.case)
    retest.save()
    return redirect(
        reverse(
            "simplified:edit-retest-overview", kwargs={"pk": retest.simplified_case.id}
        )
    )


class RetestMetadataUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update a equality body retest metadata
    """

    model: type[Retest] = Retest
    form_class: type[RetestUpdateForm] = RetestUpdateForm
    template_name: str = "audits/forms/equality_body_retest_metadata_update.html"
    context_object_name: str = "retest"

    def get_next_platform_page(self) -> PlatformPage:
        return get_next_platform_page_equality_body(retest=self.object)

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(
                user=self.request.user,
                model_object=self.object,
                case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestPageChecksFormView(NextPlatformPageMixin, UpdateView):
    """
    View to update check results for a page in a retest requested by an equality body
    """

    model: type[RetestPage] = RetestPage
    form_class: type[RetestPageChecksForm] = RetestPageChecksForm
    template_name: str = "audits/forms/equality_body_retest_page_checks.html"
    context_object_name: str = "retest_page"

    def get_next_platform_page(self) -> PlatformPage:
        retest_page: RetestPage = self.object
        return get_next_platform_page_equality_body(
            retest=retest_page.retest, current_page=retest_page
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.POST:
            retest_check_results_formset: RetestCheckResultFormset = (
                RetestCheckResultFormset(self.request.POST)
            )
        else:
            retest_check_results_formset: RetestCheckResultFormset = (
                RetestCheckResultFormset(
                    queryset=self.object.retestcheckresult_set.all()
                )
            )

        context["retest_check_results_formset"] = retest_check_results_formset

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        if "missing_date" in form.changed_data:
            retest_page: RetestPage = self.object
            if form.cleaned_data["missing_date"]:
                retest_page.page.not_found = Boolean.YES
            else:
                retest_page.page.not_found = Boolean.NO
            retest_page.page.save()

        retest_check_results_formset: RetestCheckResultFormset = context[
            "retest_check_results_formset"
        ]
        if retest_check_results_formset.is_valid():
            retest_check_results_formset.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class RetestComparisonUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update a equality body retest comparison
    """

    model: type[Retest] = Retest
    form_class: type[RetestComparisonUpdateForm] = RetestComparisonUpdateForm
    template_name: str = "audits/forms/equality_body_retest_comparison_update.html"
    context_object_name: str = "retest"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        retest: Retest = self.object

        hide_fixed = "hide-fixed" in self.request.GET
        context["hide_fixed"] = hide_fixed

        retest_check_results: QuerySet[RetestCheckResult] = (
            retest.unfixed_check_results if hide_fixed else retest.check_results
        )

        view_url_param: str | None = self.request.GET.get("view")
        show_failures_by_wcag: bool = view_url_param == "WCAG view"
        context["show_failures_by_wcag"] = show_failures_by_wcag

        if show_failures_by_wcag:
            context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                items=retest_check_results, group_by_attr="wcag_definition"
            )

        context["missing_pages"] = RetestPage.objects.filter(retest=retest).exclude(
            missing_date=None
        )

        return context

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(
                user=self.request.user,
                model_object=self.object,
                case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestComplianceUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update a equality body retest compliance
    """

    model: type[Retest] = Retest
    form_class: type[RetestComplianceUpdateForm] = RetestComplianceUpdateForm
    template_name: str = "audits/forms/equality_body_retest_compliance_update.html"
    context_object_name: str = "retest"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(
                user=self.request.user,
                model_object=self.object,
                case=self.object.simplified_case,
            )
        return super().form_valid(form)


class RetestStatementPageFormsetUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update statement pages in equality body-requested retest
    """

    model: type[Retest] = Retest
    form_class: type[RetestStatementPagesUpdateForm] = RetestStatementPagesUpdateForm
    template_name: str = (
        "audits/forms/equality_body_retest_statement_pages_formset.html"
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            statement_pages_formset = StatementPageFormset(self.request.POST)
        else:
            statement_pages: QuerySet[StatementPage] = (
                self.object.simplified_case.audit.statement_pages
            )
            if "add_extra" in self.request.GET:
                statement_pages_formset = StatementPageFormsetOneExtra(
                    queryset=statement_pages
                )
            else:
                statement_pages_formset = StatementPageFormset(queryset=statement_pages)
        for form in statement_pages_formset:
            if form.instance.id is None:
                form.fields["added_stage"].initial = StatementPage.AddedStage.RETEST
        context["statement_pages_formset"] = statement_pages_formset
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        statement_pages_formset = context["statement_pages_formset"]
        retest: Retest = form.save(commit=False)
        if statement_pages_formset.is_valid():
            statement_pages: list[StatementPage] = statement_pages_formset.save(
                commit=False
            )
            for statement_page in statement_pages:
                if not statement_page.audit_id:
                    statement_page.audit = retest.simplified_case.audit
                    statement_page.save()
                    record_model_create_event(
                        user=self.request.user,
                        model_object=statement_page,
                        case=retest.case,
                    )
                else:
                    record_model_update_event(
                        user=self.request.user,
                        model_object=statement_page,
                        case=retest.case,
                    )
                    statement_page.save()
        else:
            return super().form_invalid(form)
        mark_object_as_deleted(
            request=self.request,
            delete_button_prefix="remove_statement_page_",
            object_to_delete_model=StatementPage,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "add_statement_page" in self.request.POST:
            retest: Retest = self.object
            retest_pk: dict[str, int] = {"pk": retest.id}
            current_url: str = reverse(
                "audits:edit-equality-body-statement-pages", kwargs=retest_pk
            )
            return f"{current_url}?add_extra=true#statement-page-None"
        return super().get_success_url()


class RetestUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update equality body retest
    """

    model: type[Retest] = Retest
    context_object_name: str = "retest"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of retest"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(
                user=self.request.user,
                model_object=self.object,
                case=self.object.simplified_case,
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class RetestStatementCheckingView(RetestUpdateView):
    """
    View to do statement checks as part of an equality body-requested retest
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        retest: Retest = self.object

        if self.request.POST:
            retest_statement_check_results_formset: (
                RetestStatementCheckResultFormset
            ) = RetestStatementCheckResultFormset(self.request.POST)
        else:
            retest_statement_check_results_formset: (
                RetestStatementCheckResultFormset
            ) = RetestStatementCheckResultFormset(
                queryset=RetestStatementCheckResult.objects.filter(
                    retest=retest, type=self.statement_check_type
                )
            )

        context["retest_statement_check_results_formset"] = (
            retest_statement_check_results_formset
        )

        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        retest_statement_check_results_formset: RetestStatementCheckResultFormset = (
            context["retest_statement_check_results_formset"]
        )
        if retest_statement_check_results_formset.is_valid():
            for (
                retest_statement_check_results_form
            ) in retest_statement_check_results_formset.forms:
                retest_statement_check_result: RetestStatementCheckResult = (
                    retest_statement_check_results_form.save(commit=False)
                )
                record_model_update_event(
                    user=self.request.user,
                    model_object=retest_statement_check_result,
                    case=retest_statement_check_result.retest.case,
                )
                retest_statement_check_result.save()
        else:
            return super().form_invalid(form)

        return super().form_valid(form)


class RetestStatementOverviewFormView(RetestStatementCheckingView):
    """
    View to update statement overview check results retest
    """

    form_class: type[RetestStatementOverviewUpdateForm] = (
        RetestStatementOverviewUpdateForm
    )
    template_name: str = (
        "audits/statement_checks/equality_body_retest_statement_overview.html"
    )
    statement_check_type: str = StatementCheck.Type.OVERVIEW

    def get_next_platform_page(self) -> PlatformPage:
        retest: Retest = self.object
        if retest.all_overview_statement_checks_have_passed:
            return get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-website", instance=retest
            )
        return get_platform_page_by_url_name(
            url_name="audits:edit-equality-body-statement-results", instance=retest
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Populate context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        retest: Retest = self.object
        context["next_platform_pages"] = [
            get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-website", instance=retest
            ),
            get_platform_page_by_url_name(
                url_name="audits:edit-equality-body-statement-results", instance=retest
            ),
        ]
        return context


class RetestStatementWebsiteFormView(RetestStatementCheckingView):
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


class RetestStatementComplianceFormView(RetestStatementCheckingView):
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


class RetestStatementNonAccessibleFormView(RetestStatementCheckingView):
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


class RetestStatementPreparationFormView(RetestStatementCheckingView):
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


class RetestStatementFeedbackFormView(RetestStatementCheckingView):
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


class RetestStatementCustomFormView(RetestUpdateView):
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
        retest: Retest = self.object
        if self.request.POST:
            retest_statement_check_results_formset = (
                RetestStatementCustomCheckResultFormset(self.request.POST)
            )
        else:
            retest_statement_check_results: QuerySet[RetestStatementCheckResult] = (
                retest.custom_statement_check_results
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
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        retest_statement_check_results_formset = context[
            "retest_statement_check_results_formset"
        ]
        retest: Retest = form.save(commit=False)
        if retest_statement_check_results_formset.is_valid():
            retest_statement_check_results: list[RetestStatementCheckResult] = (
                retest_statement_check_results_formset.save(commit=False)
            )
            for retest_statement_check_result in retest_statement_check_results:
                if not retest_statement_check_result.id:
                    retest_statement_check_result.retest = retest
                    retest_statement_check_result.check_result_state = (
                        RetestStatementCheckResult.Result.NO
                    )
                    retest_statement_check_result.save()
                    record_model_create_event(
                        user=self.request.user,
                        model_object=retest_statement_check_result,
                        case=retest_statement_check_result.retest.case,
                    )
                else:
                    record_model_update_event(
                        user=self.request.user,
                        model_object=retest_statement_check_result,
                        case=retest_statement_check_result.retest.case,
                    )
                    retest_statement_check_result.save()
        else:
            return super().form_invalid(form)
        mark_object_as_deleted(
            request=self.request,
            delete_button_prefix="remove_custom_",
            object_to_delete_model=RetestStatementCheckResult,
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


class RetestStatementResultsUpdateView(RetestUpdateView):
    """
    View to show results of statement content checks
    """

    form_class: type[RetestStatementResultsUpdateForm] = (
        RetestStatementResultsUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_statement_results.html"


class RetestDisproportionateBurdenUpdateView(RetestUpdateView):
    """
    View to update equality body-requested retest disproportionate burden fields
    """

    form_class: type[RetestDisproportionateBurdenUpdateForm] = (
        RetestDisproportionateBurdenUpdateForm
    )
    template_name: str = (
        "audits/forms/equality_body_retest_disproportionate_burden.html"
    )


class RetestStatementDecisionUpdateView(RetestUpdateView):
    """
    View to update equality body-requested retest statement decsion
    """

    form_class: type[RetestStatementDecisionUpdateForm] = (
        RetestStatementDecisionUpdateForm
    )
    template_name: str = "audits/forms/equality_body_retest_statement_decision.html"
