"""
S3 readwrite utilities
"""

import re
import uuid

from django.contrib.auth.models import User

from ..cases.models import BaseCase
from ..common.s3_utils import S3Wrapper
from .models import S3Report

NO_REPORT_HTML: str = "<p>Does not exist</p>"


class S3ReadWriteReport(S3Wrapper):
    """S3 report readwrite utilities"""

    def upload_string_to_s3_as_html(
        self,
        html_content: str,
        base_case: BaseCase,
        user: User,
        report_version: str,
    ) -> str:
        version = 1
        if S3Report.objects.filter(base_case=base_case).exists():
            version = len(S3Report.objects.filter(base_case=base_case)) + 1

        guid: str = str(uuid.uuid4())

        s3_url_for_report: str = self.url_builder(
            organisation_name=base_case.organisation_name,
            case_id=base_case.id,
            version=version,
            report_version=report_version,
            guid=guid,
        )

        self.s3_client.put_object(
            Body=html_content,
            Bucket=self.bucket,
            Key=s3_url_for_report,
        )

        s3report = S3Report(
            base_case=base_case,
            created_by=user,
            s3_directory=s3_url_for_report,
            version=version,
            guid=guid,
            html=html_content,
            latest_published=True,
        )

        s3report.save()
        return s3report.guid

    def retrieve_raw_html_from_s3_by_guid(self, guid: str) -> str:
        if S3Report.objects.filter(guid=guid).exists():
            s3file = S3Report.objects.get(guid=guid)
            try:
                obj = self.s3_resource.Object(self.bucket, s3file.s3_directory)
                return obj.get()["Body"].read().decode("utf-8")
            except self.s3_client.exceptions.NoSuchKey:
                return NO_REPORT_HTML
        return NO_REPORT_HTML

    def url_builder(
        self,
        organisation_name: str,
        case_id: int,
        version: int,
        report_version: str,
        guid: str,
    ) -> str:
        clean_orgnisation_name: str = re.sub(
            "[^a-zA-Z0-9]", "_", organisation_name
        ).lower()
        return f"""caseid_{case_id}/org_{clean_orgnisation_name}__reportid_{version}__reportversion_{report_version}__guid_{guid}.html"""
