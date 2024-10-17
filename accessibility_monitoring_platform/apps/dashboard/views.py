"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from datetime import date

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..cases.models import Case
from ..common.utils import checks_if_2fa_is_enabled, get_recent_changes_to_platform
from .utils import (
    get_all_cases_in_qa,
    group_cases_by_status,
    return_cases_requiring_user_review,
)


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)  # type: ignore
        all_cases: list[Case] = list(
            Case.objects.all().select_related("auditor", "reviewer").all()
        )

        view_url_param: str | None = self.request.GET.get("view")
        show_all_cases = view_url_param == "View all cases"

        if show_all_cases:
            cases: list[Case] = all_cases
        else:
            cases: list[Case] = [case for case in all_cases if case.auditor == user]

        cases_by_status: dict[str, list[Case]] = group_cases_by_status(cases=cases)

        cases_by_status["requires_your_review"] = return_cases_requiring_user_review(
            cases=all_cases,
            user=user,
        )

        incomplete_cases: list[Case] = [
            case
            for case in all_cases
            if (
                case.status.status != "complete"
                and case.status.status != "case-closed-sent-to-equalities-body"
                and case.status.status != "deleted"
                and case.status.status != "deactivated"
            )
        ]
        unassigned_cases: list[Case] = sorted(
            [case for case in all_cases if case.status.status == "unassigned-case"],
            key=lambda case: (case.created),  # type: ignore
        )
        cases_by_status["unassigned_cases"] = unassigned_cases

        context.update(
            {
                "cases_by_status": cases_by_status,
                "total_incomplete_cases": len(incomplete_cases),
                "total_your_active_cases": len(
                    [case for case in incomplete_cases if case.auditor == user]
                ),
                "total_unassigned_cases": len(unassigned_cases),
                "today": date.today(),
                "show_all_cases": show_all_cases,
                "page_title": "All cases" if show_all_cases else "Your cases",
                "mfa_disabled": not checks_if_2fa_is_enabled(user=user),
                "recent_changes_to_platform": get_recent_changes_to_platform(),
                "all_cases_in_qa": get_all_cases_in_qa(all_cases=all_cases),
            }
        )
        return context
