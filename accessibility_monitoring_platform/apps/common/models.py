"""
Models for common data used across project
"""
from django.db import models


class Sector(models.Model):
    """
    Model for website/organisation sector
    """

    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)
