'''
Paths for the query_local_website_registry app
'''

from django.urls import path
from accessibility_monitoring_platform.apps.axe_data.views import home


app_name = 'axe_data'
urlpatterns = [
    path('', home, name='home'),
]
