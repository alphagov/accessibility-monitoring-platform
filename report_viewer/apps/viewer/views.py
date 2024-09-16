"""Views for report viewer"""

import logging
from typing import Any, Dict

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from accessibility_monitoring_platform.apps.common.platform_template_view import (
    PlatformTemplateView,
)
from accessibility_monitoring_platform.apps.reports.models import Report
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.s3_read_write.utils import (
    NO_REPORT_HTML,
    S3ReadWriteReport,
)

from .utils import show_warning

FORM_SUBMITTED_SUCCESSFULLY: str = "Form submitted successfully"

logger = logging.getLogger(__name__)


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "viewer/accessibility_statement.html"


class MoreInformationTemplateView(PlatformTemplateView):
    template_name: str = "viewer/more_information.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "viewer/privacy_notice.html"


class ViewReport(TemplateView):
    """
    View of report on S3
    """

    template_name: str = "reports_common/accessibility_report_base.html"

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

        context.update(
            {
                "html_report": raw_html,
                "report": report,
                "s3_report": s3_report,
                "guid": self.kwargs["guid"],
                "report_viewer": True,
                "show_warning": show_warning(),
            }
        )
        return context

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path
