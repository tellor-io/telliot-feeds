from telliot_feeds.feeds.mimicry_feed import mimicry_collection_stat_datafeed

import pytest

@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve TAMI index and NFT market cap from source"""

    bored_apes_addy = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"

    mimicry_collection_stat_datafeed.source.chainId = 1
    mimicry_collection_stat_datafeed.source.collectionAddress = bored_apes_addy
    mimicry_collection_stat_datafeed.source.metric = 0

    tami, _ = await mimicry_collection_stat_datafeed.source.fetch_new_datapoint()
    print(tami)

    assert tami > 0
    
    mimicry_collection_stat_datafeed.source.metric = 1

    market_cap, _ = await mimicry_collection_stat_datafeed.source.fetch_new_datapoint()
    print(market_cap)

    assert market_cap > tami

