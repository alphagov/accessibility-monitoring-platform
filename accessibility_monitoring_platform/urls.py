"""
Project URL Configuration
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.views.generic import RedirectView, TemplateView
from two_factor.urls import urlpatterns as tf_urls


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
    path("security.txt", TemplateView.as_view(template_name="security.txt", content_type="text/plain")),
    path(".well-known/security.txt", TemplateView.as_view(template_name="security.txt", content_type="text/plain")),
]
