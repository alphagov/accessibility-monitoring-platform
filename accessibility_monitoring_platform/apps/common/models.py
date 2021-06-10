"""
Models for common data used across project
"""
from django.db import models


class Region(models.Model):
    """
    Model for geographic Region
    """

    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)
