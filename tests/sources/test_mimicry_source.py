import pytest

from telliot_feeds.sources.mimicry.collection_stat import MimicryCollectionStatSource


@pytest.mark.asyncio
async def test_fetching_data():
    """Test fetching data from Mimicry API"""
    # tami
    source = MimicryCollectionStatSource(
        chainId=1, collectionAddress="0x5180db8F5c931aaE63c74266b211F580155ecac8", metric=0
    )
    val, _ = await source.fetch_new_datapoint()
    print(val)
    assert isinstance(val, float)

    # market cap
    source.metric = 1
    val, _ = await source.fetch_new_datapoint()
    print(val)
    assert isinstance(val, float)
