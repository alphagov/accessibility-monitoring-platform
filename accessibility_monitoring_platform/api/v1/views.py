"""
Views for api
"""
from rest_framework import viewsets, status
from rest_framework.response import Response

from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

from .serializers import S3ReportSerializer


class S3ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for S3Report"""

    queryset = S3Report.objects.all()
    lookup_field = "guid"
    serializer_class = S3ReportSerializer
    http_method_names = ["get"]

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
