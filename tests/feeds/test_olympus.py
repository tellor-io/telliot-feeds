import pytest

from telliot_feed_examples.feeds.olympus import ohm_eth_median_feed
from tests.conftest import reporter_submit_once


@pytest.mark.asyncio
async def test_fetch_price():
    (value, ts) = await ohm_eth_median_feed.source.fetch_new_datapoint()
    assert value > 0
    print(value)


def test_query_info():
    q = ohm_eth_median_feed.query

    assert q.query_data == b'{"type":"SpotPrice","asset":"ohm","currency":"eth"}'
    assert (
        q.query_id.hex()
        == "0136f215d1f75daabc0c0726ad4356debeb9bc95b24344165145a56684995966"
    )
    assert (
        q.query_data.hex() == "7b2274797065223a2253706f745072696365222c2261"
        "73736574223a226f686d222c2263757272656e6379223a22657468227d"
    )


@pytest.mark.skip("Fails when reporter is in lock")
@pytest.mark.asyncio
async def test_ohm_eth_reporter_submit_once(rinkeby_core):
    """Test reporting AMPL/USD/VWAP to the TellorX Oracle on Rinkeby."""

    await reporter_submit_once(rinkeby_core, ohm_eth_median_feed)
