"""notesapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path("", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path("", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path("blog/", include("blog.urls"))
"""
import hashlib
import os.path
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.views.generic import RedirectView
from .apps.cases.models import Case

urlpatterns = [
    path("", include("accessibility_monitoring_platform.apps.dashboard.urls")),
    path("cases/", include("accessibility_monitoring_platform.apps.cases.urls")),
    path("websites/", include("accessibility_monitoring_platform.apps.websites.urls")),
    path("user/", include("accessibility_monitoring_platform.apps.users.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(r"admin/", admin.site.urls),
    path(r"favicon.ico", RedirectView.as_view(url="/static/images/favicon.ico")),
]

# When the server restarts, it will create and overwrite the current statuses in the db.
# The minor delay in restarting the server is very annoying during
# local development; therefore, the code below checks whether
# the status logic has changed. If it has, it will run case save.

FILE_HASH = "filehash.txt"
BUF_SIZE = 65536
hash_string = None

if os.path.isfile(FILE_HASH):
    with open(FILE_HASH, "r") as file:
        hash_string = file.read().replace("\n", "")

sha1 = hashlib.sha1()
with open("accessibility_monitoring_platform/apps/cases/models.py", "rb") as f:
    while True:
        data = f.read(BUF_SIZE)
        if not data:
            break
        sha1.update(data)

if hash_string != sha1.hexdigest():
    print(">>> Creating new status cache")
    open(FILE_HASH, "w").close()
    with open(FILE_HASH, "a") as file_object:
        file_object.write(sha1.hexdigest())
    resaved_status = False
    if resaved_status is False:
        for case in Case.objects.all():
            case.save()
        resaved_status = True
