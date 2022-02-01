import pytest
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.olympus import ohm_eth_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter


@pytest.mark.skip("Avoid coingecko rate limits")
@pytest.mark.asyncio
async def test_fetch_price():
    (value, _) = await ohm_eth_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)


def test_query_info():
    q = ohm_eth_median_feed.query
    assert (
        q.query_data
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03ohm\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03eth\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # noqa: E501
    )
    assert (
        q.query_id.hex()
        == "ee4fcdeed773931af0bcd16cfcea5b366682ffbd4994cf78b4f0a6a40b570340"
    )
    assert (
        q.query_data.hex()
        == "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000036f686d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000036574680000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    )


@pytest.mark.skip("Asks for psswd")
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
