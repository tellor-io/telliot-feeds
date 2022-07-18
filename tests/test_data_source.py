""" Unit tests for data source module

"""
from datetime import datetime

import pytest

from telliot_feeds.datasource import RandomSource


@pytest.mark.asyncio
async def test_random_source():
    """Test the random source example"""
    s = RandomSource()

    assert s.latest == (None, None)

    v, t = await s.fetch_new_datapoint()
    assert isinstance(v, float)
    assert 0 <= v < 1
    assert isinstance(t, datetime)

    v, t = await s.fetch_new_datapoint()

    assert s.depth == 2

    latest_values = s.get_all_datapoints()
    assert len(latest_values) == 2
