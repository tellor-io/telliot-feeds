import os
from datetime import datetime

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.sources.ampl_usd_vwap import AmpleforthCustomSpotPriceSource
from telliot_feeds.sources.ampl_usd_vwap import AnyBlockSource
from telliot_feeds.sources.ampl_usd_vwap import BraveNewCoinSource


@pytest.fixture(scope="module")
def keys_dict():
    keys = TelliotConfig().api_keys
    anyblock_key = keys.find("anyblock")[0].key
    rapid_key = keys.find("bravenewcoin")[0].key

    if not anyblock_key and "ANYBLOCK_KEY" in os.environ:
        anyblock_key = os.environ["ANYBLOCK_KEY"]

    if not rapid_key and "RAPID_KEY" in os.environ:
        rapid_key = os.environ["RAPID_KEY"]

    return {"anyblock": anyblock_key, "bravenewcoin": rapid_key}


@pytest.mark.asyncio
async def test_bravenewcoin_source(keys_dict):
    """Test retrieving AMPL/USD/VWAP data from BraveNewCoin/Rapid api.

    Retrieves bearer token and adds to headers of main data request."""

    if keys_dict["bravenewcoin"]:
        ampl_source = BraveNewCoinSource(api_key=keys_dict["bravenewcoin"])

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
    else:
        print("No BraveNewCoin api key ")


@pytest.mark.asyncio
async def test_anyblock_source(keys_dict):
    """Test retrieving AMPL/USD/VWAP data from AnyBlock api."""
    api_key = keys_dict["anyblock"]

    if api_key != "":
        ampl_source = AnyBlockSource(api_key=api_key)

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
    else:
        print("No AnyBlock api key ")


@pytest.mark.asyncio
async def test_ampl_usd_vwap_source(keys_dict):
    """Test getting median updated AMPL/USD/VWAP value."""

    if not all(keys_dict.values()):
        print("No api keys found")
    else:
        ampl_source = AmpleforthCustomSpotPriceSource()
        ampl_source.sources[0].api_key = keys_dict["anyblock"]
        ampl_source.sources[1].api_key = keys_dict["bravenewcoin"]

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0


@pytest.mark.asyncio
async def test_no_updated_value(bad_datasource):
    """Test no AMPL/USD/VWAP value retrieved."""

    ampl_source = AmpleforthCustomSpotPriceSource()

    # Switch source to test one that doesn't return an updated value
    ampl_source.sources = [bad_datasource]

    value, timestamp = await ampl_source.fetch_new_datapoint()

    assert value is None
    assert timestamp is None
