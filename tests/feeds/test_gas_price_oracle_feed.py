from datetime import datetime

import pytest

from telliot_feeds.feeds.gas_price_oracle_feed import gas_price_oracle_feed


@pytest.mark.asyncio
async def test_fetch_new_datapoint(caplog):
    """Retrieve historical gas price data from source."""

    gas_price_oracle_feed.source.chainId = 1
    gas_price_oracle_feed.source.timestamp = 1655232127

    v, t = await gas_price_oracle_feed.source.fetch_new_datapoint()

    if (v is None) and (t is None):
        assert "Max retries exceeded with url" in caplog.text

    else:
        assert isinstance(v, float)
        assert isinstance(t, datetime)
