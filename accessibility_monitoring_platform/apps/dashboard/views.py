"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date
from typing import Dict, List

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..cases.models import Case

from .utils import (
    group_cases_by_status,
    group_cases_by_qa_status,
    return_cases_requiring_user_review,
    return_recently_completed_cases,
)


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)
        all_cases: List[Case] = list(Case.objects.all())

        show_all_cases: bool = self.request.GET.get("view") == "View all cases"
        cases: List[Case] = all_cases if show_all_cases else [case for case in all_cases if case.auditor == user]

        cases_by_status: Dict[str, List[Case]] = group_cases_by_status(cases=cases)
        cases_by_status.update(group_cases_by_qa_status(cases=cases))

        cases_by_status["requires_your_review"] = return_cases_requiring_user_review(
            cases=all_cases, user=user
        )
        cases_by_status["recently_completed"] = return_recently_completed_cases(
            cases=cases
        )

        incomplete_cases: List[Case] = [
            case for case in all_cases if case.status != "complete"
        ]

        context.update(
            {
                "cases_by_status": cases_by_status,
                "total_incomplete_cases": len(incomplete_cases),
                "total_your_active_cases": len(
                    [case for case in incomplete_cases if case.auditor == user]
                ),
                "total_unassigned_cases": len(
                    [
                        case
                        for case in incomplete_cases
                        if case.status == "unassigned-case"
                    ]
                ),
                "total_ready_to_qa_cases": len(cases_by_status["ready_for_qa"]),
                "today": date.today(),
                "show_all_cases": show_all_cases,
                "page_title": "All cases" if show_all_cases else "Your cases",
            }
        )
        return context
