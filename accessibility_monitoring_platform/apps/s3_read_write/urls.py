"""
URLS for S3 read write
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import ViewReport, CreateReport


app_name = "s3_read_write"
urlpatterns = [
    path(
        "save/<int:id>",
        login_required(CreateReport.as_view()),
        name="save",
    ),
    path(
        "<str:guid>",
        login_required(ViewReport.as_view()),
        name="viewreport",
    ),
]
