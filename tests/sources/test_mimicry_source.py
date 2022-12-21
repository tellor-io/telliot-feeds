import pytest

from telliot_feeds.sources.mimicry import IndexValueHistoryList
from telliot_feeds.sources.mimicry import MimicryCollectionStatSource
from telliot_feeds.sources.mimicry import Transaction
from telliot_feeds.sources.mimicry import TransactionList

chain_id = 1
collection = "0x5180db8F5c931aaE63c74266b211F580155ecac8"


@pytest.fixture(scope="function")
def transactions_list():
    transactions = [
        Transaction(500, "Lavender", 1593129600000),
        Transaction(700, "Hyacinth", 1600992000000),
        Transaction(400, "Hyacinth", 1614211200000),
        Transaction(612, "Mars", 1624406400000),
        Transaction(1200, "Mars", 1639008000000),
    ]

    return TransactionList(transactions=transactions, floor_price=700)


@pytest.mark.asyncio
async def test_get_collection_market_cap(transactions_list):
    """test algorithm for calculating market cap of an NFT collection"""

    mc = MimicryCollectionStatSource(chainId=1, collectionAddress=collection, metric=1)

    market_cap = mc.get_collection_market_cap(transactions_list)

    assert market_cap == 2600


@pytest.mark.asyncio
async def test_tami(transactions_list):
    """test implementation of the TAMI algorithm"""

    mc = MimicryCollectionStatSource(chainId=1, collectionAddress=collection, metric=1)

    tami_index = mc.tami(transactions_list)

    assert tami_index == pytest.approx(1832.411067193676)


@pytest.mark.asyncio
async def test_index_ratios(transactions_list: TransactionList):
    """test calculation of index ratios"""

    transactions_list.sort_transactions("timestamp")

    history_list: IndexValueHistoryList = transactions_list.create_index_value_history()

    iv = history_list.get_index_value()

    index_ratios = history_list.get_index_ratios()

    assert iv == pytest.approx(520.8333333333334)
    assert index_ratios[0] == 1.0
    assert index_ratios[1] == pytest.approx(1.06, 1e6)
    assert index_ratios[2] == pytest.approx(2.304)


@pytest.mark.asyncio
async def test_index_value(transactions_list: TransactionList):
    """test index price calculation"""

    transactions_list.sort_transactions("timestamp")

    history_list: IndexValueHistoryList = transactions_list.create_index_value_history()

    expected_index_values = [500, 500, 375, 375, 520.8333333333334]

    actual_index_values = []

    for i in history_list.index_values:
        actual_index_values.append(i.index_value)

    assert expected_index_values == actual_index_values


@pytest.mark.asyncio
async def test_filter_valid_transactions(transactions_list: TransactionList):
    """test that TAMI algorithm filters the right transactions"""

    transactions_list.sort_transactions("timestamp")

    assert len(transactions_list.transactions) == 5

    transactions_list.filter_valid_transactions()

    assert len(transactions_list.transactions) == 4


@pytest.mark.asyncio
async def test_sort_transactions(transactions_list: TransactionList):

    transactions_list.sort_transactions("timestamp")

    prev_timestamp = 0
    for tx in transactions_list.transactions:
        assert tx.timestamp > prev_timestamp
        prev_timestamp = tx.timestamp


@pytest.mark.asyncio
async def test_fetching_data():

    # tami
    source = MimicryCollectionStatSource(chainId=1, collectionAddress=collection, metric=0)
    val, _ = await source.fetch_new_datapoint()
    assert isinstance(val, float)

    # market cap
    source.metric = 1
    val, _ = await source.fetch_new_datapoint()
    print(val)
    assert isinstance(val, float)
