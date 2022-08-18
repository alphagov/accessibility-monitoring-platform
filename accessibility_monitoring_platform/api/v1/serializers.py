"""
Serialisers for api
"""
from rest_framework import serializers

from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report


class S3ReportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = S3Report
        fields = ["guid", "html", "case_id"]
