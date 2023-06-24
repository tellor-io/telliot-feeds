from datetime import datetime

import pytest
from telliot_core.apps.core import TelliotCore

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.pool import DivaPool
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.sources.price.historical.kraken import (
    KrakenHistoricalPriceSource,
)


@pytest.mark.asyncio
async def test_diva_datafeed(mumbai_test_cfg) -> None:
    async with TelliotCore(config=mumbai_test_cfg):
        pool = DivaPool(
            pool_id="0x0ccf69d6832bcb70d201cd5d4014799d4e5b9944d7644522bfabecfe147ec2a0",
            reference_asset="ETH/USD",
            collateral_token_address="0x6b175474e89094c44da98b954eedeac495271d0f",
            collateral_token_symbol="dUSD",
            collateral_balance=100000,
            expiry_time=1620000000,
        )
        feed = assemble_diva_datafeed(pool=pool)

        assert isinstance(feed, DataFeed)
        assert isinstance(feed.query, DIVAProtocol)
        assert isinstance(feed.source.reference_asset_source.sources[1], KrakenHistoricalPriceSource)
        assert isinstance(feed.source.reference_asset_source.sources[0].ts, int)
        assert feed.source.reference_asset_source.asset == "eth"
        assert feed.source.reference_asset_source.sources[1].currency == "usd"

        v, t = await feed.source.fetch_new_datapoint()
        assert v is None or isinstance(v, list)
        if v is not None:
            assert v[0] > 1000
            assert v[1] == 1
            assert isinstance(t, datetime)

        pool2 = DivaPool(
            pool_id="0x17b06c50236906dd13e350f03ba7c937d810412feb2186f1dbafe6bdb9f88194",
            reference_asset="BTC/USD",
            collateral_token_address="0x6b175474e89094c44da98b954eedeac495271d0f",
            collateral_token_symbol="dUSD",
            collateral_balance=100000,
            expiry_time=1620000000,
        )
        feed = assemble_diva_datafeed(pool=pool2)

        assert isinstance(feed, DataFeed)
        assert feed.source.reference_asset_source.asset == "btc"
        assert feed.source.reference_asset_source.sources[1].asset == "xbt"

        v, t = await feed.source.fetch_new_datapoint()

        assert v is None or isinstance(v, list)
        if v is not None:
            assert v[0] > 20000
            assert v[1] == 1
            assert isinstance(t, datetime)
