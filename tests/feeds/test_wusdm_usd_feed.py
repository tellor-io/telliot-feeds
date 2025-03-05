# import statistics
import os

import pytest
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds.wusdm_usd_feed import wusdm_usd_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource


@pytest.mark.asyncio
async def test_wusdm_usd_feed(caplog, mock_price_feed, monkeypatch):
    """Retrieve median USDM/USD price converted to wUSDM by ratio"""
    custom_endpoint = RPCEndpoint(chain_id=1, url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}")

    def custom_find(chain_id):
        return [custom_endpoint]

    monkeypatch.setattr(wusdm_usd_feed.source.service.cfg.endpoints, "find", custom_find)
    mock_prices = [1200.50, 1205.25]
    mock_price_feed(wusdm_usd_feed, mock_prices, [CoinGeckoSpotPriceSource, CoinpaprikaSpotPriceSource])
    v, _ = await wusdm_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 2" in caplog.text.lower()
    print(f"wusdm/usd Price: {v}")

    # Get list of data sources from sources dict
    # source_prices = [source.latest[0] for source in usdm_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    # assert (v - statistics.median(source_prices)) < 10**-6
