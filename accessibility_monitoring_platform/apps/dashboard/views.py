"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date, datetime, timedelta
from ..cases.models import Case
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.generic import TemplateView


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
            "qa_cases": qa_entries.filter(
                qa_status="in_qa"
            ),
            "awaiting_response_to_report": user_entries.filter(
                status="awaiting-response"
            ).order_by(
                "report_sent_date"
            ),
            "twelve_week_review_due": user_entries.filter(
                status="12w-review"
            ).order_by(
                "week_12_followup_date"
            ),
            "update_for_enforcement_bodies_due": user_entries.filter(
                status="update-for-enforcement-bodies-due"
            ),
            "recently_completed": user_entries.filter(
                status="complete",
                completed__gte=datetime.now() - timedelta(30)
            ),
        }

        headers = {
            "new_case": ["Date created", "Case", "Organisation", "Step progress"],
            "test_in_progress": [
                "Date created",
                "Case",
                "Organisation",
                "Step progress",
            ],
            "reports_in_progress": [
                "Date created",
                "Case",
                "Organisation",
                "Step progress",
            ],
            "qa_cases": ["Date created", "Case", "Organisation", "Step progress"],
            "awaiting_response_to_report": [
                "Days since being sent",
                "Case",
                "Organisation",
                "Step progress",
            ],
            "twelve_week_review_due": [
                "Review due",
                "Case",
                "Organisation",
                "Step progress",
            ],
            "update_for_enforcement_bodies_due": [
                "Review due",
                "Case",
                "Organisation",
                "Step progress",
            ],
            "recently_completed": [
                "Completed on",
                "Case",
                "Organisation",
                "Step progress",
            ],
        }

        context.update(
            {
                "sorted_cases": sorted_cases,
                "headers": headers,
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
                "week_12_followup_date"
            ),
            "update_for_enforcement_bodies_due": all_entries.filter(
                status="update-for-enforcement-bodies-due"
            ),
            "recently_completed": all_entries.filter(
                status="complete",
                completed__gte=datetime.now() - timedelta(30)
            ),
        }

        headers = {
            "new_case": ["Date created", "Case", "Organisation", "Auditor"],
            "test_in_progress": ["Date created", "Case", "Organisation", "Auditor"],
            "reports_in_progress": ["Date created", "Case", "Organisation", "Auditor"],
            "qa_cases": ["Date created", "Case", "Organisation", "QA auditor"],
            "unassigned_qa_cases": [
                "Date created",
                "Case",
                "Organisation",
                "QA auditor",
            ],
            "awaiting_response_to_report": [
                "Days since being sent",
                "Case",
                "Organisation",
                "Auditor",
            ],
            "twelve_week_review_due": ["Review due", "Case", "Organisation", "Auditor"],
            "update_for_enforcement_bodies_due": [
                "Review due",
                "Case",
                "Organisation",
                "Auditor",
            ],
            "recently_completed": ["Completed on", "Case", "Organisation", "Auditor"],
        }

        context.update(
            {
                "sorted_cases": sorted_cases,
                "headers": headers,
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
