import logging

logger = logging.getLogger(__name__)


def safe_delay(task, *args, **kwargs):
    """
    Attempt task.delay(*args, **kwargs).
    On any broker failure, fall back to calling the task synchronously.

    Do not use for long-running tasks — synchronous fallback blocks the
    request thread.
    """
    try:
        return task.delay(*args, **kwargs)
    except Exception as exc:
        logger.error(
            "safe_delay: Celery broker unavailable for task %r, "
            "falling back to synchronous execution. Error: %s",
            task.name,
            exc,
        )
        try:
            return task(*args, **kwargs)
        except Exception as sync_exc:
            logger.error(
                "safe_delay: Synchronous fallback also failed for task %r: %s",
                task.name,
                sync_exc,
            )
            return None
