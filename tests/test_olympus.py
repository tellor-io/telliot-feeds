from telliot_feed_examples.olympus import ohm_eth_median_feed
import pytest
from tests.conftest import reporter_submit_once


@pytest.mark.asyncio
async def test_fetch_price():
    result = await ohm_eth_median_feed.source.fetch_new_datapoint()
    print(result)


def test_query_info():
    q = ohm_eth_median_feed.query

    assert q.query_data == b'{"type":"SpotPrice","asset":"ohm","currency":"eth"}'
    assert q.query_id.hex() == "0136f215d1f75daabc0c0726ad4356debeb9bc95b24344165145a56684995966"
    assert q.query_data.hex() == "7b2274797065223a2253706f745072696365222c226173736574223a226f686d222c2263757272656e6379223a22657468227d"


@pytest.mark.skip('temp')
@pytest.mark.asyncio
async def test_ohm_eth_reporter_submit_once(rinkeby_core):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""

    await reporter_submit_once(rinkeby_core, ohm_eth_median_feed)
