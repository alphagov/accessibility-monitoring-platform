"""
Common views
"""
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone as django_timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..audits.models import (
    Audit,
    CheckResult,
    CHECK_RESULT_ERROR,
    RETEST_CHECK_RESULT_FIXED,
)
from ..cases.models import (
    Case,
    RECOMMENDATION_NO_ACTION,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    CLOSED_CASE_STATUSES,
)

from .forms import (
    AMPContactAdminForm,
    AMPIssueReportForm,
    ActiveQAAuditorUpdateForm,
    FrequentlyUsedLinkFormset,
    FrequentlyUsedLinkOneExtraFormset,
)
from .metrics import (
    calculate_metric_progress,
    count_statement_issues,
    get_case_progress_metrics,
    get_report_progress_metrics,
    get_case_yearly_metrics,
    get_policy_yearly_metrics,
    get_report_yearly_metrics,
)
from .models import FrequentlyUsedLink, IssueReport, Platform, ChangeToPlatform
from .page_title_utils import get_page_title
from .utils import (
    get_id_from_button_name,
    get_platform_settings,
    record_model_update_event,
    record_model_create_event,
)


class ContactAdminView(FormView):
    """
    Send email to platform admin
    """

    form_class = AMPContactAdminForm
    template_name: str = "common/contact_admin.html"
    success_url: str = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        self.send_mail(form.cleaned_data)
        return super().form_valid(form)

    def send_mail(self, cleaned_data: Dict[str, str]) -> None:
        subject: str = cleaned_data.get("subject", "")
        message: str = cleaned_data.get("message", "")
        if subject or message:
            email: EmailMessage = EmailMessage(
                subject=subject,
                body=message,
                from_email=self.request.user.email,
                to=[settings.CONTACT_ADMIN_EMAIL],
            )
            email.send()


class IssueReportView(FormView):
    """
    Save user feedback
    """

    form_class: Type[AMPIssueReportForm] = AMPIssueReportForm
    template_name: str = "common/issue_report.html"
    success_url: str = reverse_lazy("dashboard:home")

    def get(self, request, *args, **kwargs):
        """Populate form"""
        page_url: str = self.request.GET.get("page_url", "")
        page_title: str = get_page_title(page_url)
        description: str = self.request.GET.get("description", "")
        self.form: AMPIssueReportForm = self.form_class(
            {
                "page_url": page_url,
                "page_title": page_title,
                "description": description,
            }
        )
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        issue_report: IssueReport = form.save(commit=False)
        issue_report.created_by = self.request.user
        issue_report.save()
        self.send_mail(issue_report)
        return redirect(issue_report.page_url)

    def send_mail(self, issue_report: IssueReport) -> None:
        email: EmailMessage = EmailMessage(
            subject=f"Platform issue on {issue_report.page_title}",
            body=f"""Reported by: {issue_report.created_by}

URL: https://{self.request.get_host()}{issue_report.page_url}

{issue_report.description}""",
            from_email=self.request.user.email,
            to=[settings.CONTACT_ADMIN_EMAIL],
        )
        email.send()


class ActiveQAAuditorUpdateView(UpdateView):
    """
    Update active QA auditor
    """

    model: Type[Platform] = Platform
    context_object_name: str = "platform"
    form_class: Type[ActiveQAAuditorUpdateForm] = ActiveQAAuditorUpdateForm
    template_name: str = "common/settings/active_qa_auditor.html"

    def get_object(self) -> Platform:
        """Return the platform-wide settings"""
        return Platform.objects.get(pk=1)

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class ChangeToPlatformListView(ListView):
    """
    View of list of platform changes
    """

    model: Type[ChangeToPlatform] = ChangeToPlatform
    template_name: str = "common/settings/platform_history.html"
    context_object_name: str = "changes_to_platform"
    paginate_by: int = 10


class PlatformTemplateView(TemplateView):
    """
    View of platform-level settings
    """

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add platform settings to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["platform"] = get_platform_settings()
        return context


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "common/accessibility_statement.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "common/privacy_notice.html"


class MarkdownCheatsheetTemplateView(PlatformTemplateView):
    template_name: str = "common/settings/markdown_cheatsheet.html"


class MoreInformationTemplateView(PlatformTemplateView):
    template_name: str = "common/settings/more_information.html"


class MetricsCaseTemplateView(TemplateView):
    """
    View of case metrics
    """

    template_name: str = "common/metrics/case.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add number of cases to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        extra_context: Dict[str, Any] = {
            "progress_metrics": get_case_progress_metrics(),
            "yearly_metrics": get_case_yearly_metrics(),
        }
        return {**extra_context, **context}


class MetricsPolicyTemplateView(TemplateView):
    """
    View of policy metrics
    """

    template_name: str = "common/metrics/policy.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add number of cases to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        total_metrics: List[Dict[str, int]] = [
            {
                "label": "Total reports sent",
                "total": Case.objects.exclude(report_sent_date=None).count(),
            },
            {
                "label": "Total cases closed",
                "total": Case.objects.filter(status__in=CLOSED_CASE_STATUSES).count(),
            },
            {
                "label": "Total number of accessibility issues found",
                "total": CheckResult.objects.filter(
                    check_result_state=CHECK_RESULT_ERROR
                ).count(),
            },
            {
                "label": "Total number of accessibility issues fixed",
                "total": CheckResult.objects.filter(
                    retest_state=RETEST_CHECK_RESULT_FIXED
                ).count(),
            },
        ]
        now: datetime = django_timezone.now()
        start_date: datetime = now - timedelta(days=90)
        retested_audits: QuerySet[Audit] = Audit.objects.filter(
            retest_date__gte=start_date
        )
        fixed_audits: QuerySet[Audit] = retested_audits.filter(
            case__recommendation_for_enforcement=RECOMMENDATION_NO_ACTION
        )
        fixed_audits_count: int = fixed_audits.count()
        closed_audits: QuerySet[Audit] = retested_audits.filter(
            Q(  # pylint: disable=unsupported-binary-operation
                case__status="case-closed-sent-to-equalities-body"
            )
            | Q(case__status="complete")
            | Q(case__status="case-closed-waiting-to-be-sent")
            | Q(case__status="in-correspondence-with-equalities-body")
        )
        closed_audits_count: int = closed_audits.count()
        compliant_audits: QuerySet[Audit] = retested_audits.filter(
            case__accessibility_statement_state_final=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT
        )
        compliant_audits_count: int = compliant_audits.count()
        check_results_of_last_90_days: QuerySet[
            CheckResult
        ] = CheckResult.objects.filter(audit__retest_date__gte=start_date)
        fixed_check_results_count: int = (
            check_results_of_last_90_days.filter(check_result_state="error")
            .filter(retest_state="fixed")
            .count()
        )
        total_check_results_count: int = (
            check_results_of_last_90_days.filter(check_result_state="error")
            .exclude(retest_state="not-retested")
            .count()
        )

        fixed_statement_issues_count, statement_issues_count = count_statement_issues(
            retested_audits
        )

        thirteen_month_start_date: datetime = datetime(
            now.year - 1, now.month, 1, tzinfo=timezone.utc
        )
        last_year_cases: QuerySet[Case] = Case.objects.filter(
            created__gte=thirteen_month_start_date
        )
        equality_body_cases_completed_count: int = last_year_cases.filter(
            enforcement_body_pursuing="yes-completed"
        ).count()
        equality_body_cases_in_progress_count: int = last_year_cases.filter(
            enforcement_body_pursuing="yes-in-progress"
        ).count()

        progress_metrics: List[Dict[str, Union[str, int]]] = [
            calculate_metric_progress(
                label="Websites compliant after retest in the last 90 days",
                partial_count=fixed_audits_count,
                total_count=closed_audits_count,
            ),
            calculate_metric_progress(
                label="Statements compliant after retest in the last 90 days",
                partial_count=compliant_audits_count,
                total_count=closed_audits_count,
            ),
            calculate_metric_progress(
                label="Website accessibility issues fixed in the last 90 days",
                partial_count=fixed_check_results_count,
                total_count=total_check_results_count,
            ),
            calculate_metric_progress(
                label="Statement issues fixed in the last 90 days",
                partial_count=fixed_statement_issues_count,
                total_count=statement_issues_count,
            ),
        ]

        extra_context: Dict[str, Any] = {
            "total_metrics": total_metrics,
            "progress_metrics": progress_metrics,
            "equality_body_cases_completed_count": equality_body_cases_completed_count,
            "equality_body_cases_in_progress_count": equality_body_cases_in_progress_count,
            "yearly_metrics": get_policy_yearly_metrics(),
        }
        return {**extra_context, **context}


class MetricsReportTemplateView(TemplateView):
    """
    View of report metrics
    """

    template_name: str = "common/metrics/report.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add number of cases to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        extra_context: Dict[str, Any] = {
            "progress_metrics": get_report_progress_metrics(),
            "yearly_metrics": get_report_yearly_metrics(),
        }

        return {**extra_context, **context}


class FrequentlyUsedLinkFormsetTemplateView(TemplateView):
    """
    Update list of frequently used links
    """

    template_name: str = "common/settings/edit_frequently_used_links.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            links_formset = FrequentlyUsedLinkFormset(self.request.POST)
        else:
            links: QuerySet[FrequentlyUsedLink] = FrequentlyUsedLink.objects.filter(
                is_deleted=False
            )
            if "add_link" in self.request.GET:
                links_formset = FrequentlyUsedLinkOneExtraFormset(queryset=links)
            else:
                links_formset = FrequentlyUsedLinkFormset(queryset=links)
        context["links_formset"] = links_formset
        return context

    def post(
        self, request: HttpRequest, *args: Tuple[str], **kwargs: Dict[str, Any]
    ) -> Union[HttpResponseRedirect, HttpResponse]:
        """Process contents of valid form"""
        context: Dict[str, Any] = self.get_context_data()
        links_formset = context["links_formset"]
        if links_formset.is_valid():
            links: List[FrequentlyUsedLink] = links_formset.save(commit=False)
            for link in links:
                if not link.id:
                    link.save()
                    record_model_create_event(user=self.request.user, model_object=link)
                else:
                    record_model_update_event(user=self.request.user, model_object=link)
                    link.save()
        else:
            return self.render_to_response(
                self.get_context_data(links_formset=links_formset)
            )
        link_id_to_delete: Optional[int] = get_id_from_button_name(
            button_name_prefix="remove_link_",
            querydict=request.POST,
        )
        if link_id_to_delete is not None:
            link_to_delete: FrequentlyUsedLink = FrequentlyUsedLink.objects.get(
                id=link_id_to_delete
            )
            link_to_delete.is_deleted = True
            record_model_update_event(
                user=self.request.user, model_object=link_to_delete
            )
            link_to_delete.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        url: str = reverse_lazy("common:edit-frequently-used-links")
        if "add_link" in self.request.POST:
            return f"{url}?add_link=true#link-None"
        return url
