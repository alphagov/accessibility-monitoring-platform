"""
Views - query_local_website_registry
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from ..forms import SearchForm
from .views_post import read_post
from .views_get import read_get
from typing import Any


@login_required
def read(request: HttpRequest) -> Any:
    """
    Routes post and get requests

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        Union[HttpResponse, None]: Django HttpResponse
    """
    if request.method == 'POST':
        return read_post(request)
    elif request.method == 'GET':
        return read_get(request)
    return render(request, 'query_local_website_registry/home.html', {'form': SearchForm()})
