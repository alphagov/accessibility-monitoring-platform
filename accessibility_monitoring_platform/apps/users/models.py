"""
Models - users
"""

from django.contrib.auth.models import User
from django.db import models


class EmailInclusionList(models.Model):
    """
    Model for EmailInclusionList.

    This contains a list of emails that are allowed to sign
    up to the app.
    """

    inclusion_email = models.CharField(max_length=200)

    def __str__(self):
        return str(self.inclusion_email)
