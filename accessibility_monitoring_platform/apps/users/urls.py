"""
URLs - users
"""

from django.urls import path

from .views import UserCreateView, UserUpdateView


app_name = "users"
urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path("account-details/", UserUpdateView.as_view(), name="account_details"),
]
