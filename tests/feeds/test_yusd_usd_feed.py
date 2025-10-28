# import statistics
import os

import pytest
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds.yusd_usd_feed import yusd_usd_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource


@pytest.mark.asyncio
async def test_yusd_usd_feed(caplog, mock_price_feed, monkeypatch):
    """Retrieve yUSD/USD price"""
    custom_endpoint = RPCEndpoint(chain_id=1, url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}")

    def custom_find(chain_id):
        return [custom_endpoint]

    monkeypatch.setattr(yusd_usd_feed.source.service.cfg.endpoints, "find", custom_find)
    mock_prices = [1.12, 1.15]
    mock_price_feed(yusd_usd_feed, mock_prices, [CoinGeckoSpotPriceSource, CoinpaprikaSpotPriceSource])
    v, _ = await yusd_usd_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"yusd/usd Price: {v}")
