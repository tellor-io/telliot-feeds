import time

from telliot_feed_examples.sources.price.historical.utils import ensure_valid_timestamp


def test_ensure_valid_timestamp():
    """Make sure timestamp not too soon."""
    too_soon_ts = int(time.time())
    period = 1234 # seconds
    adjusted_ts = ensure_valid_timestamp(too_soon_ts, period)

    assert adjusted_ts < too_soon_ts
    assert adjusted_ts + period/2 < time.time()