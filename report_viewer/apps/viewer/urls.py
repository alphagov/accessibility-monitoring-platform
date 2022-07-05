"""
URLS for public reports
"""

from django.urls import path
from .views import AccessibilityStatementTemplateView, ViewReport


app_name = "viewer"
urlpatterns = [
    path(
        "accessibility-statement",
        AccessibilityStatementTemplateView.as_view(),
        name="accessibility-statement",
    ),
    path("<str:guid>", ViewReport.as_view(), name="viewreport"),
]
