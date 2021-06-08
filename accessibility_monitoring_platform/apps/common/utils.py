""" Common utility functions """
import re
import csv
from typing import (
    Any,
    List,
)

from django.db.models import QuerySet
from django.http import HttpResponse


def download_as_csv(
    queryset: QuerySet, field_names: List[str], filename: str = "download.csv"
) -> HttpResponse:
    """ Given a queryset and a list of field names, download the data in csv format """
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(field_names)

    output: List[List[str]] = []
    for item in queryset:
        output.append([getattr(item, field_name) for field_name in field_names])

    writer.writerows(output)

    return response


def extract_domain_from_url(url):
    domain_match = re.search("https?://([A-Za-z_0-9.-]+).*", url)
    return domain_match.group(1) if domain_match else ""
