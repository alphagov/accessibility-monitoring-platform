"""
Common views
"""
from typing import Any, Dict, List, Type, Union
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone as django_timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..audits.models import Audit, CheckResult
from ..cases.models import (
    Case,
    IS_WEBSITE_COMPLIANT_COMPLIANT,
    RECOMMENDATION_NO_ACTION,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    REPORT_METHODOLOGY_ODT,
)
from ..s3_read_write.models import S3Report

from .chart import LineChart, build_yearly_metric_chart
from .forms import AMPContactAdminForm, AMPIssueReportForm, ActiveQAAuditorUpdateForm
from .metrics import (
    Timeseries,
    TimeseriesDatapoint,
    TimeseriesHtmlTable,
    calculate_current_month_progress,
    group_timeseries_data_by_month,
    calculate_metric_progress,
    count_statement_issues,
    build_html_table,
    convert_timeseries_pair_to_ratio,
)
from .models import IssueReport, Platform, ChangeToPlatform
from .page_title_utils import get_page_title
from .utils import get_platform_settings

CLOSED_CASE_STATUSES: List[str] = [
    "case-closed-sent-to-equalities-body",
    "complete",
    "case-closed-waiting-to-be-sent",
    "in-correspondence-with-equalities-body",
    "deactivated",
    "deleted",
]


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
        now: datetime = django_timezone.now()
        first_of_this_month: datetime = datetime(
            now.year, now.month, 1, tzinfo=timezone.utc
        )
        first_of_last_month: datetime = (
            datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
            if now.month > 1
            else datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        )

        progress_metrics: List[Dict[str, Union[str, int]]] = [
            calculate_current_month_progress(
                now=now,
                label="Cases created",
                this_month_value=Case.objects.filter(
                    created__gte=first_of_this_month
                ).count(),
                last_month_value=Case.objects.filter(created__gte=first_of_last_month)
                .filter(created__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                now=now,
                label="Tests completed",
                this_month_value=Case.objects.filter(
                    testing_details_complete_date__gte=first_of_this_month
                ).count(),
                last_month_value=Case.objects.filter(
                    testing_details_complete_date__gte=first_of_last_month
                )
                .filter(testing_details_complete_date__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                now=now,
                label="Reports sent",
                this_month_value=Case.objects.filter(
                    report_sent_date__gte=first_of_this_month
                ).count(),
                last_month_value=Case.objects.filter(
                    report_sent_date__gte=first_of_last_month
                )
                .filter(report_sent_date__lt=first_of_this_month)
                .count(),
            ),
            calculate_current_month_progress(
                now=now,
                label="Cases closed",
                this_month_value=Case.objects.filter(
                    completed_date__gte=first_of_this_month
                ).count(),
                last_month_value=Case.objects.filter(
                    completed_date__gte=first_of_last_month
                )
                .filter(completed_date__lt=first_of_this_month)
                .count(),
            ),
        ]

        yearly_metrics: List[
            Dict[
                str,
                Union[str, TimeseriesHtmlTable, List[TimeseriesDatapoint], LineChart],
            ]
        ] = []
        start_date: datetime = datetime(now.year - 1, now.month, 1, tzinfo=timezone.utc)
        for label, date_column_name in [
            ("Cases created", "created"),
            ("Tests completed", "testing_details_complete_date"),
            ("Reports sent", "report_sent_date"),
            ("Cases completed", "completed_date"),
        ]:
            datapoints: List[TimeseriesDatapoint] = group_timeseries_data_by_month(
                queryset=Case.objects,
                date_column_name=date_column_name,
                start_date=start_date,
            )
            columns: List[Timeseries] = [
                Timeseries(
                    label=label,
                    datapoints=group_timeseries_data_by_month(
                        queryset=Case.objects,
                        date_column_name=date_column_name,
                        start_date=start_date,
                    ),
                )
            ]
            yearly_metrics.append(
                {
                    "label": f"{label} over the last year",
                    "html_table": build_html_table(columns=columns),
                    "chart": build_yearly_metric_chart(
                        lines=[Timeseries(datapoints=datapoints)]
                    ),
                }
            )

        extra_context: Dict[str, Any] = {
            "first_of_last_month": first_of_last_month,
            "progress_metrics": progress_metrics,
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

        thirteen_month_tested: QuerySet[Audit] = Audit.objects.filter(
            date_of_test__gte=thirteen_month_start_date
        )
        thirteen_month_website_initial_compliant: QuerySet[
            Audit
        ] = thirteen_month_tested.filter(
            case__is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT
        )
        thirteen_month_statement_initial_compliant: QuerySet[
            Audit
        ] = thirteen_month_tested.filter(
            case__accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT
        )
        thirteen_month_retested_audits: QuerySet[Audit] = Audit.objects.filter(
            retest_date__gte=thirteen_month_start_date
        )
        thirteen_month_final_no_action: QuerySet[
            Audit
        ] = thirteen_month_retested_audits.filter(
            case__recommendation_for_enforcement=RECOMMENDATION_NO_ACTION
        )

        tested_by_month: Timeseries = Timeseries(
            label="Tested",
            datapoints=group_timeseries_data_by_month(
                queryset=thirteen_month_tested,
                date_column_name="date_of_test",
                start_date=thirteen_month_start_date,
            ),
        )
        website_initial_compliant_by_month: Timeseries = Timeseries(
            label="Compliant",
            datapoints=group_timeseries_data_by_month(
                queryset=thirteen_month_website_initial_compliant,
                date_column_name="date_of_test",
                start_date=thirteen_month_start_date,
            ),
        )
        statement_initial_compliant_by_month: Timeseries = Timeseries(
            label="Compliant",
            datapoints=group_timeseries_data_by_month(
                queryset=thirteen_month_statement_initial_compliant,
                date_column_name="date_of_test",
                start_date=thirteen_month_start_date,
            ),
        )
        retested_by_month: Timeseries = Timeseries(
            label="Retested",
            datapoints=group_timeseries_data_by_month(
                queryset=thirteen_month_retested_audits,
                date_column_name="retest_date",
                start_date=thirteen_month_start_date,
            ),
        )
        final_no_action_by_month: Timeseries = Timeseries(
            label="No action",
            datapoints=group_timeseries_data_by_month(
                queryset=thirteen_month_final_no_action,
                date_column_name="retest_date",
                start_date=thirteen_month_start_date,
            ),
        )

        website_initial_ratio: Timeseries = convert_timeseries_pair_to_ratio(
            label="Initial",
            partial_timeseries=website_initial_compliant_by_month,
            total_timeseries=tested_by_month,
        )
        statement_initial_ratio: Timeseries = convert_timeseries_pair_to_ratio(
            label="Initial",
            partial_timeseries=statement_initial_compliant_by_month,
            total_timeseries=tested_by_month,
        )
        final_ratio: Timeseries = convert_timeseries_pair_to_ratio(
            label="Final",
            partial_timeseries=final_no_action_by_month,
            total_timeseries=retested_by_month,
        )

        yearly_metrics: List[Dict[str, Union[str, TimeseriesHtmlTable, LineChart]]] = [
            {
                "label": "State of websites after retest in last year",
                "html_table": build_html_table(
                    columns=[
                        tested_by_month,
                        website_initial_compliant_by_month,
                        retested_by_month,
                        final_no_action_by_month,
                    ],
                ),
                "chart": build_yearly_metric_chart(
                    lines=[website_initial_ratio, final_ratio], y_axis_ratio=True
                ),
            },
            {
                "label": "State of accessibility statements after retest in last year",
                "html_table": build_html_table(
                    columns=[
                        tested_by_month,
                        statement_initial_compliant_by_month,
                        retested_by_month,
                        final_no_action_by_month,
                    ],
                ),
                "chart": build_yearly_metric_chart(
                    lines=[statement_initial_ratio, final_ratio], y_axis_ratio=True
                ),
            },
        ]

        extra_context: Dict[str, Any] = {
            "progress_metrics": progress_metrics,
            "equality_body_cases_completed_count": equality_body_cases_completed_count,
            "equality_body_cases_in_progress_count": equality_body_cases_in_progress_count,
            "yearly_metrics": yearly_metrics,
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
        now: datetime = django_timezone.now()
        first_of_this_month: datetime = datetime(
            now.year, now.month, 1, tzinfo=timezone.utc
        )
        first_of_last_month: datetime = (
            datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
            if now.month > 1
            else datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        )
        open_cases: QuerySet[Case] = Case.objects.all().exclude(
            status__in=CLOSED_CASE_STATUSES
        )
        number_open_cases: int = open_cases.count()
        number_template_reports: int = open_cases.filter(
            report_methodology=REPORT_METHODOLOGY_ODT
        ).count()

        progress_metrics: List[Dict[str, Union[str, int]]] = [
            calculate_current_month_progress(
                now=now,
                label="Published reports",
                this_month_value=S3Report.objects.filter(
                    created__gte=first_of_this_month
                )
                .filter(latest_published=True)
                .count(),
                last_month_value=S3Report.objects.filter(
                    created__gte=first_of_last_month,
                )
                .filter(created__lt=first_of_this_month)
                .filter(latest_published=True)
                .count(),
            ),
        ]

        start_date: datetime = datetime(now.year - 1, now.month, 1, tzinfo=timezone.utc)
        datapoints: List[TimeseriesDatapoint] = group_timeseries_data_by_month(
            queryset=S3Report.objects.filter(latest_published=True),
            date_column_name="created",
            start_date=start_date,
        )
        columns: List[Timeseries] = [
            Timeseries(
                label="Published reports",
                datapoints=datapoints,
            )
        ]
        yearly_metrics: List[Dict[str, Union[str, TimeseriesHtmlTable, LineChart]]] = [
            {
                "label": "Reports published over the last year",
                "html_table": build_html_table(columns=columns),
                "chart": build_yearly_metric_chart(
                    lines=[Timeseries(datapoints=datapoints)]
                ),
            }
        ]

        extra_context: Dict[str, Any] = {
            "number_open_cases": number_open_cases,
            "number_template_reports": number_template_reports,
            "first_of_last_month": first_of_last_month,
            "progress_metrics": progress_metrics,
            "yearly_metrics": yearly_metrics,
        }

        return {**extra_context, **context}
