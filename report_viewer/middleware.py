from django.http import HttpResponse

class ALBHealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/alb-health/":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
