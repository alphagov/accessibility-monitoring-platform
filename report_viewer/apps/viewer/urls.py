"""
URLS for public reports
"""

from django.urls import path
from .views import (
    AccessibilityStatementTemplateView,
    MoreInformationTemplateView,
    PrivacyNoticeTemplateView,
    ViewReport,
)


app_name = "viewer"
urlpatterns = [
    path(
        "accessibility-statement",
        AccessibilityStatementTemplateView.as_view(),
        name="accessibility-statement",
    ),
    path(
        "privacy-notice",
        PrivacyNoticeTemplateView.as_view(),
        name="privacy-notice",
    ),
    path(
        "more-information",
        MoreInformationTemplateView.as_view(),
        name="more-information",
    ),
    path("<str:guid>", ViewReport.as_view(), name="viewreport"),
]
