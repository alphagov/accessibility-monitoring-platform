"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from ..cases.models import Case, STATUS_READY_TO_QA


class DashboardView(TemplateView):
    """Filters and displays the cases into states on the landing page"""

    template_name: str = "dashboard/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user: User = get_object_or_404(User, id=self.request.user.id)
        if self.request.GET.get("view") == "View all cases":
            context["page_title"] = "All cases"
            return self.show_all_cases(context, user)
        context["page_title"] = "Your cases"
        return self.user_view(context, user)

    def user_view(self, context, user):
        """Shows and filters user cases"""
        all_entries = Case.objects.all()
        user_entries = Case.objects.filter(auditor=user).order_by("created")
        qa_entries = Case.objects.filter(reviewer=user).order_by("created")

        sorted_cases = {
            "unknown": user_entries.filter(
                status="unknown"
            ),
            "test_in_progress": user_entries.filter(
                status="test-in-progress"
            ),
            "reports_in_progress": user_entries.filter(
                status="report-in-progress"
            ),
            "ready_for_qa": user_entries.filter(
                qa_status="unassigned-qa-case"
            ),
            "qa_in_progress": user_entries.filter(
                qa_status="in-qa"
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
            "in_correspondence_with_equalities_body": user_entries.filter(
                status="in-correspondence-with-equalities-body"
            ),
            "recently_completed": user_entries.filter(
                status="complete",
                completed_date__gte=timezone.now() - timedelta(30)
            ),
        }
        context.update(
            {
                "sorted_cases": sorted_cases,
                "total_cases": len(all_entries.exclude(status="complete")),
                "your_cases": len(user_entries.exclude(status="complete")),
                "unassigned_cases": len(all_entries.filter(status="unassigned-case")),
                "unassigned_qa_cases": len(
                    all_entries.filter(qa_status=STATUS_READY_TO_QA)
                ),
                "today": date.today(),
            }
        )
        return context

    def show_all_cases(self, context, user):
        """Shows and filters all cases"""
        all_entries = Case.objects.all()
        user_entries = Case.objects.filter(auditor=user).order_by("created")
        sorted_cases = {
            "unknown": all_entries.filter(
                status="unknown"
            ),
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
            "ready_for_qa": all_entries.filter(
                qa_status=STATUS_READY_TO_QA
            ),
            "qa_in_progress": all_entries.filter(
                qa_status="in-qa"
            ),
            "report_ready_to_send": all_entries.filter(
                status="report-ready-to-send"
            ),
            "in_report_correspondence": all_entries.filter(
                status="in-report-correspondence"
            ).order_by("report_sent_date"),
            "in_probation_period": all_entries.filter(
                status="in-probation-period"
            ).order_by("report_followup_week_12_due_date"),
            "in_12_week_correspondence": all_entries.filter(
                status="in-12-week-correspondence"
            ),
            "final_decision_due": all_entries.filter(
                status="final-decision-due"
            ),
            "in_correspondence_with_equalities_body": all_entries.filter(
                status="in-correspondence-with-equalities-body"
            ),
            "recently_completed": all_entries.filter(
                status="complete",
                completed_date__gte=timezone.now() - timedelta(30)
            ),
        }
        context.update(
            {
                "sorted_cases": sorted_cases,
                "total_cases": len(all_entries.exclude(status="complete")),
                "your_cases": len(user_entries.exclude(status="complete")),
                "unassigned_cases": len(all_entries.filter(status="unassigned-case")),
                "unassigned_qa_cases": len(
                    all_entries.filter(qa_status=STATUS_READY_TO_QA)
                ),
                "today": date.today(),
                "show_all_cases": True,
            }
        )
        return context
