"""
Common views
"""
from typing import Any, Dict, List, Type, Union
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..audits.models import Audit, CheckResult
from ..cases.models import (
    Case,
    RECOMMENDATION_NO_ACTION,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
)

from .forms import AMPContactAdminForm, AMPIssueReportForm, ActiveQAAuditorUpdateForm
from .metrics import (
    calculate_current_month_progress,
    build_yearly_metric_chart,
    build_13_month_x_axis_labels,
    calculate_metric_progress,
    count_statement_issues,
)
from .models import IssueReport, Platform, ChangeToPlatform
from .page_title_utils import get_page_title
from .utils import get_platform_settings


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
                from_email=self.request.user.email,  # type: ignore
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
        issue_report.created_by = self.request.user  # type: ignore
        issue_report.save()
        self.send_mail(issue_report)
        return redirect(issue_report.page_url)

    def send_mail(self, issue_report: IssueReport) -> None:
        email: EmailMessage = EmailMessage(
            subject=f"Platform issue on {issue_report.page_title}",
            body=f"""Reported by: {issue_report.created_by}

URL: https://{self.request.get_host()}{issue_report.page_url}

{issue_report.description}""",
            from_email=self.request.user.email,  # type: ignore
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


class MetricsCaseTemplateView(TemplateView):
    """
    View of case metrics
    """

    template_name: str = "common/metrics/case.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add number of cases to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        now: datetime = timezone.now()
        first_of_this_month: datetime = datetime(
            now.year, now.month, 1, tzinfo=timezone.utc
        )
        first_of_last_month: datetime = (
            datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
            if now.month > 1
            else datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        )

        monthly_metrics: List[Dict[str, Union[str, int]]] = [
            calculate_current_month_progress(
                label="Cases created",
                number_done_this_month=Case.objects.filter(
                    created__gte=first_of_this_month
                ).count(),
                number_done_last_month=Case.objects.filter(
                    created__gte=first_of_last_month
                )
                .filter(created__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                label="Tests completed",
                number_done_this_month=Case.objects.filter(
                    testing_details_complete_date__gte=first_of_this_month
                ).count(),
                number_done_last_month=Case.objects.filter(
                    testing_details_complete_date__gte=first_of_last_month
                )
                .filter(testing_details_complete_date__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                label="Reports sent",
                number_done_this_month=Case.objects.filter(
                    report_sent_date__gte=first_of_this_month
                ).count(),
                number_done_last_month=Case.objects.filter(
                    report_sent_date__gte=first_of_last_month
                )
                .filter(report_sent_date__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                label="Cases closed",
                number_done_this_month=Case.objects.filter(
                    completed_date__gte=first_of_this_month
                ).count(),
                number_done_last_month=Case.objects.filter(
                    completed_date__gte=first_of_last_month
                )
                .filter(completed_date__lt=first_of_this_month)
                .count(),
            ),
        ]

        yearly_metrics: List[
            Dict[
                str,
                Union[
                    str,
                    int,
                    List[Dict[str, Union[datetime, int]]],
                    List[Dict[str, Union[str, int]]],
                ],
            ]
        ] = []
        start_date: datetime = datetime(now.year - 1, now.month, 1)
        x_axis_labels = build_13_month_x_axis_labels()
        for label, date_column in [
            ("Cases created over the last year", "created"),
            ("Tests completed over the last year", "testing_details_complete_date"),
            ("Reports sent over the last year", "report_sent_date"),
            ("Cases completed over the last year", "completed_date"),
        ]:
            cases: QuerySet[Case] = Case.objects.filter(
                **{f"{date_column}__gte": start_date}
            )
            month_dates: QuerySet = cases.dates(  # type: ignore
                date_column, kind="month"
            )
            all_table_rows: List[Dict[str, Union[datetime, int]]] = [
                {
                    "month_date": month_date,
                    "count": cases.filter(
                        **{
                            f"{date_column}__year": month_date.year,
                            f"{date_column}__month": month_date.month,
                        }
                    ).count(),
                }
                for month_date in month_dates
            ]
            if all_table_rows:
                yearly_metrics.append(
                    build_yearly_metric_chart(
                        label=label, all_table_rows=all_table_rows
                    )
                )

        extra_context: Dict[str, Any] = {
            "first_of_last_month": first_of_last_month,
            "x_axis_labels": x_axis_labels,
            "monthly_metrics": monthly_metrics,
            "yearly_metrics": yearly_metrics,
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
        now: datetime = timezone.now()
        start_date: datetime = now - timedelta(days=90)
        retested_audits: QuerySet[Audit] = Audit.objects.filter(
            retest_date__gte=start_date
        )
        fixed_audits: QuerySet[Audit] = retested_audits.filter(
            case__recommendation_for_enforcement=RECOMMENDATION_NO_ACTION
        )
        fixed_audits_count: int = fixed_audits.count()
        closed_audits: QuerySet[Audit] = retested_audits.filter(
            Q(case__status="case-closed-sent-to-equalities-body")  # pylint: disable=unsupported-binary-operation
            | Q(case__status="complete")
            | Q(case__status="case-closed-waiting-to-be-sent")
            | Q(case__status="in-correspondence-with-equalities-body")
        )
        closed_audits_count: int = closed_audits.count()
        compliant_audits: QuerySet[Audit] = retested_audits.filter(
            case__accessibility_statement_state_final=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT
        )
        compliant_audits_count: int = compliant_audits.count()
        check_results_of_last_90_days: QuerySet[CheckResult] = CheckResult.objects.filter(
            audit__retest_date__gte=start_date
        )
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

        fixed_statement_issues_count, statement_issues_count = count_statement_issues(retested_audits)

        context["annual_metrics"] = [
            calculate_metric_progress(
                label="Websites compliant after audit in the last 90 days",
                partial_count=fixed_audits_count,
                total_count=closed_audits_count,
            ),
            calculate_metric_progress(
                label="Statements compliant after audit in the last 90 days",
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
            calculate_metric_progress(
                label="Cases completed with equalities bodies in 2022",
                partial_count=5,
                total_count=10,
            ),
        ]

        monthly_metrics: List[
            Dict[
                str,
                Union[
                    str,
                    int,
                    List[Dict[str, Union[datetime, int]]],
                    List[Dict[str, Union[str, int]]],
                ],
            ]
        ] = []
        month_dates: QuerySet = closed_audits.dates(  # type: ignore
            "retest_date", kind="month"
        )
        all_table_rows: List[Dict[str, Union[datetime, int]]] = [
            {
                "month_date": month_date,
                "partial_count": fixed_audits.filter(
                    **{"retest_date__month": month_date.month, "retest_date__year": month_date.year}
                ).count(),
                "total_count": closed_audits.filter(
                    **{"retest_date__month": month_date.month, "retest_date__year": month_date.year}
                ).count(),
            }
            for month_date in month_dates
        ]
        if all_table_rows:
            monthly_metrics.append(
                {
                    "label": "State of websites after audit in 2022",
                    "all_table_rows": all_table_rows,
                }
            )
        month_dates: QuerySet = closed_audits.dates(  # type: ignore
            "retest_date", kind="month"
        )
        all_table_rows: List[Dict[str, Union[datetime, int]]] = [
            {
                "month_date": month_date,
                "partial_count": compliant_audits.filter(
                    **{"retest_date__month": month_date.month, "retest_date__year": month_date.year}
                ).count(),
                "total_count": closed_audits.filter(
                    **{"retest_date__month": month_date.month, "retest_date__year": month_date.year}
                ).count(),
            }
            for month_date in month_dates
        ]
        if all_table_rows:
            monthly_metrics.append(
                {
                    "label": "State of accessibility statements after audit in 2022",
                    "all_table_rows": all_table_rows,
                }
            )

        context["monthly_metrics"] = monthly_metrics
        return context
