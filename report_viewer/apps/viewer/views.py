"""Views for report viewer"""
from typing import Any, Dict, Type

from django.shortcuts import get_object_or_404
from django.views.generic import FormView
from django.contrib import messages

from accessibility_monitoring_platform.apps.common.views import PlatformTemplateView
from accessibility_monitoring_platform.apps.reports.models import Report, ReportFeedback
from accessibility_monitoring_platform.apps.reports.forms import ReportFeedbackForm

from accessibility_monitoring_platform.apps.s3_read_write.utils import (
    S3ReadWriteReport,
    NO_REPORT_HTML,
)
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

FORM_SUBMITTED_SUCCESSFULLY: str = "Form submitted successfully"


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "viewer/accessibility_statement.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "viewer/privacy_notice.html"


class ViewReport(FormView):
    """
    View of report on S3
    """

    template_name: str = "reports/accessibility_report_base.html"
    form_class: Type[ReportFeedbackForm] = ReportFeedbackForm

    def get_context_data(
        self, *args, **kwargs  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """Add table rows to context for each section of page"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        s3_report = get_object_or_404(S3Report, guid=self.kwargs["guid"])
        s3_rw = S3ReadWriteReport()
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=self.kwargs["guid"])
        if raw_html == NO_REPORT_HTML and s3_report.html:
            raw_html = s3_report.html
        report = Report.objects.get(case=s3_report.case)

        all_error_messages_content = [
            msg.message for msg in list(messages.get_messages(self.request))
        ]
        form_submitted_successfully: bool = (
            FORM_SUBMITTED_SUCCESSFULLY in all_error_messages_content
        )

        context.update(
            {
                "html_report": raw_html,
                "report": report,
                "s3_report": s3_report,
                "guid": self.kwargs["guid"],
                "form_submitted": form_submitted_successfully,
                "report_viewer": True,
            }
        )
        return context

    def form_valid(self, form: ReportFeedbackForm):
        """Process contents of valid form"""
        report_feedback: ReportFeedback = form.save(commit=False)
        report_feedback.guid = self.kwargs["guid"]
        report_feedback.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            FORM_SUBMITTED_SUCCESSFULLY,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path
