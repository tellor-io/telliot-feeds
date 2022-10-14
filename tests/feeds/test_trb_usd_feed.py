import statistics

import pytest

from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed


@pytest.mark.asyncio
async def test_trb_asset_price_feed():
    """Retrieve median TRB/USD price."""
    v, _ = await trb_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"TRB/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in trb_usd_median_feed.source.sources]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
