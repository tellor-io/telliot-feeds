import pytest

from telliot_feeds.feeds.leth_usd_feed import leth_usd_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource


@pytest.mark.asyncio
async def test_leth_usd_feed(caplog, mock_price_feed):
    """Retrieve median ETH/USD price converted to LETH/USD by ratio"""
    mock_prices = [1200.50, 1205.25, 1202.75]
    mock_price_feed(
        leth_usd_feed, mock_prices, [CoinGeckoSpotPriceSource, GeminiSpotPriceSource, KrakenSpotPriceSource]
    )
    v, _ = await leth_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    # check contract response
    assert "total pooled tokens" in caplog.text.lower()
    assert "total supply" in caplog.text.lower()
    # check 4 sources for ETH/USD price:
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"LETH/USD Price: {v}")
