import pytest
from brownie import accounts
from brownie import Autopay
from brownie import chain
from brownie import TellorPlayground
from telliot_core.tellor.tellor360.autopay import Tellor360AutopayContract

from telliot_feeds.feeds import matic_usd_median_feed
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip


# deploy new contracts
@pytest.fixture(scope="function")
def deploy(query_data_storage_contract):
    # deploy playground
    playground = accounts[0].deploy(TellorPlayground)
    # deploy autopay
    autopay = accounts[0].deploy(Autopay, playground.address, query_data_storage_contract.address, 20)
    return playground, autopay


@pytest.mark.asyncio
async def test_tips_disputed_submissions(deploy, mumbai_test_cfg):
    """Test to check if tipped query ids are suggested by tip listener after a tip eligible submission is disputed

    - Tip a query id
    - Check if the query id is suggested by tip listener
    - Submit a value for the query id
    - Check that the query id is not suggested by tip listener
    - Dispute the reported value
    - Check that the query id is suggested by tip listener
    """
    query_id = matic_usd_median_feed.query.query_id.hex()
    query_data = matic_usd_median_feed.query.query_data.hex()

    playground, autopay = deploy
    node = mumbai_test_cfg.get_endpoint()
    node.connect()
    txn = playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    assert txn.status == 1
    chain.mine(timedelta=1)
    # mint tokens
    txn = playground.faucet(accounts[0].address, {"from": accounts[0]})
    assert txn.status == 1
    # approve autopay to spend tokens
    txn = playground.approve(autopay.address, int(10e18), {"from": accounts[0]})
    assert txn.status == 1
    # tip query
    txn = autopay.tip(query_id, int(10e18), query_data, {"from": accounts[0]})
    assert txn.status == 1
    # assemble tellor autopay contract object
    tellor_autopay = Tellor360AutopayContract(node)
    tellor_autopay.address = autopay.address
    tellor_autopay.abi = autopay.abi
    tellor_autopay.connect()
    # get feed and tip, should not be none since we just tipped
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is not None
    assert tip is not None
    # submit a value
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    # tip should be none since we just submitted a value
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is None
    assert tip is None
    chain.mine(timedelta=1)
    playground.beginDispute(query_id, chain.time(), {"from": accounts[0]})
    # approve autopay to spend tokens
    txn = playground.approve(autopay.address, int(10e18), {"from": accounts[0]})
    assert txn.status == 1
    # tip query
    txn = autopay.tip(query_id, int(10e18), query_data, {"from": accounts[0]})
    assert txn.status == 1
    # submit a value
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    assert autopay.getCurrentTip(query_id) == 0
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is None
    assert tip is None
    playground.beginDispute(query_id, chain.time(), {"from": accounts[0]})
    # get feed and tip, should not be none since previous report was disputed
    chain.mine(timedelta=1)
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is not None
    assert tip > 0
    # submit a value
    time = chain.time()
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    assert autopay.getCurrentTip(query_id) == 0
    playground.beginDispute(query_id, time, {"from": accounts[0]})
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is not None
    assert tip > 0
    # claimOneTimeTip
    # advance time to bypass buffer
    chain.sleep(86400)
    txn = playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    assert txn.status == 1
    chain.mine(timedelta=1)
    txn = playground.approve(autopay.address, int(10e18), {"from": accounts[0]})
    assert txn.status == 1
    txn = autopay.setupDataFeed(
        query_id,
        int(1e18),  # reward
        chain.time(),  # start time
        3600,  # interval
        600,  # window
        0,  # price threshold
        0,  # reward increase per second
        query_data,
        int(10e18),
        {"from": accounts[0]},
    )
    assert txn.status == 1
    chain.mine(timedelta=1)
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is not None
    assert tip > 0
    # submit a value
    time = chain.time()
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, {"from": accounts[0]})
    chain.mine(timedelta=1)
    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is None
    assert tip is None
    # dispute value
    playground.beginDispute(query_id, time, {"from": accounts[0]})
    chain.mine(timedelta=1)

    datafeed, tip = await get_feed_and_tip(tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.time())
    assert datafeed is not None
    assert tip > 0
