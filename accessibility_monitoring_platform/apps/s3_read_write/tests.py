import pytest
import boto3
from moto import mock_s3
from datetime import datetime
from django.contrib.auth.models import User
from ..cases.models import Case
from .utils import S3ReadWriteReport
from .models import S3Report


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
    raw_html: str = f"""
        <div>
            <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
            <p class="govuk-body-l">Case id {case.id}.</p>
            <p class="govuk-body-l">datetime: {datetime.now()}.</p>
        </div>
    """
    s3rw.upload_string_to_s3_as_html(
        html_content=raw_html,
        case=case,
        user=user
    )

    s3_resource = boto3.resource(service_name="s3")
    obj = s3_resource.Object("bucketname", "caseid_1/org_org name__reportid_1.html")  # type: ignore

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
    raw_html: str = f"""
        <div>
            <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
            <p class="govuk-body-l">Case id {case.id}.</p>
            <p class="govuk-body-l">datetime: {datetime.now()}.</p>
        </div>
    """
    s3rw.upload_string_to_s3_as_html(
        html_content=raw_html,
        case=case,
        user=user
    )

    guid: str = S3Report.objects.get(case=case).guid
    res: str = s3rw.retrieve_raw_html_from_s3_by_guid(guid)

    assert res == raw_html
