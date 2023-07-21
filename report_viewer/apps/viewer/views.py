"""Views for report viewer"""
import os
from typing import Any, Dict, Type

import logging

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

from .utils import show_warning

FORM_SUBMITTED_SUCCESSFULLY: str = "Form submitted successfully"

logger = logging.getLogger(__name__)


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "viewer/accessibility_statement.html"


class MoreInformationTemplateView(PlatformTemplateView):
    template_name: str = "viewer/more_information.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "viewer/privacy_notice.html"


class StatusTemplateView(PlatformTemplateView):
    template_name: str = "viewer/status.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add environmental variables to context to determine if application is
        running on PaaS or AWS.
        """
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["vcap_services"] = os.getenv("VCAP_SERVICES", "")
        context["copilot_application_name"] = os.getenv("COPILOT_APPLICATION_NAME", "")
        return context


class ViewReport(FormView):
    """
    View of report on S3
    """

    template_name: str = "reports_common/accessibility_report_base.html"
    form_class: Type[ReportFeedbackForm] = ReportFeedbackForm

    def get_context_data(
        self, *args, **kwargs  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        guid: str = self.kwargs["guid"]
        s3_report = get_object_or_404(S3Report, guid=guid)
        s3_rw = S3ReadWriteReport()
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=guid)
        if raw_html == NO_REPORT_HTML and s3_report.html:
            raw_html = s3_report.html
            logger.warning("Report %s not found on S3", guid)
        report: Report = s3_report.case.report

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
                "show_warning": show_warning(),
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
