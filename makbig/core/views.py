import logging
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Diagnostic endpoint. Always returns HTTP 200.
    Reports 'redis': 'unavailable' in JSON body when Redis is down.
    """
    status = {"django": "ok", "redis": "ok"}

    try:
        cache.set("__makbig_health_probe__", "1", timeout=10)
        cache.get("__makbig_health_probe__")
    except Exception as exc:
        logger.warning("health_check: Redis probe failed: %s", exc)
        status["redis"] = "unavailable"

    return JsonResponse(status, status=200)
