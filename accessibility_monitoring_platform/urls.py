"""
Project URL Configuration
"""

import requests
from django.conf.urls import include
from django.contrib import admin
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import path
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls


def get_security_txt(request):  # pylint: disable=unused-argument
    url = "https://vdp.cabinetoffice.gov.uk/.well-known/security.txt"
    response = requests.get(url, stream=True)
    return StreamingHttpResponse(
        response.raw,
        content_type=response.headers.get("content-type"),
        status=response.status_code,
        reason=response.reason,
    )


def robots_txt(request):  # pylint: disable=unused-argument
    return HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")


urlpatterns = [
    path("__reload__/", include("django_browser_reload.urls")),
    path("", include(tf_urls)),
    path("", include("accessibility_monitoring_platform.apps.dashboard.urls")),
    path("accounts/login/", RedirectView.as_view(url="/")),
    path("audits/", include("accessibility_monitoring_platform.apps.audits.urls")),
    path("comments/", include("accessibility_monitoring_platform.apps.comments.urls")),
    path("common/", include("accessibility_monitoring_platform.apps.common.urls")),
    path("reports/", include("accessibility_monitoring_platform.apps.reports.urls")),
    path("cases/", include("accessibility_monitoring_platform.apps.cases.urls")),
    path("detailed/", include("accessibility_monitoring_platform.apps.detailed.urls")),
    path("exports/", include("accessibility_monitoring_platform.apps.exports.urls")),
    path("user/", include("accessibility_monitoring_platform.apps.users.urls")),
    path(
        "notifications/",
        include("accessibility_monitoring_platform.apps.notifications.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path(r"platform-admin/", admin.site.urls),
    path(r"favicon.ico", RedirectView.as_view(url="/static/assets/images/favicon.ico")),
    path("security.txt", get_security_txt),
    path("robots.txt", robots_txt),
    path(".well-known/security.txt", get_security_txt),
]
