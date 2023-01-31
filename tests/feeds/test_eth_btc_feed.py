import statistics

import pytest

from telliot_feeds.feeds.eth_btc_feed import eth_btc_median_feed


@pytest.mark.asyncio
async def test_eth_btc_median_feed(caplog):
    """Retrieve median ETH/BTC price."""
    v, _ = await eth_btc_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert (  # sometimes only 3 sources are used bc binance restricts locations
        "sources used in aggregate: 4" in caplog.text.lower() or "sources used in aggregate: 3" in caplog.text.lower()
    )
    print(f"ETH/BTC Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in eth_btc_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
