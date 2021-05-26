"""
Models - cases
"""
from typing import List, Union

from django.db import models
from django.db.models import QuerySet
from django.core.paginator import Paginator, Page
from django.http.request import HttpRequest

class PageQuerySet(models.QuerySet):
    """
    QuerySet to provide pagination
    """

    def per_page(self, request: HttpRequest, per_page: int) -> Page:
        paginator: Paginator = Paginator(self, per_page)
        page_number: Union[str, None] = request.GET.get("page")
        return paginator.get_page(page_number)

PageManager: models.Manager = models.Manager.from_queryset(PageQuerySet)


class Case(models.Model):
    """
    Model for Case.
    """
    website_name = models.CharField(max_length=200)
    home_page_url = models.CharField(max_length=200)
    auditor = models.CharField(max_length=200)
    simplified_test_filename = models.CharField(max_length=200)
    created = models.DateTimeField()
    created_by = models.CharField(max_length=200)

    objects = PageManager()

    def __str__(self):
        return str(f"#{self.id} {self.website_name}")
