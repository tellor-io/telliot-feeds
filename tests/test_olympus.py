import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.olympus import ohm_eth_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter


@pytest.mark.asyncio
async def test_fetch_price():
    (value, _) = await ohm_eth_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)


def test_query_info():
    q = ohm_eth_median_feed.query

    assert q.query_data == b'{"type":"SpotPrice","asset":"ohm","currency":"eth"}'
    assert (
        q.query_id.hex()
        == "0136f215d1f75daabc0c0726ad4356debeb9bc95b24344165145a56684995966"
    )
    assert (
        q.query_data.hex() == "7b2274797065223a2253706f745072696365222c2261"
        "73736574223a226f686d222c2263757272656e6379223a22657468227d"
    )


@pytest.mark.asyncio
async def test_ohm_eth_reporter_submit_once(rinkeby_cfg):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""
    async with TelliotCore(config=rinkeby_cfg) as core:
        account = core.get_account()
        tellorx = core.get_tellorx_contracts()
        r = IntervalReporter(
            endpoint=core.config.get_endpoint(),
            account=account,
            master=tellorx.master,
            oracle=tellorx.oracle,
            datafeed=ohm_eth_median_feed,
            expected_profit="YOLO",
            transaction_type=0,
            gas_limit=400000,
            max_fee=None,
            priority_fee=None,
            legacy_gas_price=None,
            gas_price_speed="safeLow",
            chain_id=core.config.main.chain_id,
        )

        EXPECTED_ERRORS = {
            "Current addess disputed. Switch address to continue reporting.",
            "Current address is locked in dispute or for withdrawal.",
            "Current address is in reporter lock.",
            "Estimated profitability below threshold.",
            "Estimated gas price is above maximum gas price.",
            "Unable to retrieve updated datafeed value.",
        }

        ORACLE_ADDRESSES = {
            "0xe8218cACb0a5421BC6409e498d9f8CC8869945ea",  # mainnet
            "0x18431fd88adF138e8b979A7246eb58EA7126ea16",  # rinkeby
        }

        tx_receipt, status = await r.report_once()

        # Reporter submitted
        if tx_receipt is not None and status.ok:
            assert isinstance(tx_receipt, AttributeDict)
            assert tx_receipt.to in ORACLE_ADDRESSES
        # Reporter did not submit
        else:
            assert not tx_receipt
            assert not status.ok
            assert status.error in EXPECTED_ERRORS
