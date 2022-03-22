import time


def ensure_valid_timestamp(ts: int, period: int) -> int:
    """Adjust timestamp if not enought time between timestamp
    and current time to include the second half of the period."""
    now = int(time.time())

    if ts + period / 2 > now:
        return int(now - period / 2)

    return ts
