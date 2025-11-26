"""URLS for tech team pages"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import PlatformCheckingView, ReferenceImplementaionView

app_name = "tech"
urlpatterns = [
    path(
        "",
        login_required(ReferenceImplementaionView.as_view()),
        name="reference-implementation",
    ),
    path(
        "platform-checking/",
        login_required(PlatformCheckingView.as_view()),
        name="platform-checking",
    ),
]
