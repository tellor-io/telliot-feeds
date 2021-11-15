import pytest

from telliot_ampl_feeds.feeds.usd_vwap import ampl_usd_vwap_feed
from tests.conftest import reporter_submit_once


# @pytest.mark.skip("uninvestigated error")
@pytest.mark.asyncio
async def test_uspce_reporter_submit_once(cfg, master, oracle):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""

    reporter_submit_once(cfg, master, oracle, ampl_usd_vwap_feed)
