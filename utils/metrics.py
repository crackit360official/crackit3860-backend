from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def calculate_streak(dates: list[datetime]) -> int:
    if not dates:
        return 0

    unique_days = sorted({d.date() for d in dates})

    streak = 1
    for i in range(1, len(unique_days)):
        if unique_days[i] - unique_days[i - 1] == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


async def track_attempt_metrics(data):
    """
    Fire-and-forget telemetry hook.
    Safe for Prometheus / Sentry / analytics queues.
    """
    try:
        # Example:
        # await send_to_queue(data)
        # attempt_histogram.observe(data.time_spent)
        pass
    except Exception as exc:
        logger.warning(
            "Metrics tracking failed",
            extra={"error": str(exc)},
        )
