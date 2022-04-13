import statistics
import pytest
from telliot_feed_examples.feeds.tellor_rng_feed import tellor_rng_feed
from telliot_feed_examples.sources import blockhash_aggregator
from telliot_feed_examples.sources.blockhash_aggregator import TellorRNGManualSource

@pytest.mark.asyncio
async def test_rng():
    """Retrieve random number."""
    # v, _ = await trb_usd_median_feed.source.fetch_new_datapoint()
    blockhash_aggregator.input = lambda: "1649769707"
    rng_source = TellorRNGManualSource()
    v, t = await rng_source.fetch_new_datapoint()
    # v = await tellor_rng_feed.source.fetch_new_datapoint()

    assert v == b'Ad\x81\xc2\x9d\xab\x8a\xf6\x8fN^\xcd\xb9g\xdf{\xeap\xe4\xf8\xf2\xab\x89\xcb\xb0\xe6\x8cGR\x18\xf2+'



#
# @pytest.mark.asyncio
# async def test_uspce_source():
#     """Test retrieving USPCE data from user input."""
#     # Override Python built-in input method
#     uspce.input = lambda: "1234.1234"
#
#     ampl_source = USPCESource()
#
#     value, timestamp = await ampl_source.fetch_new_datapoint()
#
#     assert isinstance(value, float)
#     assert isinstance(timestamp, datetime)
#     assert value > 0
