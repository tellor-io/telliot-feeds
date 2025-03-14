import statistics

import pytest

from telliot_feeds.feeds.wrseth_usd_feed import wrseth_usd_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource


@pytest.mark.asyncio
async def test_wrseth_usd_feed(caplog, mock_price_feed):
    """Retrieve median WrsETH/USD price."""
    mock_prices = [1200.50, 1205.25, 1202.75, 1201.00]
    mock_price_feed(
        wrseth_usd_feed,
        mock_prices,
        [CoinGeckoSpotPriceSource, CoinpaprikaSpotPriceSource, CurveFiUSDPriceSource, UniswapV3PriceSource],
    )
    v, _ = await wrseth_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"WrsETH/USD Price: {v}")
    # Get list of data sources from sources dict
    source_prices = wrseth_usd_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
