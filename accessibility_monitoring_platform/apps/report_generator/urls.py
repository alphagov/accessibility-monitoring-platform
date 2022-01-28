"""
URLS for report generator
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import ReportGeneratorBase


app_name = "reportgenerator"
urlpatterns = [
    path(
        "",
        login_required(ReportGeneratorBase.as_view()),
        name="reportgenerator",
    ),
]
