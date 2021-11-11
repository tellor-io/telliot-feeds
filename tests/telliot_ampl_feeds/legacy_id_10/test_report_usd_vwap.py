import pytest

from telliot_ampl_feeds.feeds.usd_vwap import ampl_usd_vwap_feed
from telliot_feed_examples.reporters.interval import IntervalReporter


@pytest.mark.skip('uninvestigated error')
@pytest.mark.asyncio
async def test_uspce_reporter_submit_once(cfg, master, oracle):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""
    rinkeby_endpoint = cfg.get_endpoint()

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[ampl_usd_vwap_feed],
    )

    tx_receipts = await reporter.report_once()

    assert tx_receipts is not None

    for receipt in tx_receipts:
        assert isinstance(receipt, tuple)
        assert receipt[0].to == oracle.address
