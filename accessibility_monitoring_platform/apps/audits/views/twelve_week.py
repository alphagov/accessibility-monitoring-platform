"""
Views for audits app (called tests by users)
"""

from datetime import date
from typing import Any

from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ...cases.models import CaseEvent
from ...common.utils import record_model_update_event
from ..forms import (
    ArchiveAuditRetestStatement1UpdateForm,
    ArchiveAuditRetestStatement2UpdateForm,
    AuditRetestCheckResultFilterForm,
    AuditRetestCheckResultForm,
    AuditRetestCheckResultFormset,
    AuditRetestMetadataUpdateForm,
    AuditRetestPageChecksForm,
    AuditRetestPagesUpdateForm,
    AuditRetestStatementCheckResultFormset,
    AuditRetestStatementComplianceUpdateForm,
    AuditRetestStatementCustomUpdateForm,
    AuditRetestStatementDecisionUpdateForm,
    AuditRetestStatementFeedbackUpdateForm,
    AuditRetestStatementNonAccessibleUpdateForm,
    AuditRetestStatementOverviewUpdateForm,
    AuditRetestStatementPreparationUpdateForm,
    AuditRetestStatementSummaryUpdateForm,
    AuditRetestStatementWebsiteUpdateForm,
    AuditRetestWcagSummaryUpdateForm,
    AuditRetestWebsiteDecisionUpdateForm,
    CaseComplianceStatement12WeekUpdateForm,
    CaseComplianceWebsite12WeekUpdateForm,
    TwelveWeekDisproportionateBurdenUpdateForm,
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
    get_audit_summary_context,
    get_next_retest_page_url,
    get_other_pages_with_retest_notes,
)
from .base import (
    AuditCaseComplianceUpdateView,
    AuditUpdateView,
    StatementPageFormsetUpdateView,
)
from .initial import AuditPageChecksFormView


class AuditRetestMetadataUpdateView(AuditUpdateView):
    """
    View to update audit retest metadata
    """

    form_class: type[AuditRetestMetadataUpdateForm] = AuditRetestMetadataUpdateForm
    template_name: str = "audits/forms/twelve_week_retest_metadata.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            if not audit.case.psb_response:
                return reverse(
                    "audits:edit-audit-retest-statement-pages", kwargs=audit_pk
                )
            return reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestPagesView(AuditUpdateView):
    """View to retest pages"""

    form_class: type[AuditRetestPagesUpdateForm] = AuditRetestPagesUpdateForm
    template_name: str = "audits/forms/twelve_week_pages.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            url: str = get_next_retest_page_url(audit=self.object)
            return url
        return super().get_success_url()


class AuditRetestPageChecksFormView(AuditPageChecksFormView):
    """
    View to retest check results for a page
    """

    form_class: type[AuditRetestPageChecksForm] = AuditRetestPageChecksForm
    template_name: str = "audits/forms/twelve_week_retest_page_checks.html"
    page: Page

    def get_form(self):
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
                AuditRetestCheckResultFormset(self.request.POST)
            )
        else:
            check_results_formset: AuditRetestCheckResultFormset = (
                AuditRetestCheckResultFormset(
                    initial=[
                        check_result.dict_for_retest
                        for check_result in self.page.failed_check_results
                    ]
                )
            )
        check_results_and_forms: list[
            tuple[CheckResult, AuditRetestCheckResultForm]
        ] = list(zip(self.page.failed_check_results, check_results_formset.forms))

        context["check_results_formset"] = check_results_formset
        context["check_results_and_forms"] = check_results_and_forms
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
            record_model_update_event(user=self.request.user, model_object=page)
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
                    record_model_update_event(
                        user=self.request.user, model_object=check_result
                    )
                    check_result.save()
        else:
            return super().form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return get_next_retest_page_url(
                audit=self.page.audit, current_page=self.page
            )
        return super().get_success_url()


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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-audit-retest-wcag-summary", kwargs=audit_pk)
        return super().get_success_url()


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
    template_name: str = "audits/forms/test_summary.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            return reverse(
                "audits:edit-audit-retest-statement-pages", kwargs={"pk": audit.id}
            )
        return super().get_success_url()


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
        audit: Audit = self.object
        audit_pk: dict[str, int] = {"pk": audit.id}
        current_url: str = reverse(
            "audits:edit-audit-retest-statement-pages", kwargs=audit_pk
        )
        if "save_continue" in self.request.POST:
            if audit.uses_statement_checks:
                return reverse("audits:edit-retest-statement-overview", kwargs=audit_pk)
            return reverse("audits:edit-audit-retest-statement-1", kwargs=audit_pk)
        elif "add_statement_page" in self.request.POST:
            return f"{current_url}?add_extra=true#statement-page-None"
        else:
            return current_url


class AuditRetestStatement1UpdateView(AuditUpdateView):
    """
    View to retest accessibility statement part one
    """

    form_class: type[ArchiveAuditRetestStatement1UpdateForm] = (
        ArchiveAuditRetestStatement1UpdateForm
    )
    template_name: str = "audits/forms/retest_statement_1.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: dict[str, int] = {"pk": self.object.id}
            return reverse("audits:edit-audit-retest-statement-2", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatement2UpdateView(AuditUpdateView):
    """
    View to retest accessibility statement part two
    """

    form_class: type[ArchiveAuditRetestStatement2UpdateForm] = (
        ArchiveAuditRetestStatement2UpdateForm
    )
    template_name: str = "audits/forms/retest_statement_2.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: dict[str, int] = {"pk": self.object.id}
            return reverse(
                "audits:edit-twelve-week-disproportionate-burden", kwargs=audit_pk
            )
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
                    record_model_update_event(
                        user=self.request.user, model_object=statement_check_result
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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            if audit.all_overview_statement_checks_have_passed:
                return reverse("audits:edit-retest-statement-website", kwargs=audit_pk)
            return reverse(
                "audits:edit-twelve-week-disproportionate-burden", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementWebsiteFormView(AuditRetestStatementCheckingView):
    """
    View to update statement information check results retest
    """

    form_class: type[AuditRetestStatementWebsiteUpdateForm] = (
        AuditRetestStatementWebsiteUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.WEBSITE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-retest-statement-compliance", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatementComplianceFormView(AuditRetestStatementCheckingView):
    """
    View to update statement compliance check results retest
    """

    form_class: type[AuditRetestStatementComplianceUpdateForm] = (
        AuditRetestStatementComplianceUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.COMPLIANCE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse(
                "audits:edit-retest-statement-non-accessible", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementNonAccessibleFormView(AuditRetestStatementCheckingView):
    """
    View to update statement non-accessible check results retest
    """

    form_class: type[AuditRetestStatementNonAccessibleUpdateForm] = (
        AuditRetestStatementNonAccessibleUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.NON_ACCESSIBLE

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-retest-statement-preparation", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatementPreparationFormView(AuditRetestStatementCheckingView):
    """
    View to update statement preparation check results retest
    """

    form_class: type[AuditRetestStatementPreparationUpdateForm] = (
        AuditRetestStatementPreparationUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.PREPARATION

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-retest-statement-feedback", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatementFeedbackFormView(AuditRetestStatementCheckingView):
    """
    View to update statement feedback check results retest
    """

    form_class: type[AuditRetestStatementFeedbackUpdateForm] = (
        AuditRetestStatementFeedbackUpdateForm
    )
    statement_check_type: str = StatementCheck.Type.FEEDBACK

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse("audits:edit-retest-statement-custom", kwargs=audit_pk)
        return super().get_success_url()


class AuditRetestStatementCustomFormView(AuditRetestStatementCheckingView):
    """
    View to update statement custom check results retest
    """

    form_class: type[AuditRetestStatementCustomUpdateForm] = (
        AuditRetestStatementCustomUpdateForm
    )
    template_name: str = "audits/statement_checks/retest_statement_other.html"
    statement_check_type: str = StatementCheck.Type.CUSTOM

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse(
                "audits:edit-twelve-week-disproportionate-burden", kwargs=audit_pk
            )
        return super().get_success_url()


class TwelveWeekDisproportionateBurdenUpdateView(AuditUpdateView):
    """
    View to update 12-week disproportionate burden fields
    """

    form_class: type[TwelveWeekDisproportionateBurdenUpdateForm] = (
        TwelveWeekDisproportionateBurdenUpdateForm
    )
    template_name: str = "audits/forms/twelve_week_disproportionate_burden.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            audit_pk: dict[str, int] = {"pk": audit.id}
            return reverse(
                "audits:edit-audit-retest-statement-decision", kwargs=audit_pk
            )
        return super().get_success_url()


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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit_pk: dict[str, int] = {"pk": self.object.id}
            return reverse(
                "audits:edit-audit-retest-statement-summary", kwargs=audit_pk
            )
        return super().get_success_url()


class AuditRetestStatementSummaryUpdateView(AuditRetestSummaryUpdateView):
    """
    View to update audit summary for 12-week WCAG test
    """

    form_class: type[AuditRetestStatementSummaryUpdateForm] = (
        AuditRetestStatementSummaryUpdateForm
    )
    template_name: str = "audits/forms/test_summary.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            audit: Audit = self.object
            return reverse("cases:edit-review-changes", kwargs={"pk": audit.case.id})
        return super().get_success_url()


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
    record_model_update_event(user=request.user, model_object=audit)
    audit.save()
    CaseEvent.objects.create(
        case=audit.case,
        done_by=request.user,
        event_type=CaseEvent.EventType.START_RETEST,
        message="Started retest",
    )
    return redirect(reverse("audits:edit-audit-retest-metadata", kwargs={"pk": pk}))
