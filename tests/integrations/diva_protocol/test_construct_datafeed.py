"""
Construct Diva Protocol datafeed from pool info.

Fetch sources and make query instance from pool info
(reference asset, collateral token address, pool expiry & ID).
"""
import pytest

from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.sources import dUSDSource
from telliot_feeds.integrations.diva_protocol.utils import dict_to_pool
from utils import EXAMPLE_POOLS_FROM_SUBGRAPH


EXAMPLE_POOLS = [dict_to_pool(d) for d in EXAMPLE_POOLS_FROM_SUBGRAPH]


def test_assemble_diva_datafeed():
    feed1 = assemble_diva_datafeed(EXAMPLE_POOLS[0])

    assert feed1.query.poolId.hex() == "0x0ccf69d6832bcb70d201cd5d4014799d4e5b9944d7644522bfabecfe147ec2a0"
    assert feed1.source.reference_asset_source.sources[0].asset == "eth"
    assert feed1.source.reference_asset_source.sources[0].currency == "usd"
    assert feed1.source.reference_asset_source.sources[0].ts == 1659001353
    assert isinstance(feed1.source.collat_token_source, dUSDSource)


def test_assemble_diva_datafeed_fail(caplog):
    feed = assemble_diva_datafeed(EXAMPLE_POOLS[2])

    assert "Unable to assemble DIVA datafeed. Unsupported reference asset: 1INCH/USD" in caplog.text
    assert feed is None


@pytest.mark.asyncio
async def test_diva_datafeed_fetch_data():
    feed = assemble_diva_datafeed(EXAMPLE_POOLS[1])
    val, _ = await feed.source.fetch_new_datapoint()

    assert val is not None
    assert val[0] > 0
    assert val[1] == 1.0
