from django.shortcuts import render
from django.views.generic import TemplateView
from .utils import S3ReadWriteReport
from ..cases.models import Case
from datetime import datetime


class ViewReport(TemplateView):
    """
    View of list of overdue tasks for user
    """

    def get(self, request, guid, *args, **kwargs):
        s3_rw = S3ReadWriteReport()
        print(">>>> get report")
        raw_html = s3_rw.retrieve_raw_html_from_s3_by_guid(guid=guid)
        return render(
            request,
            "s3_read_write/base.html",
            {"content": raw_html}
        )


class CreateReport(TemplateView):
    """
    View of list of overdue tasks for user
    """

    def get(self, request, id, *args, **kwargs):
        case = Case.objects.get(pk=id)
        raw_html = f"""
            <div>
                <h1 class="govuk-body-l">org: {case.organisation_name}</h1>
                <p class="govuk-body-l">Case id {case.id}.</p>
                <p class="govuk-body-l">datetime: {datetime.now()}.</p>
            </div>
        """
        s3_rw = S3ReadWriteReport()
        guid = s3_rw.upload_string_to_s3_as_html(
            html_content=raw_html,
            case=case,
            user=request.user
        )
        return render(request, "s3_read_write/saved_successfully.html", {"guid": guid})
