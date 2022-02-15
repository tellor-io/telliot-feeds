import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.dai_usd_feed import dai_usd_median_feed
from telliot_feed_examples.reporters.tellorflex import PolygonReporter


@pytest.mark.skip("Run locally, github action testing failure")
@pytest.mark.asyncio
async def test_dai_usd_reporter_submit_once(mumbai_cfg):
    """Test reporting bct/usd on mumbai."""
    async with TelliotCore(config=mumbai_cfg) as core:
        flex = core.get_tellorflex_contracts()
        r = PolygonReporter(
            endpoint=core.endpoint,
            account=core.get_account(),
            chain_id=80001,
            oracle=flex.oracle,
            token=flex.token,
            datafeed=dai_usd_median_feed,
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
