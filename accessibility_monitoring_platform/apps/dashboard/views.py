"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """
    View for the main dashboard

    Args:
        request (HttpRequest): Django request

    Returns:
        HttpResponse: Django http response
    """
    return render(request, "dashboard/home.html")
