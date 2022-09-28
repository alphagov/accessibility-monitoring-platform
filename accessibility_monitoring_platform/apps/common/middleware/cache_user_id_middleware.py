"""cache_user_id_middleware - Caches user unique id to database"""

import logging

from report_viewer.apps.viewer.middleware.report_views_middleware import ReportMetrics
from accessibility_monitoring_platform.apps.common.models import UserCacheUniqueHash

logger = logging.getLogger(__name__)


class CacheUserUniqueID:
    """Middleware for recording report views to the database"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                report_metrics: ReportMetrics = ReportMetrics(self.get_response)
                string_to_hash: str = report_metrics.user_fingerprint(request)
                fingerprint_hash: int = report_metrics.four_digit_hash(string_to_hash)
                UserCacheUniqueHash(
                    user=request.user,
                    fingerprint_hash=fingerprint_hash,
                ).save()
        except Exception as e:
            logger.warning("Error in CacheUserUniqueID Middleware: %s", e)

        response = self.get_response(request)
        return response
