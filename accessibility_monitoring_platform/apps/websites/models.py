"""
Models for websites app
"""

from django.db import models


class DomainRegister(models.Model):
    """ DomainRegister Model """

    domain_id = models.IntegerField(primary_key=True)
    domain_name = models.CharField(unique=True, max_length=1000)
    organisation_id = models.IntegerField(blank=True, null=True)
    parent_domain = models.CharField(max_length=1000, blank=True, null=True)
    service = models.CharField(max_length=1000, blank=True, null=True)
    sector = models.ForeignKey("Sector", models.DO_NOTHING, blank=True, null=True)
    service_type = models.CharField(max_length=1000, blank=True, null=True)
    registrant_email = models.CharField(max_length=1000, blank=True, null=True)
    registrant_address = models.CharField(max_length=1000, blank=True, null=True)
    registrant_postcode = models.CharField(max_length=1000, blank=True, null=True)
    nuts3 = models.CharField(max_length=5, blank=True, null=True)
    alexa_ranking = models.IntegerField(blank=True, null=True)
    http_status_code = models.ForeignKey(
        "HttpStatusCodes",
        models.DO_NOTHING,
        db_column="http_status_code",
        blank=True,
        null=True,
        related_name="http",
    )
    https_status_code = models.ForeignKey(
        "HttpStatusCodes",
        models.DO_NOTHING,
        db_column="https_status_code",
        blank=True,
        null=True,
        related_name="https",
    )
    requires_authentication = models.BooleanField(blank=True, null=True)
    data_source = models.CharField(max_length=1000, blank=True, null=True)
    is_a_website = models.BooleanField(blank=True, null=True)
    tempname = models.CharField(max_length=1000, blank=True, null=True)
    domain_name_level = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "domain_register"


class DomainsOrgs(models.Model):
    """ DomainsOrgs Model """

    domain = models.OneToOneField(DomainRegister, models.DO_NOTHING, primary_key=True)
    organisation = models.ForeignKey("Organisation", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "domains_orgs"
        unique_together = (("domain", "organisation"),)


class HttpStatusCodes(models.Model):
    """ HttpStatusCodes Model """

    status = models.CharField(primary_key=True, max_length=3)
    status_description = models.CharField(max_length=1000)
    status_type = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "http_status_codes"


class NutsArea(models.Model):
    """ NutsArea Model """

    area_code = models.CharField(primary_key=True, max_length=1000)
    area_name = models.CharField(max_length=1000)
    parent = models.CharField(max_length=1000, blank=True, null=True)
    area_level = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "nuts_area"


class OrgOrgtype(models.Model):
    """ OrgOrgtype Model """

    organisation = models.OneToOneField(
        "Organisation", models.DO_NOTHING, primary_key=True
    )
    organisation_type = models.ForeignKey("OrganisationType", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "org_orgtype"
        unique_together = (("organisation", "organisation_type"),)


class Organisation(models.Model):
    """ Organisation Model """

    organisation_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=1000)
    abbreviation = models.CharField(max_length=1000, blank=True, null=True)
    organisation_type = models.ForeignKey(
        "OrganisationType", models.DO_NOTHING, blank=True, null=True
    )
    own_website = models.BooleanField(blank=True, null=True)
    format = models.CharField(max_length=1000, blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    street = models.CharField(max_length=1000, blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    temp_school_website = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "organisation"


class OrganisationType(models.Model):
    """ OrganisationType Model """

    organisation_type_id = models.IntegerField(primary_key=True)
    type_name = models.CharField(max_length=1000)
    group_name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "organisation_type"


class Sector(models.Model):
    """ Sector Model """

    sector_id = models.IntegerField(primary_key=True)
    sector_name = models.CharField(max_length=1000)

    class Meta:
        managed = False
        db_table = "sector"

    def __str__(self):
        return self.sector_name


class WebsiteRegister(models.Model):
    """ WebsiteRegister Model """

    website_id = models.IntegerField(primary_key=True, unique=True)
    url = models.CharField(max_length=1000)
    service = models.CharField(max_length=1000, blank=True, null=True)
    htmlhead_title = models.CharField(max_length=1000, blank=True, null=True)
    htmlmeta_description = models.CharField(max_length=1000, blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    sector = models.ForeignKey("Sector", models.DO_NOTHING, blank=True, null=True)
    original_domain = models.CharField(max_length=1000, blank=True, null=True)
    nuts3 = models.CharField(max_length=5, blank=True, null=True)
    requires_authentication = models.BooleanField(blank=True, null=True)
    holding_page = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "website_register"

    def __str__(self):
        return f"#{self.website_id}: {self.url}"


class WebsitesOrgs(models.Model):
    """ WebsitesOrgs Model """

    website = models.OneToOneField(WebsiteRegister, models.DO_NOTHING, primary_key=True)
    organisation = models.ForeignKey(Organisation, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "websites_orgs"
        unique_together = (("website", "organisation"),)


class NutsConversion(models.Model):
    """ NutsConversion Model """

    lad18cd = models.CharField(
        db_column="LAD18CD", max_length=200, blank=True, null=True
    )
    lad18nm = models.CharField(
        db_column="LAD18NM", max_length=200, blank=True, null=True
    )
    lau118cd = models.CharField(
        db_column="LAU118CD", max_length=200, blank=True, null=True
    )
    lau118nm = models.CharField(
        db_column="LAU118NM", max_length=200, blank=True, null=True
    )
    nuts318cd = models.CharField(
        db_column="NUTS318CD", max_length=200, blank=True, null=True
    )
    nuts318nm = models.CharField(db_column="NUTS318NM", max_length=200, blank=True)
    nuts218cd = models.CharField(
        db_column="NUTS218CD", max_length=200, blank=True, null=True
    )
    nuts218nm = models.CharField(
        db_column="NUTS218NM", max_length=200, blank=True, null=True
    )
    nuts118cd = models.CharField(
        db_column="NUTS118CD", max_length=200, blank=True, null=True
    )
    nuts118nm = models.CharField(
        db_column="NUTS118NM", max_length=200, blank=True, null=True
    )
    fid = models.IntegerField(primary_key=True, db_column="FID")

    class Meta:
        managed = False
        db_table = "nuts_conversion"
