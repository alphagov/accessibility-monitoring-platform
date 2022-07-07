"""
Models - users
"""

from django.db import models


class AllowedEmail(models.Model):
    """
    Model for AllowedEmail.

    This model contains emails that are allowed to sign
    up to the app.
    """

    inclusion_email = models.CharField(max_length=200)

    def __str__(self):
        return str(self.inclusion_email)
