from django.db import models


class EmailInclusionList(models.Model):
    inclusion_email = models.CharField(max_length=200)

    def __str__(self):
        return str(self.inclusion_email)
