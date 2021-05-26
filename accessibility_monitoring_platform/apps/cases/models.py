"""
Models - cases
"""
from django.db import models

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

    def __str__(self):
        return str(f"#{self.id} {self.website_name}")
