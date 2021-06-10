"""
URLs - users
"""

from django.urls import path
from accessibility_monitoring_platform.apps.users.views import register, account_details


app_name = 'users'
urlpatterns = [
    path('register/', register, name='register'),
    path('account_details/', account_details, name='account_details'),
]
