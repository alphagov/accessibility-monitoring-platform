"""URLS for tech team pages"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import (
    EqualityBodyCsvMetadataView,
    PlatformCheckingView,
    ReferenceImplementaionView,
    SitemapView,
)

app_name = "tech"
urlpatterns = [
    path(
        "",
        login_required(ReferenceImplementaionView.as_view()),
        name="reference-implementation",
    ),
    path(
        "equality-body-csv-metadata/",
        login_required(EqualityBodyCsvMetadataView.as_view()),
        name="equality-body-csv-metadata",
    ),
    path(
        "platform-checking/",
        login_required(PlatformCheckingView.as_view()),
        name="platform-checking",
    ),
    path(
        "sitemap/",
        login_required(SitemapView.as_view()),
        name="sitemap",
    ),
]
