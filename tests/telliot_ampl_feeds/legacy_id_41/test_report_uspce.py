import pytest

from telliot_ampl_feeds.feeds.uspce import uspce_feed
from telliot_ampl_feeds.sources import uspce
from telliot_feed_examples.reporters.interval import IntervalReporter


@pytest.mark.asyncio
async def test_uspce_reporter_submit_once(cfg, master, oracle):
    """Test reporting manual data to the TellorX Oracle on Rinkeby."""
    # Override Python built-in input method
    uspce.input = lambda: "123.456"

    rinkeby_endpoint = cfg.get_endpoint()

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[uspce_feed],
    )

    tx_receipts = await reporter.report_once()

    assert tx_receipts is not None

    for receipt in tx_receipts:
        assert isinstance(receipt, tuple)
        assert receipt[0].to == oracle.address
