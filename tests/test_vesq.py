import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.vesq import vsq_usd_median_feed
from telliot_feed_examples.reporters.tellorflex import PolygonReporter


@pytest.mark.asyncio
async def test_fetch_price():
    (value, ts) = await vsq_usd_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)


def test_query_info():
    q = vsq_usd_median_feed.query
    exp_id = "a21622568487d99fcdce1e75ddb12d40fecf323093ac9ee06099da27acae880c"
    exp_data = (
        "7b2274797065223a2253706f745072696365222c2261737365"
        "74223a22767371222c2263757272656e6379223a22757364227d"
    )

    assert q.query_data == b'{"type":"SpotPrice","asset":"vsq","currency":"usd"}'
    assert q.query_id.hex() == exp_id
    assert q.query_data.hex() == exp_data


@pytest.mark.asyncio
async def test_vsq_usd_reporter_submit_once(mumbai_cfg):
    """Test reporting Vesq on mumbai."""
    async with TelliotCore(config=mumbai_cfg) as core:
        flex = core.get_tellorflex_contracts()
        r = PolygonReporter(
            endpoint=core.endpoint,
            account=core.get_account(),
            chain_id=80001,
            oracle=flex.oracle,
            token=flex.token,
            datafeed=vsq_usd_median_feed,
            max_fee=100,
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
            "0xFd45Ae72E81Adaaf01cC61c8bCe016b7060DD537",  # polygon
            "0x41b66dd93b03e89D29114a7613A6f9f0d4F40178",  # mumbai
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
