"""notesapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url


urlpatterns = [
    url('', include('accessibility_monitoring_platform.apps.dashboard.urls')),
    url(
        'query-domains/',
        include(
            (
                'accessibility_monitoring_platform'
                '.apps'
                '.query_local_website_registry'
                '.urls'
            )
        )
    ),
    url('', include('accessibility_monitoring_platform.apps.users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
]
