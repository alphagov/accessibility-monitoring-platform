"""report_viewer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import requests

from django.conf.urls import include
from django.http import JsonResponse, StreamingHttpResponse
from django.urls import path
from django.views.defaults import page_not_found


def custom_page_not_found(request):
    return page_not_found(request, None)


def healthcheck(request):  # pylint: disable=unused-argument
    return JsonResponse({"healthcheck": "ok"})


def get_security_txt(request):
    url = "https://vdp.cabinetoffice.gov.uk/.well-known/security.txt"
    response = requests.get(url, stream=True)
    return StreamingHttpResponse(
        response.raw,
        content_type=response.headers.get("content-type"),
        status=response.status_code,
        reason=response.reason,
    )


app_name = "apps"
urlpatterns = [
    path("reports/", include("report_viewer.apps.viewer.urls")),
    path("404/", custom_page_not_found),
    path("healthcheck/", healthcheck),
    path("security.txt", get_security_txt),
    path(".well-known/security.txt", get_security_txt),
]
