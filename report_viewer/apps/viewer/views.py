"""Views for report viewer"""
from typing import Any, Dict, Type

import requests

from django.contrib import messages
from django.http import Http404
from django.views.generic import FormView

from rest_framework.authtoken.models import Token

from accessibility_monitoring_platform.apps.common.views import PlatformTemplateView
from accessibility_monitoring_platform.apps.reports.models import Report, ReportFeedback
from accessibility_monitoring_platform.apps.reports.forms import ReportFeedbackForm

from accessibility_monitoring_platform.apps.s3_read_write.utils import (
    S3ReadWriteReport,
    NO_REPORT_HTML,
)

from .utils import get_platform_domain

FORM_SUBMITTED_SUCCESSFULLY: str = "Form submitted successfully"


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "viewer/accessibility_statement.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "viewer/privacy_notice.html"


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
        token: Token = Token.objects.all()[0]
        headers = {"Authorization": f"Token {token.key}"}
        guid: str = self.kwargs.get("guid", "")
        platform_domain: str = get_platform_domain(self.request)
        protocol: str = "http://" if "localhost" in platform_domain else "https://"
        s3_report_response: requests.models.Response = requests.get(
            f"{protocol}{platform_domain}/api/v1/s3-reports/{guid}",
            headers=headers,
        )
        if s3_report_response.status_code >= 400:
            raise Http404
        s3_report: Dict[str, str] = s3_report_response.json()
        s3_rw = S3ReadWriteReport()
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=guid)
        if raw_html == NO_REPORT_HTML and s3_report.get("html"):
            raw_html = s3_report["html"]
        report = Report.objects.get(case_id=s3_report.get("case_id"))

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
