import statistics

import pytest

from telliot_feeds.feeds.aave_usd_feed import aave_usd_median_feed


@pytest.mark.asyncio
async def test_aave_usd_median_feed(mock_price_feed, caplog):
    """Retrieve median aave/USD price."""
    mock_prices = [1200.50, 1205.25, 1202.75]
    mock_price_feed(aave_usd_median_feed, mock_prices)

    v, _ = await aave_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"aave/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in aave_usd_median_feed.source.sources]
    print(source_prices)

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6


# @pytest.mark.asyncio
# async def test_aave_usd_median_feed(mock_price_feed, caplog):
#     """Test the AAVE/USD median price feed with mocked sources (3 sources)."""
#     # Option 1: Provide a list with exact number of values
#     mock_prices = [1200.50, 1205.25, 1202.75]
#     expected_median = mock_price_feed(aave_usd_median_feed, mock_prices)

#     v, _ = await aave_usd_median_feed.source.fetch_new_datapoint()
#     assert abs(v - expected_median) < 10**-6
#     assert v is not None
#     assert v > 0
#     assert "sources used in aggregate: 3" in caplog.text.lower()
#     print(f"aave/USD Price: {v}")
