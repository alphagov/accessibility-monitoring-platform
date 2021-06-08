""" Common utility functions """
from django.db.models import QuerySet
from django.http import HttpResponse
import csv
from typing import (
    Any,
    List,
)


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
