import pytest

from telliot_feeds.feeds.sfrax_usd_feed import sfrax_usd_feed
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource


@pytest.mark.asyncio
async def test_sfrax_usd_feed(caplog, mock_price_feed, monkeypatch):
    """Retrieve median sFRAX/USD price converted to wUSDM by ratio with custom endpoint"""

    monkeypatch.setattr(sfrax_usd_feed.source.service, "get_sfrax_usd_ratio", lambda: 1.05)
    mock_prices = [1200.50, 1202.75, 1201.00]
    mock_price_feed(
        sfrax_usd_feed,
        mock_prices,
        [CoinpaprikaSpotPriceSource, CurveFiUSDPriceSource, UniswapV3PriceSource],
    )
    v, _ = await sfrax_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"sfrax/usd Price: {v}")

    # Get list of data sources from sources dict
    # source_prices = [source.latest[0] for source in sfrax_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    # assert (v - statistics.median(source_prices)) < 10**-6
