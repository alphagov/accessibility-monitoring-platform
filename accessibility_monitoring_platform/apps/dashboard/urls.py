from django.conf.urls import include, url
from accessibility_monitoring_platform.apps.dashboard.views import home
from django.urls import path

app_name = 'dashboard'
urlpatterns = [
    path('', home, name='home'),
]
