import pytest

from telliot_feed_examples.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed
from tests.conftest import reporter_submit_once


@pytest.mark.asyncio
async def test_uspce_reporter_submit_once(rinkeby_cfg, master, oracle):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""

    await reporter_submit_once(rinkeby_cfg, master, oracle, ampl_usd_vwap_feed)
