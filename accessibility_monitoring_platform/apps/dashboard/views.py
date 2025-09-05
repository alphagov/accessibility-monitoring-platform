"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.db.models import Q

from ..common.utils import checks_if_2fa_is_enabled, get_recent_changes_to_platform
from ..notifications.utils import build_task_list, get_task_type_counts
from ..simplified.models import SimplifiedCase
from ..detailed.models import DetailedCase
from .utils import (
    group_cases_by_status,
    group_detailed_cases_by_status
)


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore

        type_param: str | None = self.request.GET.get("type")
        filter_param: str | None = self.request.GET.get("filter")

        case_list = None
        if not type_param:  # Default is simplified
            case_list = SimplifiedCase.objects.all().select_related("auditor", "reviewer").exclude(
                status__in=[
                    SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
                    SimplifiedCase.Status.COMPLETE,
                    SimplifiedCase.Status.DEACTIVATED
                ]
            )
        else:  # This will be replaced by type_param == "detailed": when mobile cases are implemented
            case_list = DetailedCase.objects.all().select_related("auditor", "reviewer").all()

        qa_count = case_list.filter(
            status__in=[
                SimplifiedCase.Status.QA_IN_PROGRESS,
                SimplifiedCase.Status.READY_TO_QA,
            ]
        ).count()

        if isinstance(case_list.first(), SimplifiedCase) and not filter_param:  # Simplified and your cases
            case_list = case_list.filter(
                Q(auditor=user)
                | Q(status=SimplifiedCase.Status.UNASSIGNED)
            )
        elif isinstance(case_list.first(), DetailedCase) and not filter_param:  # Detailed and your cases
            case_list = case_list.filter(
                Q(auditor=user) | Q(
                    status__in=[
                        SimplifiedCase.Status.UNASSIGNED,
                        DetailedCase.Status.PSB_INFO_REQ,
                        DetailedCase.Status.PSB_INFO_CHASING,
                        DetailedCase.Status.PSB_INFO_REQ_ACK,
                        DetailedCase.Status.PSB_INFO_RECEIVED,
                        DetailedCase.Status.PSB_INFO_REQ,
                        DetailedCase.Status.PSB_INFO_CHASING,
                        DetailedCase.Status.PSB_INFO_REQ_ACK,
                        DetailedCase.Status.PSB_INFO_RECEIVED,
                    ]
                )
            )
        elif filter_param == "qa-filter":  # Looks into the 'all cases' queryset and pulls out the QA cases
            case_list = case_list.filter(
                status__in=[
                    SimplifiedCase.Status.QA_IN_PROGRESS,
                    SimplifiedCase.Status.READY_TO_QA,
                ]
            )

        cases_by_status = {}
        if case_list and isinstance(case_list.first(), SimplifiedCase):
            cases_by_status = group_cases_by_status(
                simplified_cases=case_list
            )
        elif case_list and isinstance(case_list.first(), DetailedCase):
            cases_by_status = group_detailed_cases_by_status(
                detailed_cases=case_list
            )

        context.update(
            {
                "type": type_param,
                "filter": filter_param,
                "cases_by_status": cases_by_status,
                "today": date.today(),
                "mfa_disabled": not checks_if_2fa_is_enabled(user=user),
                "recent_changes_to_platform": get_recent_changes_to_platform(),
                "task_type_counts": get_task_type_counts(tasks=build_task_list(user=self.request.user)),
                "qa_count": qa_count,
            }
        )
        return context
