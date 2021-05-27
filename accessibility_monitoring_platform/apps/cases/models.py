"""
Models - cases
"""
from django.db import models

STATUS_CHOICES = [
    ("new-case", "New case"),
    ("test-in-progress", "Test in progress"),
    ("report-in-progress", "Report in progress"),
    ("awaiting-response", "Awaiting response to report"),
    ("12w-due", "12 Week review due"),
    ("12w-sent", "12 Week review sent"),
    ("escalated", "Case sent to supporting bodies"),
    ("complete", "Complete"),
    ("archived", "Archived"),
    ("not-a-psb", "Not a public sector body"),
]
class Case(models.Model):
    """
    Model for Case
    """

    website_name = models.CharField(max_length=200)
    home_page_url = models.CharField(max_length=200)
    domain = models.CharField(max_length=200)
    auditor = models.CharField(max_length=200)
    simplified_test_filename = models.CharField(max_length=200)
    created = models.DateTimeField()
    created_by = models.CharField(max_length=200)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)

    def __str__(self):
        return str(f"#{self.id} {self.website_name}")
