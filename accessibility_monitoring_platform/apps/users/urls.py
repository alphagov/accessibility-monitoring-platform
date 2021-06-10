"""
URLs - users
"""

from django.conf.urls import url
from accessibility_monitoring_platform.apps.users.views import register, account_details


app_name = 'users'
urlpatterns = [
    url('register/', register, name='register'),
    url('account_details/', account_details, name='account_details'),
]
