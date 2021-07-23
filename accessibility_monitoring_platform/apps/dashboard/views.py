"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from ..cases.models import Case


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)
        if self.request.GET.get("view") == "View all cases":
            return self.macro_view(context, user)
        return self.user_view(context, user)

    def user_view(self, context, user):
        """Shows and filters user cases"""
        all_entries = Case.objects.all()
        user_entries = Case.objects.filter(auditor=user).order_by("created")
        qa_entries = Case.objects.filter(reviewer=user).order_by("created")

        sorted_cases = {
            "new_case": user_entries.filter(
                status="new-case"
            ),
            "test_in_progress": user_entries.filter(
                status="test-in-progress"
            ),
            "reports_in_progress": user_entries.filter(
                status="report-in-progress"
            ),
            "qa_in_progress": user_entries.filter(
                status="qa-in-progress"
            ),
            "requires_your_review": qa_entries.filter(
                qa_status="in-qa"
            ),
            "report_ready_to_send": user_entries.filter(
                status="report-ready-to-send"
            ),
            "in_report_correspondence": user_entries.filter(
                status="in-report-correspondence"
            ).order_by("report_sent_date"),
            "in_probation_period": user_entries.filter(
                status="in-probation-period"
            ).order_by("report_followup_week_12_due_date"),
            "in_12_week_correspondence": user_entries.filter(
                status="in-12-week-correspondence"
            ),
            "final_decision_due": user_entries.filter(
                status="final-decision-due"
            ),
            "recently_completed": user_entries.filter(
                status="complete",
                completed__gte=timezone.now() - timedelta(30)
            ),
            "in_equality_body_correspondence": user_entries.filter(
                equalities_body_status="in-correspondence"
            ),
        }

        context.update(
            {
                "sorted_cases": sorted_cases,
                "total_cases": len(all_entries),
                "your_cases": len(user_entries),
                "unassigned_cases": len(all_entries.filter(status="unassigned-case")),
                "unassigned_qa_cases": len(
                    all_entries.filter(qa_status="unassigned_qa_case")
                ),
                "today": date.today(),
            }
        )
        return context

    def macro_view(self, context, user):
        """Shows and filters all cases"""
        all_entries = Case.objects.all()
        user_entries = Case.objects.filter(auditor=user).order_by("created")
        sorted_cases = {
            "unassigned_cases": all_entries.filter(
                status="unassigned-case"
            ),
            "new_case": all_entries.filter(
                status="new-case"
            ),
            "test_in_progress": all_entries.filter(
                status="test-in-progress"
            ),
            "reports_in_progress": all_entries.filter(
                status="report-in-progress"
            ),
            "qa_cases": all_entries.filter(
                qa_status="in_qa"
            ),
            "unassigned_qa_cases": all_entries.filter(
                qa_status="unassigned_qa_case"
            ),
            "awaiting_response_to_report": all_entries.filter(
                status="awaiting-response"
            ).order_by(
                "report_sent_date"
            ),
            "twelve_week_review_due": all_entries.filter(
                status="12w-review"
            ).order_by(
                "report_followup_week_12_due_date"
            ),
            "update_for_enforcement_bodies_due": all_entries.filter(
                status="update-for-enforcement-bodies-due"
            ),
            "recently_completed": all_entries.filter(
                status="complete",
                completed__gte=timezone.now() - timedelta(30)
            ),
        }

        context.update(
            {
                "sorted_cases": sorted_cases,
                "total_cases": len(all_entries),
                "your_cases": len(user_entries),
                "unassigned_cases": len(all_entries.filter(status="unassigned-case")),
                "unassigned_qa_cases": len(
                    all_entries.filter(qa_status="unassigned_qa_case")
                ),
                "today": date.today(),
                "macro_view": True,
            }
        )
        return context
