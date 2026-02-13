# from datetime import datetime
import pytest

from telliot_feeds.sources.numeric_api_response import NumericApiResponseSource


# test different apis with different outputs to test parser capabilities
@pytest.mark.asyncio
async def test_jsonplaceholder_nested():
    """Test parsing nested numeric value from JSON response."""
    source = NumericApiResponseSource(
        url="https://jsonplaceholder.typicode.com/posts/1",
        parseStr="userId",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val == 1


@pytest.mark.asyncio
async def test_coingecko_btc_price():
    """Test parsing nested numeric value from CoinGecko API."""
    source = NumericApiResponseSource(
        url="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
        parseStr="bitcoin, usd",
    )
    val, _ = await source.fetch_new_datapoint()
    assert 5000 < val < 500000  # BTC price range


@pytest.mark.asyncio
async def test_empty_parse_str():
    """Test that empty parseStr returns None (can't parse to single float)."""
    source = NumericApiResponseSource(
        url="https://jsonplaceholder.typicode.com/posts/1",
        parseStr="",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val is None  # Empty parseStr means we get the whole dict, not a float


@pytest.mark.asyncio
async def test_jsonplaceholder_array():
    """Test parsing numeric value from array in JSON response."""
    source = NumericApiResponseSource(
        url="https://jsonplaceholder.typicode.com/users",
        parseStr="0, id",
    )
    val, _ = await source.fetch_new_datapoint()
    assert val == 1  # First user's ID
