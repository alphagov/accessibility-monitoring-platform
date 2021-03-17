from django.shortcuts import (
    render,
    redirect
)
from django.http import QueryDict, HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    NutsConversion,
    WebsiteRegister,
)
from .forms import SearchForm
import datetime
from typing import List
import csv
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='read')
class Home():
    def __init__(self) -> None:
        self.search_form_fields = SearchForm.declared_fields.keys()

    def read(self, request):
        if request.method == 'POST':
            return self.read_post(request)
        elif request.method == 'GET':
            return self.read_get(request)
        return render(request, 'query_local_website_registry/home.html', {'form': SearchForm()})

    def read_post(self, request):
        form = SearchForm(request.POST)
        if form.is_valid():
            q = QueryDict(mutable=True)
            for field in self.search_form_fields:
                if (
                    form.cleaned_data[field] is not None
                    and form.cleaned_data[field] != ''
                ):
                    q[field] = form.cleaned_data[field]

            query_string = q.urlencode()
            return redirect(f"{reverse('query_local_website_registry:home')}?{query_string}")

    def read_get(self, request):
        # Parse query parametres
        prefill_form = {field: request.GET.get(field) for field in self.search_form_fields}

        # If all string parameter fields are empty, returns an empty page
        if all(value is None for value in prefill_form.values()):
            return render(request, 'query_local_website_registry/home.html', {'form': SearchForm()})

        website_register = WebsiteRegister.objects.using('accessibility_domain_db').all()

        if prefill_form['location']:
            unique_nuts118 = self.get_list_of_nuts118(prefill_form['location'])
            website_register = website_register.filter(nuts3__in=unique_nuts118)

        # Convert None to empty strings
        queries = {k: (prefill_form[k] if prefill_form[k] else '') for k in prefill_form.keys()}

        start_date = self.date_fixer(
            year=prefill_form['start_date_year'],
            month=prefill_form['start_date_month'],
            day=prefill_form['start_date_day'],
            max_date=False
        )

        end_date = self.date_fixer(
            year=prefill_form['end_date_year'],
            month=prefill_form['end_date_month'],
            day=prefill_form['end_date_day'],
            max_date=True
        )

        website_register = website_register.filter(
            service__icontains=queries['service'],
            sector__sector_name__icontains=queries['sector_name'],
            last_updated__gte=start_date,
            last_updated__lte=end_date,
        ).all()

        if (
            request.GET.get('format')
            and request.GET.get('format') == 'csv'
        ):
            return self.download_as_csv(website_register, request.GET.urlencode())

        paginator = Paginator(website_register, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        get_copy = request.GET.copy()
        parameters = get_copy.pop('page', True) and get_copy.urlencode()

        form = SearchForm(prefill_form)

        table_headers = [
            'Service',
            'Sector',
            'Last Updated',
            'URL',
            'Domain',
            'HTML Title'
        ]

        context = {
            'page_obj': page_obj,
            'form': form,
            'parameters': parameters,
            'table_headers': table_headers,
            'number_of_results': len(website_register),
        }

        return render(request, 'query_local_website_registry/home.html', context)

    def get_list_of_nuts118(self, location: str) -> List[str]:
        lad18 = NutsConversion.objects.using('accessibility_domain_db').filter(lad18nm__icontains=location)
        lau118 = NutsConversion.objects.using('accessibility_domain_db').filter(lau118nm__icontains=location)
        nuts318 = NutsConversion.objects.using('accessibility_domain_db').filter(nuts318nm__icontains=location)
        nuts218 = NutsConversion.objects.using('accessibility_domain_db').filter(nuts218nm__icontains=location)
        nuts_code = lad18 | lau118 | nuts318 | nuts218

        list_of_nuts118 = [x['nuts318cd'] for x in nuts_code.values()]
        unique_nuts118 = set(list_of_nuts118)
        return unique_nuts118

    def date_fixer(self, year: str, month: str, day: str, max_date: bool) -> datetime:
        try:
            return datetime.datetime(
                year=int(year),
                month=int(month),
                day=int(day),
            )
        except (ValueError, TypeError):
            if max_date:
                return datetime.datetime(year=2100, month=1, day=1)
            return datetime.datetime(year=1970, month=1, day=1)

    def download_as_csv(self, query_set, string_query):
        response = HttpResponse(content_type='text/csv')
        filename = f'website_register_?{string_query}.csv'
        response['Content-Disposition'] = f'attachment; filename={filename}'

        writer = csv.writer(response)
        writer.writerow([
            'service',
            'sector',
            'last_updated',
            'url',
            'domain',
            'html_title',
            'nuts3',
        ])

        output = []
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
