from django.db import models


class AxeRule(models.Model):
    """ AxeRule Model """
    rule_id = models.IntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField(null=True)
    impact = models.TextField(null=True)
    selector = models.TextField(null=True)
    tags = models.TextField(null=True)
    help = models.TextField(null=True)

    def __str__(self):
        return f"#{self.rule_id}: {self.name}"

    class Meta:
        managed = False
        db_table = "axe_rule"


class AxeWcag(models.Model):
    """ AxeWcag Model """
    axe_rule_id = models.IntegerField(primary_key=True)
    wcag_criterion_number = models.CharField(max_length=9)
  
    def __str__(self):
        return f"#{self.axe_rule_id}: {self.wcag_criterion_number}"

    class Meta:
        managed = False
        db_table = "axe_wcag"


class TestresultAxeData(models.Model):
    """ TestresultAxeData Model """
    test_data_id = models.IntegerField(primary_key=True)
    test_id = models.IntegerField()
    rule_name = models.TextField()
    test_status = models.TextField()
    nodes = models.TextField(null=True)

    def __str__(self):
        return f"#{self.test_data_id}: {self.rule_name}"

    class Meta:
        managed = False
        db_table = "testresult_axe_data"


class TestresultAxeHeader(models.Model):
    """ TestresultAxeHeader Model """
    test_id = models.IntegerField(primary_key=True)
    test_timestamp = models.DateTimeField(blank=True, null=True)
    url = models.TextField(null=True)
    domain_name = models.TextField(null=True)
    axe_version = models.TextField(null=True)
    test_environment = models.TextField(null=True)
    time_taken = models.FloatField(null=True)
    test_succeeded = models.BooleanField(null=True)
    further_info = models.TextField(null=True)

    def __str__(self):
        return f"#{self.test_id}: {self.test_timestamp}"

    class Meta:
        managed = False
        db_table = "testresult_axe_header"
        ordering = ["domain_name", "test_timestamp", "test_id"]


class WcagCriteria(models.Model):
    """ WcagCriteria Model """
    criterion_number = models.CharField(max_length=9, primary_key=True)
    description = models.TextField(null=True)
    wcag_version = models.CharField(max_length=4, null=True)
    wcag_level = models.CharField(max_length=4, null=True)

    def __str__(self):
        return f"{self.criterion_number.strip()}: {self.description}"

    class Meta:
        managed = False
        db_table = "wcag_criteria"


class WcagRecommendation(models.Model):
    """ WcagRecommendation Model """
    recommendation_id = models.IntegerField(primary_key=True)
    criterion_number = models.CharField(max_length=9)
    recommendation = models.TextField(null=True)

    def __str__(self):
        return f"#{self.recommendation_id}: {self.recommendation}"

    class Meta:
        managed = False
        db_table = "wcag_recommendation"
