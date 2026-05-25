import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SafeCache:
    """
    Fault-tolerant wrapper around Django's cache.
    All methods silently absorb exceptions and log at WARNING level.
    Redis being offline must never propagate an exception to the caller.
    """

    @staticmethod
    def get(key, default=None):
        try:
            return cache.get(key, default)
        except Exception as exc:
            logger.warning("SafeCache.get failed for key=%r: %s", key, exc)
            return default

    @staticmethod
    def set(key, value, timeout=None):
        try:
            cache.set(key, value, timeout)
            return True
        except Exception as exc:
            logger.warning("SafeCache.set failed for key=%r: %s", key, exc)
            return False

    @staticmethod
    def delete(key):
        try:
            cache.delete(key)
            return True
        except Exception as exc:
            logger.warning("SafeCache.delete failed for key=%r: %s", key, exc)
            return False
