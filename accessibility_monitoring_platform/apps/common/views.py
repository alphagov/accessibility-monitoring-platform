"""
Common views
"""
from typing import Any, Dict, List, Type, Union
from datetime import date, datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.forms.models import ModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import Case

from .utils import (
    get_platform_settings,
    calculate_current_month_progress,
    build_yearly_metric_chart,
)
from .forms import AMPContactAdminForm, AMPIssueReportForm, ActiveQAAuditorUpdateForm
from .models import IssueReport, Platform, ChangeToPlatform
from .page_title_utils import get_page_title


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
        first_of_this_month: date = date(now.year, now.month, 1)
        first_of_last_month: date = (
            date(now.year, now.month - 1, 1)
            if now.month > 1
            else date(now.year - 1, 12, 1)
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
            Dict[str, Union[str, int, List[Dict[str, Union[datetime, int]]]]]
        ] = []
        start_date: str = f"{now.year - 1}-{now.month}-01"
        with connection.cursor() as cursor:
            for label, date_column in [
                ("Cases created over the last year", "created"),
                ("Tests completed over the last year", "testing_details_complete_date"),
                ("Reports sent over the last year", "report_sent_date"),
                ("Cases completed over the last year", "completed_date"),
            ]:
                cursor.execute(
                    f"""SELECT DATE_TRUNC('month', {date_column}), count(*)
                          FROM cases_case
                         WHERE {date_column} >= '{start_date}'
                         GROUP BY 1 ORDER BY 1;"""
                )
                all_table_rows: List[Dict[str, Union[datetime, int]]] = [
                    {"month_date": month_date, "count": count}
                    for month_date, count in cursor.fetchall()
                ]
                if all_table_rows:
                    yearly_metrics.append(
                        build_yearly_metric_chart(label=label, all_table_rows=all_table_rows)
                    )

        extra_context: Dict[str, Any] = {
            "first_of_last_month": first_of_last_month,
            "monthly_metrics": monthly_metrics,
            "yearly_metrics": yearly_metrics,
        }
        return {**extra_context, **context}
