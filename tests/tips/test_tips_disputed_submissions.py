import pytest
from telliot_core.tellor.tellor360.autopay import Tellor360AutopayContract

from telliot_feeds.feeds import matic_usd_median_feed
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip


# deploy new contracts
@pytest.fixture(scope="function")
def deploy(accounts, project):
    # deploy playground
    playground = accounts[0].deploy(project.TellorPlayground)
    # deploy autopay
    query_data_storage_contract = accounts[0].deploy(project.QueryDataStorage)
    autopay = accounts[0].deploy(project.Autopay, playground.address, query_data_storage_contract.address, 20)
    return playground, autopay


@pytest.mark.asyncio
async def test_tips_disputed_submissions(deploy, project, mumbai_test_cfg, accounts, chain):
    """Test to check if tipped query ids are suggested by tip listener after a tip eligible submission is disputed

    - Tip a query id
    - Check if the query id is suggested by tip listener
    - Submit a value for the query id
    - Check that the query id is not suggested by tip listener
    - Dispute the reported value
    - Check that the query id is suggested by tip listener
    """
    query_id = matic_usd_median_feed.query.query_id
    query_data = matic_usd_median_feed.query.query_data

    playground, autopay = deploy
    node = mumbai_test_cfg.get_endpoint()
    node.connect()
    txn = playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    assert txn.status == 1
    chain.mine(1)
    # mint tokens
    txn = playground.faucet(accounts[0].address, sender=accounts[0])
    assert txn.status == 1
    # approve autopay to spend tokens
    txn = playground.approve(autopay.address, int(10e18), sender=accounts[0])
    assert txn.status == 1
    # tip query
    txn = autopay.tip(query_id, int(10e18), query_data, sender=accounts[0])
    assert txn.status == 1
    # assemble tellor autopay contract object
    tellor_autopay = Tellor360AutopayContract(node)
    tellor_autopay.address = autopay.address
    tellor_autopay.abi = project.Autopay.contract_type.model_dump().get("abi", [])
    tellor_autopay.connect()
    # get feed and tip, should not be none since we just tipped
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is not None
    assert tip is not None
    # submit a value
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    # tip should be none since we just submitted a value
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is None
    assert tip is None
    chain.mine(1)
    playground.beginDispute(query_id, chain.pending_timestamp, sender=accounts[0])
    # approve autopay to spend tokens
    txn = playground.approve(autopay.address, int(10e18), sender=accounts[0])
    assert txn.status == 1
    # tip query
    txn = autopay.tip(query_id, int(10e18), query_data, sender=accounts[0])
    assert txn.status == 1
    # submit a value
    time = chain.pending_timestamp
    txn = playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    assert txn.status == 1
    assert autopay.getCurrentTip(query_id) == 0
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is None
    assert tip is None
    txn = playground.beginDispute(query_id, time, sender=accounts[0])
    assert txn.status == 1
    # get feed and tip, should not be none since previous report was disputed
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is not None
    assert tip > 0
    # submit a value
    time = chain.pending_timestamp
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    assert autopay.getCurrentTip(query_id) == 0
    playground.beginDispute(query_id, time, sender=accounts[0])
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is not None
    assert tip > 0
    # claimOneTimeTip
    # advance time to bypass buffer
    chain.pending_timestamp += 86400
    txn = playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    assert txn.status == 1
    txn = playground.approve(autopay.address, int(10e18), sender=accounts[0])
    assert txn.status == 1
    txn = autopay.setupDataFeed(
        query_id,
        int(1e18),  # reward
        chain.pending_timestamp,  # start time
        3600,  # interval
        600,  # window
        0,  # price threshold
        0,  # reward increase per second
        query_data,
        int(10e18),
        sender=accounts[0],
    )
    assert txn.status == 1
    chain.mine(1)
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is not None
    assert tip > 0
    # submit a value
    time = chain.pending_timestamp
    playground.submitValue(query_id, int.to_bytes(100, 32, "big"), 0, query_data, sender=accounts[0])
    chain.mine(1)
    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is None
    assert tip is None
    # dispute value
    playground.beginDispute(query_id, time, sender=accounts[0])
    chain.mine(1)

    datafeed, tip = await get_feed_and_tip(
        tellor_autopay, skip_manual_feeds=False, current_timestamp=chain.pending_timestamp
    )
    assert datafeed is not None
    assert tip > 0
