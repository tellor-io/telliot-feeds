import pytest

from telliot_feeds.feeds.mimicry_feed import mimicry_collection_stat_datafeed


@pytest.mark.skip("TODO: see issue 603")
@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve TAMI index and NFT market cap from source"""

    crypto_coven_address = "0x5180db8F5c931aaE63c74266b211F580155ecac8"

    mimicry_collection_stat_datafeed.source.chainId = 1
    mimicry_collection_stat_datafeed.source.collectionAddress = crypto_coven_address
    mimicry_collection_stat_datafeed.source.metric = 0

    tami, _ = await mimicry_collection_stat_datafeed.source.fetch_new_datapoint()
    print(tami)

    assert tami > 0

    mimicry_collection_stat_datafeed.source.metric = 1

    market_cap, _ = await mimicry_collection_stat_datafeed.source.fetch_new_datapoint()
    print(market_cap)

    assert market_cap > tami
