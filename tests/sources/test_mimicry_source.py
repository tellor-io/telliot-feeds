import asyncio
from unittest import mock

import aiohttp
import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.feeds.mimicry.macro_market_mashup_feed import COLLECTIONS
from telliot_feeds.feeds.mimicry.macro_market_mashup_feed import TOKENS
from telliot_feeds.sources.mimicry.collection_stat import MimicryCollectionStatSource
from telliot_feeds.sources.mimicry.mashup_source import NFTMashupSource
from telliot_feeds.sources.mimicry.nft_market_index import NFTGoSource


@pytest.mark.asyncio
async def test_fetching_collection_stat_data():
    """Test fetching data from Mimicry API"""
    # tami
    source = MimicryCollectionStatSource(
        chainId=1, collectionAddress="0x5180db8F5c931aaE63c74266b211F580155ecac8", metric=0
    )
    val, _ = await source.fetch_new_datapoint()
    print(val)
    assert isinstance(val, float)


@pytest.mark.asyncio
async def test_fetching_nft_mashup_mcap():
    """Test mimicry market cap mashup"""
    api_key = TelliotConfig().api_keys.find("nftgo")
    source = NFTMashupSource(metric="market-cap", currency="usd", collections=COLLECTIONS, tokens=TOKENS)
    val, _ = await source.fetch_new_datapoint()
    if not api_key:
        assert val is None
    else:
        assert isinstance(val, int)
        assert val > 0


@pytest.mark.asyncio
async def test_fetching_nft_index_mcap():
    """Test fetch nft market cap"""
    api_key = TelliotConfig().api_keys.find("nftgo")
    source = NFTGoSource(currency="usd")
    val, _ = await source.fetch_new_datapoint()
    if not api_key:
        assert val is None
    else:
        assert isinstance(val, float)
        assert val > 0


@pytest.mark.asyncio
async def test_aiohttp_errors(caplog):
    source = NFTMashupSource(metric="market-cap", currency="usd", collections=COLLECTIONS, tokens=TOKENS, retries=1)
    with mock.patch("aiohttp.ClientSession.get", side_effect=aiohttp.ClientError):
        result = await source.fetch_new_datapoint()

        assert result == (None, None)

    with mock.patch("aiohttp.ClientSession.get", side_effect=aiohttp.ClientConnectionError):
        result = await source.fetch_new_datapoint()

        assert result == (None, None)

    with mock.patch(
        "aiohttp.ClientSession.get",
        side_effect=aiohttp.ClientResponseError(mock.MagicMock(), mock.MagicMock(), status=500),
    ):
        result = await source.fetch_new_datapoint()

        assert result == (None, None)

    with mock.patch("aiohttp.ClientSession.get", side_effect=asyncio.exceptions.TimeoutError):
        result = await source.fetch_new_datapoint()

        assert result == (None, None)
