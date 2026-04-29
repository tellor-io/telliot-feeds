import pytest
import yaml

from telliot_feeds.feeds.uspce_feed import uspce_feed
from telliot_feeds.sources.bea_gov import BEAPCESource


@pytest.mark.asyncio
async def test_uspce_feed():
    """Test USPCE feed."""
    feed = uspce_feed

    print(yaml.dump(feed.get_state(), sort_keys=False))
    assert isinstance(feed.source, BEAPCESource)

    value, timestamp = await feed.source.fetch_new_datapoint()
    print(f"USPCE report value: {value}")
    print(f"USPCE report timestamp: {timestamp}")

    assert value is not None
    assert timestamp is not None
