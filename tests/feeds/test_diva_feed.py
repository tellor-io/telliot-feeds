from datetime import datetime

import pytest
from telliot_core.api import DataFeed
from telliot_core.apps.core import TelliotCore
from telliot_core.queries.diva_protocol import divaProtocolPolygon

from telliot_feed_examples.feeds.diva_protocol_feed import assemble_diva_datafeed
from telliot_feed_examples.feeds.diva_protocol_feed import DivaPoolParameters
from telliot_feed_examples.feeds.diva_protocol_feed import get_pool_params
from telliot_feed_examples.feeds.diva_protocol_feed import get_source
from telliot_feed_examples.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceSource,
)


def test_get_source() -> None:
    source = get_source("btc", 1243)

    assert source.sources[1].asset == "xbt"
    assert source.sources[3].ts == 1243


@pytest.mark.asyncio
async def test_get_pool_parameters(ropsten_cfg) -> None:
    async with TelliotCore(config=ropsten_cfg) as core:
        account = core.get_account()
        params = await get_pool_params(3, core.endpoint, account)

        assert isinstance(params, DivaPoolParameters)
        assert params.reference_asset == "ETH/USD"
        assert params.expiry_date == 1657349074


@pytest.mark.asyncio
async def test_diva_datafeed(ropsten_cfg) -> None:
    async with TelliotCore(config=ropsten_cfg) as core:
        account = core.get_account()
        feed = await assemble_diva_datafeed(
            pool_id=3, node=core.endpoint, account=account
        )

        assert isinstance(feed, DataFeed)
        assert isinstance(feed.query, divaProtocolPolygon)
        assert isinstance(feed.source.sources[3], PoloniexHistoricalPriceSource)
        assert isinstance(feed.source.sources[0].ts, int)
        assert feed.source.asset == "eth"
        assert feed.source.sources[2].currency == "dai"

        v, t = await feed.source.fetch_new_datapoint()
        assert v is None or isinstance(v, float)
        if v is not None:
            assert v > 1000
            assert isinstance(t, datetime)

        feed = await assemble_diva_datafeed(
            pool_id=10, node=core.endpoint, account=account
        )

        assert feed.source.asset == "btc"
        assert feed.source.sources[1].asset == "xbt"

        v, t = await feed.source.fetch_new_datapoint()

        assert v is None or isinstance(v, float)
        if v is not None:
            assert v > 30000
            assert isinstance(t, datetime)
