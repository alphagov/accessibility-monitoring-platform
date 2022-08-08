"""
Project URL Configuration
"""
import requests

from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.http import StreamingHttpResponse
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls


def get_security_txt(request):
    url = "https://vdp.cabinetoffice.gov.uk/.well-known/security.txt"
    response = requests.get(url, stream=True)
    return StreamingHttpResponse(
        response.raw,
        content_type=response.headers.get("content-type"),
        status=response.status_code,
        reason=response.reason,
    )


urlpatterns = [
    path("", include(tf_urls)),
    path("", include("accessibility_monitoring_platform.apps.dashboard.urls")),
    path("accounts/login/", RedirectView.as_view(url="/")),
    path("audits/", include("accessibility_monitoring_platform.apps.audits.urls")),
    path("common/", include("accessibility_monitoring_platform.apps.common.urls")),
    path("reports/", include("accessibility_monitoring_platform.apps.reports.urls")),
    path(
        "reminders/", include("accessibility_monitoring_platform.apps.reminders.urls")
    ),
    path("overdue/", include("accessibility_monitoring_platform.apps.overdue.urls")),
    path("cases/", include("accessibility_monitoring_platform.apps.cases.urls")),
    path("user/", include("accessibility_monitoring_platform.apps.users.urls")),
    path("comments/", include("accessibility_monitoring_platform.apps.comments.urls")),
    path(
        "notifications/",
        include("accessibility_monitoring_platform.apps.notifications.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path(r"admin/", admin.site.urls),
    path(r"favicon.ico", RedirectView.as_view(url="/static/images/favicon.ico")),
    path("security.txt", get_security_txt),
    path(".well-known/security.txt", get_security_txt),
]
