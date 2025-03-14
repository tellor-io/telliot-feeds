import statistics

import pytest

from telliot_feeds.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feeds.queries.query import OracleQuery


@pytest.mark.asyncio
async def test_AssetPriceFeed(mock_price_feed):
    """Retrieve median BTC price from example datafeed &
    make sure value is within tolerance."""

    # Get query
    q = btc_usd_median_feed.query
    assert isinstance(q, OracleQuery)

    # Fetch price
    # status, price, tstamp = await btc_usd_median_feed.update_value()
    mock_prices = [12000.50, 12005.25, 12002.75, 12003.75]
    mock_price_feed(btc_usd_median_feed, mock_prices)
    v, t = await btc_usd_median_feed.source.fetch_new_datapoint()

    # Make sure error is less than decimal tolerance
    # assert status.ok
    assert 10000 < v < 100000
    print(f"BTC Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in btc_usd_median_feed.source.sources]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
