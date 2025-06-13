"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..common.utils import checks_if_2fa_is_enabled, get_recent_changes_to_platform
from ..notifications.utils import build_task_list, get_task_type_counts
from ..simplified.models import SimplifiedCase
from .utils import (
    get_all_cases_in_qa,
    group_cases_by_status,
    return_cases_requiring_user_review,
)


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore
        all_simplified_cases: list[SimplifiedCase] = list(
            SimplifiedCase.objects.all().select_related("auditor", "reviewer").all()
        )

        view_url_param: str | None = self.request.GET.get("view")
        show_all_cases = view_url_param == "View all cases"

        if show_all_cases:
            simplified_cases: list[SimplifiedCase] = all_simplified_cases
        else:
            simplified_cases: list[SimplifiedCase] = [
                simplified_case
                for simplified_case in all_simplified_cases
                if simplified_case.auditor == user
            ]

        cases_by_status: dict[str, list[SimplifiedCase]] = group_cases_by_status(
            simplified_cases=simplified_cases
        )

        cases_by_status["requires_your_review"] = return_cases_requiring_user_review(
            simplified_cases=all_simplified_cases,
            user=user,
        )

        incomplete_cases: list[SimplifiedCase] = [
            simplified_case
            for simplified_case in all_simplified_cases
            if (
                simplified_case.status != "complete"
                and simplified_case.status != "case-closed-sent-to-equalities-body"
                and simplified_case.status != "deleted"
                and simplified_case.status != "deactivated"
            )
        ]
        unassigned_cases: list[SimplifiedCase] = sorted(
            [
                simplified_case
                for simplified_case in all_simplified_cases
                if simplified_case.status == "unassigned-case"
            ],
            key=lambda simplified_case: (simplified_case.created),  # type: ignore
        )
        cases_by_status["unassigned_cases"] = unassigned_cases

        context.update(
            {
                "cases_by_status": cases_by_status,
                "total_your_active_cases": len(
                    [
                        simplified_case
                        for simplified_case in incomplete_cases
                        if simplified_case.auditor == user
                    ]
                ),
                "today": date.today(),
                "show_all_cases": show_all_cases,
                "page_title": "All cases" if show_all_cases else "Your cases",
                "mfa_disabled": not checks_if_2fa_is_enabled(user=user),
                "recent_changes_to_platform": get_recent_changes_to_platform(),
                "all_cases_in_qa": get_all_cases_in_qa(all_cases=all_simplified_cases),
                "task_type_counts": get_task_type_counts(
                    tasks=build_task_list(user=self.request.user)
                ),
            }
        )
        return context
