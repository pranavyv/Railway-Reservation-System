"""Small retry helper used for database connections (RRS-NF-002)."""
import logging
import time

log = logging.getLogger(__name__)


def retry(action, attempts=3, base_delay=0.3, retry_on=(Exception,), sleep=time.sleep):
    """Call action(); on a retryable error wait base_delay, then double it, up to `attempts` tries."""
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except retry_on as error:
            if attempt == attempts:
                raise
            log.warning("Attempt %s of %s failed (%s); retrying in %.1fs",
                        attempt, attempts, type(error).__name__, delay)
            sleep(delay)
            delay *= 2
