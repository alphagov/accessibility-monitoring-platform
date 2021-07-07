"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date
from ..cases.models import Case
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from ..common.utils import filter_by_status


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
            "new_case": filter_by_status(
                user_entries,
                "new_case"
            ),
            "test_in_progress": filter_by_status(
                user_entries,
                "test_in_progress"
            ),
            "reports_in_progress": filter_by_status(
                user_entries,
                "report_in_progress"
            ),
            "qa_cases": filter_by_status(
                qa_entries,
                "qa_cases"
            ),
            "awaiting_response_to_report": filter_by_status(
                user_entries,
                "awaiting_response_to_report"
            ),
            "twelve_week_review_due": filter_by_status(
                user_entries,
                "twelve_week_review_due"
            ),
            "update_for_enforcement_bodies_due": filter_by_status(
                user_entries,
                "update_for_enforcement_bodies_due"
            ),
            "recently_completed": filter_by_status(
                user_entries,
                "recently_completed"
            ),
        }

        headers = {
            "new_case": [
                "Date created",
                "Case",
                "Organisation",
                "Step progress"
            ],
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
            "qa_cases": [
                "Date created",
                "Case",
                "Organisation",
                "Step progress"
            ],
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
                "unassigned_cases": len(
                    all_entries.filter(
                        auditor__isnull=True,
                        is_archived=False,
                        is_public_sector_body=True,
                    )
                ),
                "unassigned_qa_cases": len(
                    all_entries.filter(
                        reviewer__isnull=True,
                        report_review_status="ready-to-review",
                        report_approved_status="no",
                        is_archived=False,
                        is_public_sector_body=True,
                    )
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
            "unassigned_cases": filter_by_status(
                all_entries,
                "unassigned_cases"
            ),
            "new_case": filter_by_status(
                all_entries,
                "new_case"
            ),
            "test_in_progress": filter_by_status(
                all_entries,
                "test_in_progress"
            ),
            "reports_in_progress": filter_by_status(
                all_entries,
                "report_in_progress"
            ),
            "qa_cases": filter_by_status(
                all_entries,
                "qa_cases"
            ),
            "unassigned_qa_cases": filter_by_status(
                all_entries,
                "unassigned_qa_cases"
            ),
            "awaiting_response_to_report": filter_by_status(
                all_entries,
                "awaiting_response_to_report"
            ),
            "twelve_week_review_due": filter_by_status(
                all_entries,
                "twelve_week_review_due"
            ),
            "update_for_enforcement_bodies_due": filter_by_status(
                all_entries,
                "update_for_enforcement_bodies_due"
            ),
            "recently_completed": filter_by_status(
                all_entries,
                "recently_completed"
            ),
        }

        headers = {
            "new_case": [
                "Date created",
                "Case",
                "Organisation",
                "Auditor"
            ],
            "test_in_progress": [
                "Date created",
                "Case",
                "Organisation",
                "Auditor"
            ],
            "reports_in_progress": [
                "Date created",
                "Case",
                "Organisation",
                "Auditor"
            ],
            "qa_cases": [
                "Date created",
                "Case",
                "Organisation",
                "QA auditor"
            ],
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
            "twelve_week_review_due": [
                "Review due",
                "Case",
                "Organisation",
                "Auditor"
            ],
            "update_for_enforcement_bodies_due": [
                "Review due",
                "Case",
                "Organisation",
                "Auditor",
            ],
            "recently_completed": [
                "Completed on",
                "Case",
                "Organisation",
                "Auditor"
            ],
        }

        context.update(
            {
                "sorted_cases": sorted_cases,
                "headers": headers,
                "total_cases": len(all_entries),
                "your_cases": len(user_entries),
                "unassigned_cases": len(
                    all_entries.filter(
                        auditor__isnull=True,
                        is_archived=False,
                        is_public_sector_body=True,
                    )
                ),
                "unassigned_qa_cases": len(
                    all_entries.filter(
                        reviewer__isnull=True,
                        report_review_status="ready-to-review",
                        report_approved_status="no",
                        is_archived=False,
                        is_public_sector_body=True,
                    )
                ),
                "today": date.today(),
                "macro_view": True,
            }
        )
        return context
