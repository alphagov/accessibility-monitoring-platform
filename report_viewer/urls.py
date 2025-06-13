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
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import path
from django.views.defaults import page_not_found
from django.views.generic.base import RedirectView

ROOT_REDIRECT_DESTINATION: str = "https://www.gov.uk/guidance/public-sector-website-and-mobile-application-accessibility-monitoring/"


def custom_page_not_found(request):
    return page_not_found(request, None)


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


app_name = "apps"
urlpatterns = [
    path("__reload__/", include("django_browser_reload.urls")),
    path("", RedirectView.as_view(url=ROOT_REDIRECT_DESTINATION)),
    path("reports/", include("report_viewer.apps.viewer.urls")),
    path("404/", custom_page_not_found),
    path("security.txt", get_security_txt),
    path("robots.txt", robots_txt),
    path(".well-known/security.txt", get_security_txt),
]
