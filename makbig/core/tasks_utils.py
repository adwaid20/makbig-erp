import logging

logger = logging.getLogger(__name__)


def safe_delay(task, *args, **kwargs):
    """
    Dispatch via Celery if a live worker is reachable; otherwise run synchronously.

    Falls back to task.run() when:
      - broker (Redis) is unreachable  → inspect() raises, caught below
      - broker is up, no worker alive  → ping() returns empty/None
    """
    try:
        from celery import current_app
        if not current_app.control.inspect(timeout=0.5).ping():
            raise RuntimeError("No Celery workers available")
        logger.debug("safe_delay: dispatching %r via Celery.", task.name)
        return task.delay(*args, **kwargs)

    except Exception as exc:
        logger.error(
            "safe_delay: Celery unavailable for %r (%s) — running synchronously.",
            task.name, exc,
        )
        try:
            result = task.run(*args, **kwargs)
            logger.info("safe_delay: sync fallback for %r succeeded.", task.name)
            return result
        except Exception as sync_exc:
            logger.error("safe_delay: sync fallback for %r also failed: %s", task.name, sync_exc)
            return None
