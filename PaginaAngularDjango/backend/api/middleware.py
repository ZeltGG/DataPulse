import logging
import time

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        username = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'anonymous'
        logger.info(
            'request method=%s path=%s user=%s status=%s duration_ms=%s',
            request.method,
            request.path,
            username,
            response.status_code,
            duration_ms,
        )
        return response
