"""
Compare published report text with report preview.

Write out reports which differ for detailed comparison.

Differences found are in WCAG boilerplate text which has changed.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.template import Template, loader

from ...models import Report
from ...utils import build_report_context


class Command(BaseCommand):
    """Django command to reset the database"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset database for integration tests"""

        with open("report_old.html", "w") as old_reports_file:
            with open("report_new.html", "w") as new_reports_file:
                for report_version in [
                    "v1_0_0__20220406",
                    "v1_1_0__20230421",
                    "v1_2_0__20230523",
                    "v1_3_0__20240710",
                    "v1_4_0__20241005",
                    "v1_5_0__20241125",
                    "v1_6_0__20250122",
                    "v1_7_0__20250416",
                    "v1_8_0__20250424",
                ]:
                    reports = Report.objects.filter(report_version=report_version)
                    if reports.count() == 0:
                        print(f"No reports found for {report_version}")
                    else:
                        for report in [reports.first(), reports.last()]:
                            template: Template = loader.get_template(
                                report.template_path
                            )
                            report_context: dict[str, Any] = build_report_context(
                                report=report
                            )
                            html_report: str = template.render(report_context)
                            if report.latest_s3_report is not None:
                                if report.latest_s3_report.html != html_report:
                                    print(f"{report} mismatch")
                                    old_reports_file.write(
                                        f"<h1>{report} mismatch</h1>"
                                    )
                                    old_reports_file.write(report.latest_s3_report.html)
                                    new_reports_file.write(
                                        f"<h1>{report} mismatch</h1>"
                                    )
                                    new_reports_file.write(html_report)
