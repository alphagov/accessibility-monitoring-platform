"""
URLs for api
"""
from rest_framework import routers

from django.urls import path, include

from .views import S3ReportViewSet

router = routers.SimpleRouter()
router.register("s3-reports", S3ReportViewSet)

urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", include(router.urls)),
]
