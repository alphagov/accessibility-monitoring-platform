"""
Paths for the axe_data app
"""

from django.urls import path
from accessibility_monitoring_platform.apps.axe_data.views import home


app_name = "axe_data"
urlpatterns = [
    path("", home, name="home"),
]
