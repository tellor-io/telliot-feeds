import pytest
from telliot_feeds.sources.mimicry import MimicryCollectionStatSource, Transaction, TransactionList

chain_id = 1
collection = "0x5180db8F5c931aaE63c74266b211F580155ecac8"

transactions = [
    Transaction(500, "Lavender", 1),
    Transaction(700, "Hyacinth", 2),
    Transaction(400, "Hyacinth", 3),
    Transaction(612, "Mars", 4),
    Transaction(1200, "Mars", 5)
    ]

transactions_list = TransactionList(transactions=transactions, floor_price=700)

@pytest.mark.asyncio
async def test_get_collection_market_cap():
    """test algorithm for calculating market cap of an NFT collection"""

    mc = MimicryCollectionStatSource(chainId=1, collectionAddress=collection, metric=1)

    market_cap = await mc.get_collection_market_cap(transactions_list)

    assert market_cap == 2600

@pytest.mark.asyncio
async def test_tami():
    """test implementation of the TAMI algorithm"""

    mc = MimicryCollectionStatSource(chainId=1, collectionAddress=collection, metric=1)

    tami_index = await mc.tami(transactions_list)

    assert tami_index == 520.83
