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

TEST_TYPE_CHOICES = [
    ("simple", "Simple"),
    ("detailed", "Detailed"),
]

WEBSITE_TYPE_CHOICES = [
    ("public", "Public website"),
    ("intranet", "Intranet"),
]



class Case(models.Model):
    """
    Model for Case
    """

    created = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    auditor = models.CharField(max_length=200)
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES, default="simple")
    home_page_url = models.CharField(max_length=200)
    application = models.CharField(max_length=200, default="N/A")
    organisation_name = models.CharField(max_length=200)
    website_type = models.CharField(max_length=10, choices=WEBSITE_TYPE_CHOICES, default="public")
    sector = models.CharField(max_length=200, default="Sector")
    region = models.CharField(max_length=200, default="London")
    case_origin = models.CharField(max_length=200, default="Organisation")
    zendesk_url = models.CharField(max_length=200, default="")
    trello_url = models.CharField(max_length=200, default="")
    notes = models.TextField(default="")
    is_public_sector_body = models.BooleanField(default=True)


    domain = models.CharField(max_length=200)
    simplified_test_filename = models.CharField(max_length=200)
    created_by = models.CharField(max_length=200)

    def __str__(self):
        return str(f"#{self.id} {self.organisation_name}")
