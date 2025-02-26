import pytest

from telliot_feeds.feeds.eth_usd_30day_volatility import eth_usd_30day_volatility


@pytest.mark.asyncio
async def test_fetch_price(mock_price_feed):
    mock_prices = [1200.50, 1205.25, 1202.75]
    mock_price_feed(eth_usd_30day_volatility, mock_prices)
    (value, _) = await eth_usd_30day_volatility.source.fetch_new_datapoint()
    assert value > 0
    print(value)
