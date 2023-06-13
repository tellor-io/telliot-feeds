from datetime import datetime

import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from telliot_core.apps.core import TelliotCore

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceSource,
)


@pytest.fixture
def diva_mock_contract():
    return accounts[0].deploy(DIVAProtocolMock)


@pytest.mark.asyncio
async def test_diva_datafeed(ropsten_test_cfg, diva_mock_contract) -> None:
    async with TelliotCore(config=ropsten_test_cfg) as core:
        account = core.get_account()
        feed = await assemble_diva_datafeed(
            pool_id="0x0ccf69d6832bcb70d201cd5d4014799d4e5b9944d7644522bfabecfe147ec2a0",  # todo: u
            node=core.endpoint,
            account=account,
            diva_address=diva_mock_contract.address,
        )

        assert isinstance(feed, DataFeed)
        assert isinstance(feed.query, DIVAProtocol)
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
            pool_id="0x17b06c50236906dd13e350f03ba7c937d810412feb2186f1dbafe6bdb9f88194",
            node=core.endpoint,
            account=account,
            diva_address=diva_mock_contract.address,
        )

        assert feed.source.asset == "btc"
        assert feed.source.sources[1].asset == "xbt"

        v, t = await feed.source.fetch_new_datapoint()

        assert v is None or isinstance(v, float)
        if v is not None:
            assert v > 30000
            assert isinstance(t, datetime)
