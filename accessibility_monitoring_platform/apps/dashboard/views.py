"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from datetime import date
from typing import Any

from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from ..cases.models import BaseCase, TestType
from ..common.utils import (
    checks_if_2fa_is_enabled,
    get_recent_changes_to_platform,
    record_common_model_update_event,
)
from ..detailed.models import DetailedCase
from ..mobile.models import MobileCase
from ..notifications.models import CaseTask
from ..notifications.utils import build_task_list, get_task_type_counts
from ..simplified.models import SimplifiedCase
from .utils import group_cases_by_status, group_detailed_or_mobile_cases_by_status

DEFAULT_INBOX_FILTER: str = "all"


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore

        type_param: str | None = self.request.GET.get("type")
        filter_param: str | None = self.request.GET.get("filter")

        test_type: TestType = TestType.SIMPLIFIED if type_param is None else type_param

        if test_type == TestType.SIMPLIFIED:
            cases: QuerySet[SimplifiedCase] = (
                SimplifiedCase.objects.all()
                .select_related("auditor", "reviewer")
                .exclude(
                    status__in=[
                        SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
                        SimplifiedCase.Status.COMPLETE,
                        SimplifiedCase.Status.DEACTIVATED,
                    ]
                )
            )
        elif test_type == TestType.DETAILED:
            cases: QuerySet[DetailedCase] = DetailedCase.objects.all().select_related(
                "auditor", "reviewer"
            )
        else:
            cases: QuerySet[MobileCase] = MobileCase.objects.all().select_related(
                "auditor", "reviewer"
            )

        qa_cases: QuerySet[SimplifiedCase | DetailedCase | MobileCase] = cases.filter(
            status__in=[
                SimplifiedCase.Status.QA_IN_PROGRESS,
                SimplifiedCase.Status.READY_TO_QA,
            ]
        )

        if not filter_param:  # Your cases
            if test_type == TestType.SIMPLIFIED:
                cases: QuerySet[SimplifiedCase] = cases.filter(
                    Q(auditor=user) | Q(status=SimplifiedCase.Status.UNASSIGNED)
                )
            elif test_type == TestType.DETAILED:
                cases: QuerySet[DetailedCase] = cases.filter(
                    Q(auditor=user)
                    | Q(
                        status__in=[
                            SimplifiedCase.Status.UNASSIGNED,
                            DetailedCase.Status.PSB_INFO_REQ,
                            DetailedCase.Status.PSB_INFO_CHASING,
                            DetailedCase.Status.PSB_INFO_REQ_ACK,
                            DetailedCase.Status.PSB_INFO_RECEIVED,
                        ]
                    )
                )
            else:  # Mobile cases
                cases: QuerySet[MobileCase] = cases.filter(
                    Q(auditor=user)
                    | Q(
                        status__in=[
                            SimplifiedCase.Status.UNASSIGNED,
                            MobileCase.Status.PSB_INFO_REQ,
                            MobileCase.Status.PSB_INFO_CHASING,
                            MobileCase.Status.PSB_INFO_REQ_ACK,
                            MobileCase.Status.PSB_INFO_RECEIVED,
                        ]
                    )
                )
        elif filter_param == "qa-filter":
            cases: QuerySet[SimplifiedCase | DetailedCase | MobileCase] = qa_cases

        cases_by_status: dict[
            str, list[SimplifiedCase] | dict[str, list[DetailedCase] | str]
        ] = {}
        if cases and test_type == TestType.SIMPLIFIED:
            cases_by_status: dict[str, list[SimplifiedCase]] = group_cases_by_status(
                simplified_cases=cases
            )
        elif cases and test_type == TestType.DETAILED:
            cases_by_status: dict[
                str, dict[str, list[DetailedCase | MobileCase] | str]
            ] = group_detailed_or_mobile_cases_by_status(cases=cases)
        elif cases and test_type == TestType.MOBILE:
            cases_by_status: dict[
                str, dict[str, list[DetailedCase | MobileCase] | str]
            ] = group_detailed_or_mobile_cases_by_status(
                cases=cases, test_type=TestType.MOBILE
            )

        context.update(
            {
                "type": type_param,
                "filter": filter_param,
                "cases_by_status": cases_by_status,
                "today": date.today(),
                "mfa_disabled": not checks_if_2fa_is_enabled(user=user),
                "recent_changes_to_platform": get_recent_changes_to_platform(),
                "task_type_counts": get_task_type_counts(
                    tasks=build_task_list(user=self.request.user)
                ),
                "qa_count": qa_cases.count(),
            }
        )
        return context


class InboxView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/inbox.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)

        today: date = date.today()

        mark_complete_id: int | None = self.request.GET.get("mark_complete_id")
        if mark_complete_id is not None:
            case_task: CaseTask = CaseTask.objects.get(id=mark_complete_id)
            case_task.is_complete = True
            record_common_model_update_event(
                user=self.request.user, model_object=case_task
            )
            case_task.save()

        inbox_filter: str | None = self.request.GET.get(
            "inbox_filter", DEFAULT_INBOX_FILTER
        )
        context["inbox_filter"] = inbox_filter

        show_everyone: bool = "show_everyone" in self.request.GET

        if show_everyone:
            context["show_everyone"] = True
            user_url_param: str = "&show_everyone=true"

            case_tasks: QuerySet[CaseTask] = CaseTask.objects.filter(
                is_complete=False, is_deleted=False
            ).order_by("due_date")
            overdue_cases_count: int = BaseCase.objects.filter(
                due_date__lte=today
            ).count()
            overdue_cases_url_parameters: str = (
                f"?date_type=due_date&date_end_0={today.day}&date_end_1={today.month}&date_end_2={today.year}"
            )
        else:
            inbox_user_id: int = self.request.GET.get(
                "inbox_user_id", self.request.user.id
            )
            inbox_user: User = get_object_or_404(User, id=inbox_user_id)  # type: ignore
            context["inbox_user"] = inbox_user
            user_url_param: str = f"&inbox_user_id={inbox_user_id}"

            case_tasks: QuerySet[CaseTask] = inbox_user.casetask_set.filter(
                is_complete=False, is_deleted=False
            ).order_by("due_date")
            overdue_cases_count: int = BaseCase.objects.filter(
                auditor=inbox_user, due_date__lte=today
            ).count()
            overdue_cases_url_parameters: str = (
                f"?auditor={inbox_user_id}&date_type=due_date&date_end_0={today.day}&date_end_1={today.month}&date_end_2={today.year}"
            )

        inbox_menu_tasks = [
            {
                "label": "All",
                "number": case_tasks.count(),
                "current": inbox_filter == DEFAULT_INBOX_FILTER,
                "link": f'{reverse("dashboard:inbox")}?inbox_filter={DEFAULT_INBOX_FILTER}{user_url_param}',
            },
            {
                "label": "Reminders",
                "number": case_tasks.filter(type=CaseTask.Type.REMINDER).count(),
                "current": inbox_filter == CaseTask.Type.REMINDER,
                "link": f'{reverse("dashboard:inbox")}?inbox_filter={CaseTask.Type.REMINDER}{user_url_param}',
            },
            {
                "label": "QA comments",
                "number": case_tasks.filter(type=CaseTask.Type.QA_COMMENT).count(),
                "current": inbox_filter == CaseTask.Type.QA_COMMENT,
                "link": f'{reverse("dashboard:inbox")}?inbox_filter={CaseTask.Type.QA_COMMENT}{user_url_param}',
            },
            {
                "label": "Report approved",
                "number": case_tasks.filter(type=CaseTask.Type.REPORT_APPROVED).count(),
                "current": inbox_filter == CaseTask.Type.REPORT_APPROVED,
                "link": f'{reverse("dashboard:inbox")}?inbox_filter={CaseTask.Type.REPORT_APPROVED}{user_url_param}',
            },
            {
                "label": "Post case",
                "number": case_tasks.filter(type=CaseTask.Type.POSTCASE).count(),
                "current": inbox_filter == CaseTask.Type.POSTCASE,
                "link": f'{reverse("dashboard:inbox")}?inbox_filter={CaseTask.Type.POSTCASE}{user_url_param}',
            },
        ]
        context["inbox_menu_tasks"] = inbox_menu_tasks
        inbox_menu_cases = [
            {
                "label": "Unassigned cases",
                "number": BaseCase.objects.filter(
                    status=SimplifiedCase.Status.UNASSIGNED
                ).count(),
                "current": False,
                "link": f'{reverse("cases:case-list")}?status={SimplifiedCase.Status.UNASSIGNED}{user_url_param}',
            },
            {
                "label": "Overdue cases",
                "number": overdue_cases_count,
                "current": False,
                "link": f'{reverse("cases:case-list")}{overdue_cases_url_parameters}',
            },
        ]
        context["inbox_menu_cases"] = inbox_menu_cases

        historic_auditor_group: Group = Group.objects.get(name="Historic auditor")
        context["historic_auditors"] = historic_auditor_group.user_set.all()

        if inbox_filter != DEFAULT_INBOX_FILTER:
            case_tasks = case_tasks.filter(type=inbox_filter)

        context["case_tasks"] = case_tasks
        return context
