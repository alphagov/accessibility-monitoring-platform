"""
URLS for S3 read write
"""

from django.urls import path
from .views import download_invoice


app_name = "s3_read_write"
urlpatterns = [
    path("<int:pk>/", download_invoice, name="download_invoice"),
]
