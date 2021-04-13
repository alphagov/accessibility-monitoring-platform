"""
Views - query_local_website_registry get
"""
from django.shortcuts import render
from django.core.paginator import Paginator, Page
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import (
    HttpRequest,
    QueryDict
)
import datetime
from typing import (
    Any,
    List,
    Literal,
    Union,
    TypedDict
)
from ..models import WebsiteRegister
from ..forms import SearchForm
from .helpers import (
    date_fixer,
    download_as_csv,
    get_list_of_nuts118,
)


class QueryLocalWebsiteGetContext(TypedDict):
    page_obj: Page
    form: SearchForm
    parameters: Union[str, QueryDict, Literal[False]]
    table_headers: List[str]
    number_of_results: int


@login_required
def read_get(request: HttpRequest):
    """[summary]

    Args:
        request (HttpRequest): [description]

    Returns:
        [type]: [description]
    """

    search_form_fields: List[str] = list(SearchForm.declared_fields.keys())

    # Parse query parametres
    prefill_form: dict = {field: request.GET.get(field) for field in search_form_fields}

    # If all string parameter fields are empty, returns an empty page
    if all(value is None for value in prefill_form.values()):
        return render(request, 'query_local_website_registry/home.html', {'form': SearchForm()})

    website_register: QuerySet = WebsiteRegister.objects.using('pubsecweb_db').order_by('website_id').all()

    if prefill_form['location']:
        unique_nuts118: Any = get_list_of_nuts118(str(prefill_form['location']))
        website_register: QuerySet = website_register.filter(nuts3__in=unique_nuts118)

    # Convert None to empty strings
    queries: Any = {k: (prefill_form[k] if prefill_form[k] else '') for k in prefill_form.keys()}

    start_date: datetime.datetime = date_fixer(
        year=str(prefill_form['start_date_year']),
        month=str(prefill_form['start_date_month']),
        day=str(prefill_form['start_date_day']),
        max_date=False
    )

    end_date: datetime.datetime = date_fixer(
        year=str(prefill_form['end_date_year']),
        month=str(prefill_form['end_date_month']),
        day=str(prefill_form['end_date_day']),
        max_date=True
    )

    website_register: QuerySet = website_register.filter(
        service__icontains=queries['service'],
        sector__sector_name__icontains=queries['sector_name'],
        last_updated__gte=start_date,
        last_updated__lte=end_date,
    ).all()

    if (
        request.GET.get('format')
        and request.GET.get('format') == 'csv'
    ):
        return download_as_csv(website_register, request.GET.urlencode())

    paginator: Paginator = Paginator(website_register, 25)
    page_number: Union[str, None] = request.GET.get('page')
    page_obj: Page = paginator.get_page(page_number)

    get_copy: QueryDict = request.GET.copy()
    parameters: Union[str, QueryDict, Literal[False]] = get_copy.pop('page', True) and get_copy.urlencode()

    form: SearchForm = SearchForm(prefill_form)

    table_headers: List[str] = [
        'Service',
        'Sector',
        'Last Updated',
        'URL',
        'Domain',
        'HTML Title'
    ]

    context: QueryLocalWebsiteGetContext = {
        'page_obj': page_obj,
        'form': form,
        'parameters': parameters,
        'table_headers': table_headers,
        'number_of_results': len(website_register),
    }

    return render(request, 'query_local_website_registry/home.html', context)
