'''
Paths for the query_local_website_registry app
'''

from django.urls import path
from accessibility_monitoring_platform.apps.query_local_website_registry.views import read


app_name = 'query_local_website_registry'
urlpatterns = [
    path('', read, name='home'),
]
