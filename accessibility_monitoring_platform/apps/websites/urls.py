"""
Paths for the websites app
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import export_websites, WebsiteListView


app_name = "websites"
urlpatterns = [
    path("", login_required(WebsiteListView.as_view()), name="website-list"),
    path("export-as-csv/", login_required(export_websites), name="website-export-list"),
]
