"""
Tests covering the IntervalReporter class from
telliot's reporters subpackage.
"""
import pytest

from telliot_feed_examples.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter

# Tellor playground contract used for test
playground_address = "0x4699845F22CA2705449CFD532060e04abE3F1F31"


def test_reporter_config(cfg, master, oracle):
    """Test instantiating an IntervalReporter using default telliot configs."""

    rinkeby_endpoint = cfg.get_endpoint()

    _ = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[btc_usd_median_feed],
    )

    assert rinkeby_endpoint.network == "rinkeby"
    assert rinkeby_endpoint.provider
    assert rinkeby_endpoint.url

    assert rinkeby_endpoint.chain_id == 4


# @pytest.mark.skip(reason="fails sometimes.  Re-enable after contract.write integration")
@pytest.mark.asyncio
async def test_interval_reporter_submit_once(cfg, master, oracle):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""

    rinkeby_endpoint = cfg.get_endpoint()

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[btc_usd_median_feed],
    )

    tx_receipts = await reporter.report_once(
        name="BTC USD Median Price Feed", retries=3
    )

    assert tx_receipts is not None

    for receipt in tx_receipts:
        assert isinstance(receipt, tuple)
        # assert receipt[0].status == 1
        assert receipt[0].to == oracle.address


# TODO: choose datafeeds in reporters config
