import pytest

from telliot_feeds.feeds.eth_usd_30day_volatility import eth_usd_30day_volatility


@pytest.mark.asyncio
async def test_fetch_price():
    (value, _) = await eth_usd_30day_volatility.source.fetch_new_datapoint()
    assert value > 0
    print(value)
