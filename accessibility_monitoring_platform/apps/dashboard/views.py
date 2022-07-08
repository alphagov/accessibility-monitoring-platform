"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Union

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from ..common.models import PlatformChange
from ..common.utils import checks_if_2fa_is_enabled
from ..cases.models import Case

from .utils import (
    group_cases_by_status,
    group_cases_by_qa_status,
    return_cases_requiring_user_review,
)


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore
        all_cases: List[Case] = list(
            Case.objects.all().select_related("auditor", "reviewer").all()
        )

        view_url_param: Union[str, None] = self.request.GET.get("view")
        show_all_cases = view_url_param == "View all cases"

        if show_all_cases:
            cases: List[Case] = all_cases
        else:
            cases: List[Case] = [case for case in all_cases if case.auditor == user]

        cases_by_status: Dict[str, List[Case]] = group_cases_by_status(cases=cases)
        cases_by_status.update(group_cases_by_qa_status(cases=all_cases))

        cases_by_status["requires_your_review"] = return_cases_requiring_user_review(
            cases=all_cases, user=user
        )

        incomplete_cases: List[Case] = [
            case for case in all_cases if case.status != "complete"
        ]
        unassigned_cases: List[Case] = sorted(
            [case for case in all_cases if case.status == "unassigned-case"],
            key=lambda case: (case.created),  # type: ignore
        )
        cases_by_status["unassigned_cases"] = unassigned_cases
        twenty_four_hours_ago: datetime = timezone.now() - timedelta(hours=24)

        context.update(
            {
                "cases_by_status": cases_by_status,
                "total_incomplete_cases": len(incomplete_cases),
                "total_your_active_cases": len(
                    [case for case in incomplete_cases if case.auditor == user]
                ),
                "total_unassigned_cases": len(unassigned_cases),
                "total_ready_to_qa_cases": len(cases_by_status["ready_for_qa"]),
                "today": date.today(),
                "show_all_cases": show_all_cases,
                "page_title": "All cases" if show_all_cases else "Your cases",
                "mfa_disabled": not checks_if_2fa_is_enabled(user=user),
                "recent_platform_changes": PlatformChange.objects.filter(created__gte=twenty_four_hours_ago)
            }
        )
        return context
