import pytest
from telliot_core.api import DataFeed
from telliot_core.apps.core import TelliotCore
from telliot_core.queries.diva_protocol import divaProtocolPolygon

from telliot_feed_examples.utils.diva_protocol import assemble_diva_datafeed


@pytest.mark.asyncio
async def test_assemble_diva_datafeed(ropsten_cfg) -> None:
    async with TelliotCore(config=ropsten_cfg) as core:
        account = core.get_account()
        feed = await assemble_diva_datafeed(
            pool_id=159, node=core.endpoint, account=account
        )

        assert isinstance(feed, DataFeed)
        assert isinstance(feed.query, divaProtocolPolygon)
        assert feed.source.asset == "btc"
