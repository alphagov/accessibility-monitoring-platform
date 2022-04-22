"""
URLS for public reports
"""

from django.urls import path
from .views import ViewReport


app_name = "viewer"
urlpatterns = [
    path("<str:guid>", ViewReport.as_view(), name="viewreport"),
]
