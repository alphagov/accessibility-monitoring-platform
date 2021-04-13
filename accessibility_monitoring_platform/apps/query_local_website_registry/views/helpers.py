"""
Views - query_local_website_registry helpers
"""

from django.db.models import QuerySet
from django.http import HttpResponse
from ..models import NutsConversion
import datetime
import csv
import pytz
from typing import (
    Any,
    List,
)


def get_list_of_nuts118(location: str) -> Any:
    """ Filters town or city and returns a list of nuts118 area codes for filtering websites

    Args:
        location (str): The string to search

    Returns:
        Any: A list of nuts118 codes
    """
    lad18: QuerySet = NutsConversion.objects.using('pubsecweb_db') \
        .filter(lad18nm__icontains=location)

    lau118: QuerySet = NutsConversion.objects.using('pubsecweb_db') \
        .filter(lau118nm__icontains=location)

    nuts318: QuerySet = NutsConversion.objects.using('pubsecweb_db'). \
        filter(nuts318nm__icontains=location)

    nuts218: QuerySet = NutsConversion.objects.using('pubsecweb_db'). \
        filter(nuts218nm__icontains=location)

    nuts_code: QuerySet = lad18 | lau118 | nuts318 | nuts218

    list_of_nuts118: List[Any] = [x['nuts318cd'] for x in nuts_code.values()]
    unique_nuts118: List[str] = list(set(list_of_nuts118))
    return unique_nuts118


def date_fixer(year: str, month: str, day: str, max_date: bool) -> datetime.datetime:
    """ Converts the individual form fields and returns a datetime.datetime object

    Args:
        year (str): year as string
        month (str): month as string
        day (str): day as string
        max_date (bool): Whether it defaults to returning the minimal date or the maximum date

    Returns:
        datetime.datetime: A datetime object
    """

    try:
        return datetime.datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            tzinfo=pytz.UTC
        )
    except (ValueError, TypeError):
        if max_date:
            return datetime.datetime(
                year=2100,
                month=1,
                day=1,
                tzinfo=pytz.UTC
            )
        return datetime.datetime(
            year=1900,
            month=1,
            day=1,
            tzinfo=pytz.UTC
        )


def download_as_csv(query_set: QuerySet, string_query: str) -> HttpResponse:
    response: Any = HttpResponse(content_type='text/csv')
    filename: str = f'website_register_?{string_query}.csv'
    response['Content-Disposition'] = f'attachment; filename={filename}'

    writer: Any = csv.writer(response)
    writer.writerow([
        'service',
        'sector',
        'last_updated',
        'url',
        'domain',
        'html_title',
        'nuts3',
    ])

    output: List[List[str]] = []
    for website in query_set:
        output.append([
            website.service,
            website.sector.sector_name,
            website.last_updated,
            website.url,
            website.original_domain,
            website.htmlhead_title,
            website.nuts3,
        ])

    writer.writerows(output)

    return response
