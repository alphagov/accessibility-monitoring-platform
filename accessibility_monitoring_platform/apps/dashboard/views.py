"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..cases.models import TestType
from ..common.utils import checks_if_2fa_is_enabled, get_recent_changes_to_platform
from ..detailed.models import DetailedCase
from ..notifications.utils import build_task_list, get_task_type_counts
from ..simplified.models import SimplifiedCase
from .utils import group_cases_by_status, group_detailed_cases_by_status


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore

        type_param: str | None = self.request.GET.get("type")
        filter_param: str | None = self.request.GET.get("filter")

        test_type: TestType = (
            TestType.SIMPLIFIED if type_param is None else TestType.DETAILED
        )

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
        else:
            cases: QuerySet[DetailedCase] = DetailedCase.objects.all().select_related(
                "auditor", "reviewer"
            )

        qa_cases: QuerySet[SimplifiedCase | DetailedCase] = cases.filter(
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
            else:  # Detailed cases
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
        elif filter_param == "qa-filter":
            cases: QuerySet[SimplifiedCase | DetailedCase] = qa_cases

        cases_by_status = {}
        if cases and test_type == TestType.SIMPLIFIED:
            cases_by_status: dict[str, list[SimplifiedCase]] = group_cases_by_status(
                simplified_cases=cases
            )
        elif cases and test_type == TestType.DETAILED:
            cases_by_status: dict[str, dict[str, list[DetailedCase] | str]] = (
                group_detailed_cases_by_status(detailed_cases=cases)
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
