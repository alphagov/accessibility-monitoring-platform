"""
URLs - users
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import UserCreateView, UserUpdateView

app_name = "users"
urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path(
        "<int:pk>/edit-user/",
        login_required(UserUpdateView.as_view()),
        name="edit-user",
    ),
]
