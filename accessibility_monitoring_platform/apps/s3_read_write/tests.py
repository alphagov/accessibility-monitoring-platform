"""
Testing s3 read write
"""
from datetime import datetime

import boto3
import pytest
from django.contrib.auth.models import User
from moto import mock_s3

from ...settings.base import DATABASES, S3_MOCK_ENDPOINT
from ..cases.models import Case
from .models import S3Report
from .utils import NO_REPORT_HTML, S3ReadWriteReport


@pytest.mark.django_db
@mock_s3
def test_upload_string_to_s3():
    s3rw: S3ReadWriteReport = S3ReadWriteReport()
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    case_id: int = case.id
    raw_html: str = f"""
        <div>
            <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
            <p class="govuk-body-l">Case id {case_id}.</p>
            <p class="govuk-body-l">datetime: {datetime.now()}.</p>
        </div>
    """
    s3rw.upload_string_to_s3_as_html(
        html_content=raw_html, case=case, user=user, report_version="v1_20220406"
    )

    s3report: S3Report = S3Report.objects.get(case=case)

    s3_resource = boto3.resource(
        service_name="s3",
        region_name=DATABASES["aws-s3-bucket"]["aws_region"],
        aws_access_key_id=DATABASES["aws-s3-bucket"]["aws_access_key_id"],
        aws_secret_access_key=DATABASES["aws-s3-bucket"]["aws_secret_access_key"],
        endpoint_url=S3_MOCK_ENDPOINT,
    )
    obj = s3_resource.Object("bucketname", s3report.s3_directory)
    assert obj.get()["Body"].read().decode("utf-8") == raw_html


@pytest.mark.django_db
@mock_s3
def test_retrieve_raw_html():
    s3rw: S3ReadWriteReport = S3ReadWriteReport()
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    case_id: int = case.id
    raw_html: str = f"""
        <div>
            <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
            <p class="govuk-body-l">Case id {case_id}.</p>
            <p class="govuk-body-l">datetime: {datetime.now()}.</p>
        </div>
    """
    s3rw.upload_string_to_s3_as_html(
        html_content=raw_html, case=case, user=user, report_version="v1_20220406"
    )

    guid: str = S3Report.objects.get(case=case).guid
    res: str = s3rw.retrieve_raw_html_from_s3_by_guid(guid)

    assert res == raw_html


@pytest.mark.django_db
@mock_s3
def test_url_builder():
    s3rw: S3ReadWriteReport = S3ReadWriteReport()
    guid: str = "04f1a855-94b9-4ff5-a31f-f8982bc0736e"
    res = (
        f"caseid_1/org_orgname__reportid_1__reportversion_v1_20220406__guid_{guid}.html"
    )
    assert res == s3rw.url_builder(
        case_id=1,
        organisation_name="orgname",
        version=1,
        report_version="v1_20220406",
        guid=guid,
    )


@pytest.mark.django_db
@mock_s3
def test_s3_no_such_key():
    s3rw: S3ReadWriteReport = S3ReadWriteReport()
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    case_id: int = case.id
    raw_html: str = f"""
        <div>
            <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
            <p class="govuk-body-l">Case id {case_id}.</p>
            <p class="govuk-body-l">datetime: {datetime.now()}.</p>
        </div>
    """
    s3rw.upload_string_to_s3_as_html(
        html_content=raw_html, case=case, user=user, report_version="v1_20220406"
    )

    s3_report: S3Report = S3Report.objects.get(case=case)
    s3_report.s3_directory = "not-a-valid-dir"
    s3_report.save()
    guid: str = s3_report.guid
    res: str = s3rw.retrieve_raw_html_from_s3_by_guid(guid)

    assert res == NO_REPORT_HTML
