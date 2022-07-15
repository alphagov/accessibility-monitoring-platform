"""Views for report viewer"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from accessibility_monitoring_platform.apps.common.views import PlatformTemplateView
from accessibility_monitoring_platform.apps.reports.models import Report
from accessibility_monitoring_platform.apps.s3_read_write.utils import (
    S3ReadWriteReport,
    NO_REPORT_HTML,
)
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "viewer/accessibility_statement.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "viewer/privacy_notice.html"


class ViewReport(TemplateView):
    """
    View of report on S3
    """

    def get(self, request, guid, *args, **kwargs):  # pylint: disable=unused-argument
        s3_report = get_object_or_404(S3Report, guid=guid)
        s3_rw = S3ReadWriteReport()
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=guid)
        if raw_html == NO_REPORT_HTML and s3_report.html:
            raw_html = s3_report.html
        report = Report.objects.get(case=s3_report.case)
        context = {"html_report": raw_html, "report": report, "s3_report": s3_report}
        return render(
            request, "reports/accessibility_report_base.html", context=context
        )
