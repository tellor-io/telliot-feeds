import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.vesq import vsq_usd_median_feed
from telliot_feed_examples.reporters.tellorflex import PolygonReporter


@pytest.mark.skip("Avoid coingecko rate limits")
@pytest.mark.asyncio
async def test_fetch_price():
    (value, _) = await vsq_usd_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)


def test_query_info():
    q = vsq_usd_median_feed.query
    exp_id = "a9b17c33422e2e576fb664d1d11d38c377b614d62f92653d006eca7bb2af1656"
    exp_data = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03vsq\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03usd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # noqa: E501
    exp_data_hex = "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003767371000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501

    # print(q.query_data)
    assert q.query_data == exp_data
    assert q.query_id.hex() == exp_id
    assert q.query_data.hex() == exp_data_hex


@pytest.mark.skip("Asks for password")
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
            assert (
                ("Currently in reporter lock." in status.error)
                or ("Current addess disputed" in status.error)
                or ("Unable to retrieve updated datafeed" in status.error)
            )
