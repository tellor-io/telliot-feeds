"""
Construct Diva Protocol datafeed from pool info.

Fetch sources and make query instance from pool info
(reference asset, collateral token address, pool expiry & ID).
"""
import pytest

from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.sources import dUSDSource
from telliot_feeds.integrations.diva_protocol.utils import dict_to_pool


EXAMPLE_POOLS = [
    dict_to_pool(d)
    for d in [
        {
            "id": "49101",
            "referenceAsset": "ETH/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "100000000000000000000",
            "expiryTime": "1659001353",
        },
        {
            "id": "49102",
            "referenceAsset": "BTC/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "100000000000000000000",
            "expiryTime": "1659001922",
        },
        {
            "id": "49105",
            "referenceAsset": "1INCH/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "10000000000000000000",
            "expiryTime": "1659002533",
        },
        {
            "id": "49134",
            "referenceAsset": "AAVE/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "100000000000000000000",
            "expiryTime": "1659018168",
        },
        {
            "id": "49327",
            "referenceAsset": "ADA/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "96000000000000000000",
            "expiryTime": "1658992512",
        },
        {
            "id": "49329",
            "referenceAsset": "ZRX/USD",
            "collateralToken": {"symbol": "dUSD", "id": "0x134e62bd2ee247d4186a1fdbaa9e076cb26c1355"},
            "collateralBalance": "100000000000000000000",
            "expiryTime": "1658993052",
        },
    ]
]


def test_assemble_diva_datafeed():
    feed1 = assemble_diva_datafeed(EXAMPLE_POOLS[0])

    assert feed1.query.poolId == 49101
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
    assert 419 < val[1] < 421
