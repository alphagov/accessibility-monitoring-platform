"""
Views for audits app (called tests by users)
"""
from typing import Any, Dict, Type, Union

from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ...cases.models import Case
from ...common.models import Boolean
from ...common.utils import (
    list_to_dictionary_of_lists,
    record_model_create_event,
    record_model_update_event,
)
from ..forms import (
    RetestCheckResultFormset,
    RetestComparisonUpdateForm,
    RetestComplianceUpdateForm,
    RetestPageChecksForm,
    RetestUpdateForm,
)
from ..models import Retest, RetestCheckResult, RetestPage
from ..utils import (
    create_checkresults_for_retest,
    get_next_equality_body_retest_page_url,
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
    case: Case = get_object_or_404(Case, id=case_id)
    id_within_case: int = case.retests.count()
    if id_within_case == 0:
        id_within_case = 1
    retest: Retest = Retest.objects.create(case=case, id_within_case=id_within_case)
    record_model_create_event(user=request.user, model_object=retest)
    create_checkresults_for_retest(retest=retest)
    return redirect(reverse("audits:retest-metadata-update", kwargs={"pk": retest.id}))


class RetestMetadataUpdateView(UpdateView):
    """
    View to update a equality body retest metadata
    """

    model: Type[Retest] = Retest
    form_class: Type[RetestUpdateForm] = RetestUpdateForm
    template_name: str = "audits/forms/equality_body_retest_metadata_update.html"
    context_object_name: str = "retest"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return get_next_equality_body_retest_page_url(retest=self.object)
        return reverse("audits:retest-metadata-update", kwargs={"pk": self.object.id})


class RetestPageChecksFormView(UpdateView):
    """
    View to update check results for a page in a retest requested by an equality body
    """

    model: Type[RetestPage] = RetestPage
    form_class: Type[RetestPageChecksForm] = RetestPageChecksForm
    template_name: str = "audits/forms/equality_body_retest_page_checks.html"
    context_object_name: str = "retest_page"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

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
        context: Dict[str, Any] = self.get_context_data()
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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            retest_page: RetestPage = self.object
            return get_next_equality_body_retest_page_url(
                retest=retest_page.retest, current_page=retest_page
            )
        return self.request.path


class RetestComparisonUpdateView(UpdateView):
    """
    View to update a equality body retest comparison
    """

    model: Type[Retest] = Retest
    form_class: Type[RetestComparisonUpdateForm] = RetestComparisonUpdateForm
    template_name: str = "audits/forms/equality_body_retest_comparison_update.html"
    context_object_name: str = "retest"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Populate context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        retest: Retest = self.object

        hide_fixed = "hide-fixed" in self.request.GET
        context["hide_fixed"] = hide_fixed

        retest_check_results: QuerySet[RetestCheckResult] = (
            retest.unfixed_check_results if hide_fixed else retest.check_results
        )

        view_url_param: Union[str, None] = self.request.GET.get("view")
        show_failures_by_wcag: bool = view_url_param == "WCAG view"
        context["show_failures_by_wcag"] = show_failures_by_wcag

        if show_failures_by_wcag:
            context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                items=retest_check_results, group_by_attr="wcag_definition"
            )
        else:
            context["audit_failures_by_page"] = list_to_dictionary_of_lists(
                items=retest_check_results, group_by_attr="retest_page"
            )

        context["missing_pages"] = RetestPage.objects.filter(retest=retest).exclude(
            missing_date=None
        )

        return context

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return reverse(
                "audits:retest-compliance-update", kwargs={"pk": self.object.id}
            )
        return reverse("audits:retest-comparison-update", kwargs={"pk": self.object.id})


class RetestComplianceUpdateView(UpdateView):
    """
    View to update a equality body retest compliance
    """

    model: Type[Retest] = Retest
    form_class: Type[RetestComplianceUpdateForm] = RetestComplianceUpdateForm
    template_name: str = "audits/forms/equality_body_retest_compliance_update.html"
    context_object_name: str = "retest"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add record event on change"""
        if form.changed_data:
            self.object: Retest = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-retest-overview", kwargs={"pk": self.object.case.id}
            )
        return reverse("audits:retest-compliance-update", kwargs={"pk": self.object.id})
