import pytest

from telliot_feeds.sources.mimicry.mimicry import MimicryCollectionStatSource
from telliot_feeds.sources.mimicry.mimicry_mashup_source import NFTMashupSource


@pytest.mark.skip("See issue 603")
@pytest.mark.asyncio
async def test_fetching_data():
    """Test fetching data from Mimicry API"""
    # tami
    source = MimicryCollectionStatSource(
        chainId=1, collectionAddress="0x5180db8F5c931aaE63c74266b211F580155ecac8", metric=0
    )
    val, _ = await source.fetch_new_datapoint()
    assert isinstance(val, float)

    # market cap
    source.metric = 1
    val, _ = await source.fetch_new_datapoint()
    print(val)
    assert isinstance(val, float)


@pytest.mark.skip("Requires API key")
@pytest.mark.asyncio
async def test_fetching_nft_mashup_mcap():
    """Test mimicry market cap mashup"""

    source = NFTMashupSource(
        metric="market-cap",
        currency="usd",
        collections=(
            ("ethereum-mainnet", "0x50f5474724e0ee42d9a4e711ccfb275809fd6d4a"),
            ("ethereum-mainnet", "0xf87e31492faf9a91b02ee0deaad50d51d56d5d4d"),
            ("ethereum-mainnet", "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258"),
        ),
        tokens=(
            ("ethereum-mainnet", "sand", "0x3845badAde8e6dFF049820680d1F14bD3903a5d0"),
            ("ethereum-mainnet", "mana", "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942"),
            ("ethereum-mainnet", "ape", "0x4d224452801ACEd8B2F0aebE155379bb5D594381"),
        ),
    )
    val, _ = await source.fetch_new_datapoint()
    assert isinstance(val, int)
    assert val > 0
