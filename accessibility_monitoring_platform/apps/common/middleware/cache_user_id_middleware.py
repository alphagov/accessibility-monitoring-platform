"""cache_user_id_middleware - Caches user unique id to database"""

from report_viewer.apps.viewer.middleware.report_views_middleware import ReportMetrics
from accessibility_monitoring_platform.apps.common.models import UserCacheUniqueHash


class CacheUserUniqueID:
    """Middleware for recording report views to the database"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            rm: ReportMetrics = ReportMetrics(self.get_response)
            string_to_hash: str = rm.user_fingerprint(request)
            fingerprint_hash: int = rm.four_digit_hash(string_to_hash)
            UserCacheUniqueHash(
                user=request.user,
                fingerprint_hash=fingerprint_hash,
            ).save()
        except Exception as e:
            print(e)

        response = self.get_response(request)
        return response
