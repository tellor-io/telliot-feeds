# import statistics
import os

import pytest
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds.sfrxusd_usd_feed import sfrxusd_usd_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource


@pytest.mark.asyncio
async def test_sfrxusd_usd_feed(caplog, mock_price_feed, monkeypatch):
    """Retrieve SFRXUSD/USD price"""
    custom_endpoint = RPCEndpoint(chain_id=1, url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}")

    def custom_find(chain_id):
        return [custom_endpoint]

    monkeypatch.setattr(sfrxusd_usd_feed.source.service.cfg.endpoints, "find", custom_find)
    mock_prices = [0.99, 1.11, 0.12]
    mock_price_feed(
        sfrxusd_usd_feed, mock_prices, [CoinGeckoSpotPriceSource, CoinpaprikaSpotPriceSource, CurveFiUSDPriceSource]
    )
    v, _ = await sfrxusd_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 3" in caplog.text.lower()
    print(f"SFRXUSD/USD Price: {v}")
