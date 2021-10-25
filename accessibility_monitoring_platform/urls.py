"""
Project URL Configuration
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.conf.urls import include
from django.views.generic import RedirectView
from accessibility_monitoring_platform.apps.common.views import ContactAdminView, IssueReportView

urlpatterns = [
    path("", include("accessibility_monitoring_platform.apps.dashboard.urls")),
    path("cases/", include("accessibility_monitoring_platform.apps.cases.urls")),
    path("checks/", include("accessibility_monitoring_platform.apps.checks.urls")),
    path("websites/", include("accessibility_monitoring_platform.apps.websites.urls")),
    path("user/", include("accessibility_monitoring_platform.apps.users.urls")),
    # path("comments/", include("accessibility_monitoring_platform.apps.comments.urls")),
    # path("notifications/", include("accessibility_monitoring_platform.apps.notifications.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("contact/", login_required(ContactAdminView.as_view()), name="contact-admin"),
    path("report-issue/", login_required(IssueReportView.as_view()), name="issue-report"),
    path(r"admin/", admin.site.urls),
    path(r"favicon.ico", RedirectView.as_view(url="/static/images/favicon.ico")),
]
