from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.reports.models import Report


class ViewReport(TemplateView):
    """
    View of list of overdue tasks for user
    """

    def get(self, request, guid, *args, **kwargs):
        s3report = get_object_or_404(S3Report, guid=guid)
        s3_rw = S3ReadWriteReport()
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=guid)
        report = Report.objects.get(case=s3report.case)
        context = {
            "html_report": raw_html,
            "report": report
        }
        return render(request, "reports/acccessibility_report_container.html", context=context)
