from django.conf.urls import include, url
# from accessibility_monitoring_platform.apps.query_local_website_registry.views import home
from accessibility_monitoring_platform.apps.query_local_website_registry.views import Home
from django.urls import path


app_name = 'query_local_website_registry'
urlpatterns = [
    path('', Home().read, name='home'),
]
