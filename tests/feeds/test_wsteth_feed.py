import os
import statistics

import pytest
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds.wsteth_feed import wsteth_eth_median_feed
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource


@pytest.mark.asyncio
async def test_wsteth_eth_median_feed(caplog, mock_price_feed, monkeypatch):
    """Retrieve median WSTETH/ETH price."""
    custom_endpoint = RPCEndpoint(
        chain_id=1, network="mainnet", url=f"https://mainnet.infura.io/v3/{os.environ['INFURA_API_KEY']}"
    )

    def custom_find(chain_id):
        return [custom_endpoint]

    monkeypatch.setattr(wsteth_eth_median_feed.source.service.cfg.endpoints, "find", custom_find)
    mock_prices = [1200.50, 1205.25, 1202.75, 1201.00]
    mock_price_feed(
        wsteth_eth_median_feed,
        mock_prices,
        [CoinGeckoSpotPriceSource, CoinpaprikaSpotPriceSource, CurveFiUSDPriceSource, UniswapV3PriceSource],
    )
    v, _ = await wsteth_eth_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert "sources used in aggregate: 4" in caplog.text.lower()
    print(f"WSTETH/ETH Price: {v}")
    # Get list of data sources from sources dict
    source_prices = wsteth_eth_median_feed.source.latest[0]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median([source_prices])) < 10**-6
