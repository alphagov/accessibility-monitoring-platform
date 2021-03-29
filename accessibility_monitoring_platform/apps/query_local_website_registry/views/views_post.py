"""
Views - query_local_website_registry post
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    QueryDict
)
from django.shortcuts import render
from ..forms import SearchForm
from typing import (
    Any,
    List,
)


@login_required
def read_post(request: HttpRequest) -> Any:
    """ Creates the url parameter for filtering the database

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        Any: Django HttpResponse
    """

    search_form_fields: List[str] = list(SearchForm.declared_fields.keys())
    prefill_form: dict = {field: request.GET.get(field) for field in search_form_fields}
    form = SearchForm(request.POST, initial=prefill_form)
    if form.is_valid():
        q: QueryDict = QueryDict(mutable=True)
        for field in search_form_fields:
            if (
                form.cleaned_data[field] is not None
                and form.cleaned_data[field] != ''
            ):
                q[field] = form.cleaned_data[field]

        query_string: str = q.urlencode()
        return redirect(f"{reverse('query_local_website_registry:home')}?{query_string}")

    return render(request, 'query_local_website_registry/home.html', {'form': form})
