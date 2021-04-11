"""
Views of Axe test results
"""
import urllib
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, Page
from django.shortcuts import render
from .forms import AxeDataSearchForm, DEFAULT_START_DATE, DEFAULT_END_DATE
from .models import TestresultAxeHeader
from typing import Union

PAGE_SIZE = 25


@login_required
def home(request):
    """ Filter of Axe test results """
    context = {}
    parameters = ""
    domain_name = None
    start_date = DEFAULT_START_DATE
    end_date = DEFAULT_END_DATE
    filter_params: dict = {}

    def get_filters_from_form():
        domain_name = form.cleaned_data.get("domain_name")
        start_date = form.start_date
        end_date = form.end_date
        return domain_name, start_date, end_date

    if request.POST:
        form = AxeDataSearchForm(request.POST)
        if form.is_valid():
            populated_fields = {
                key: value
                for (key, value) in form.cleaned_data.items()
                if value is not None and value != ""
            }
            parameters = urllib.parse.urlencode(populated_fields)
            domain_name, start_date, end_date = get_filters_from_form()
    else:
        get_without_page = {
            key: value for (key, value) in request.GET.items() if key != "page"
        }
        form = AxeDataSearchForm(get_without_page)
        if form.is_valid():
            parameters = urllib.parse.urlencode(get_without_page)
            domain_name, start_date, end_date = get_filters_from_form()

    context["form"] = form
    context["parameters"] = parameters

    if domain_name or start_date != DEFAULT_START_DATE or end_date != DEFAULT_END_DATE:
        if domain_name is not None:
            filter_params["domain_name__icontains"] = domain_name
        filter_params["test_timestamp__gte"] = start_date
        filter_params["test_timestamp__lte"] = end_date
        testresult_axe_headers = TestresultAxeHeader.objects.using("axe_data").filter(
            **filter_params
        )
        context["number_of_results"] = len(testresult_axe_headers)
        paginator: Paginator = Paginator(testresult_axe_headers, PAGE_SIZE)
        page_number: Union[str, None] = request.GET.get("page")
        context["page_obj"]: Page = paginator.get_page(page_number)

    return render(request, "axe_data/home.html", context)
