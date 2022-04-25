from datetime import datetime

import pytest

from telliot_feed_examples.sources import blockhash_aggregator
from telliot_feed_examples.sources.blockhash_aggregator import TellorRNGManualSource


@pytest.mark.asyncio
async def test_rng():
    """Retrieve random number."""
    blockhash_aggregator.input = lambda: "1649769707"
    rng_source = TellorRNGManualSource()
    v, t = await rng_source.fetch_new_datapoint()

    assert v == (
        b"Ad\x81\xc2\x9d\xab\x8a\xf6\x8fN^\xcd\xb9g\xdf{"
        b"\xeap\xe4\xf8\xf2\xab\x89\xcb\xb0\xe6\x8cGR\x18\xf2+"
    )

    assert isinstance(v, bytes)
    assert isinstance(t, datetime)

@pytest.mark.asyncio
async def test_rng_btc_source_error():
    """Retrieve random number."""
    blockhash_aggregator.input = lambda: "1649769707"
    
    rng_source = TellorRNGManualSource()
    v, t = await rng_source.fetch_new_datapoint()

    assert v == (
        b"Ad\x81\xc2\x9d\xab\x8a\xf6\x8fN^\xcd\xb9g\xdf{"
        b"\xeap\xe4\xf8\xf2\xab\x89\xcb\xb0\xe6\x8cGR\x18\xf2+"
    )

    assert isinstance(v, bytes)
    assert isinstance(t, datetime)