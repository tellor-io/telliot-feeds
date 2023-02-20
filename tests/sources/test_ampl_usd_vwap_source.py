import os
from datetime import datetime

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.sources.ampleforth.ampl_usd_vwap import AmpleforthCustomSpotPriceSource
from telliot_feeds.sources.ampleforth.ampl_usd_vwap import BitfinexSource
from telliot_feeds.sources.ampleforth.ampl_usd_vwap import BraveNewCoinSource


@pytest.fixture(scope="module")
def keys_dict():
    keys = TelliotConfig().api_keys
    rapid_key = keys.find("bravenewcoin")[0].key

    if not rapid_key and "RAPID_KEY" in os.environ:
        rapid_key = os.environ["RAPID_KEY"]

    return {"bravenewcoin": rapid_key}


@pytest.mark.asyncio
async def test_bitfinex_source():
    """Test retrieving AMPL/USD/VWAP data from Bitfinex."""

    bitfinex_src = AmpleforthCustomSpotPriceSource().sources[0]
    assert isinstance(bitfinex_src, BitfinexSource)

    value, timestamp = await bitfinex_src.fetch_new_datapoint()

    print("Bitfinex VWAP:", value)

    assert isinstance(value, float)
    assert isinstance(timestamp, datetime)
    assert 0 < value < 2


@pytest.mark.asyncio
async def test_bravenewcoin_source(keys_dict):
    """Test retrieving AMPL/USD/VWAP data from BraveNewCoin/Rapid api.

    Retrieves bearer token and adds to headers of main data request."""
    brave_src = AmpleforthCustomSpotPriceSource().sources[1]
    assert isinstance(brave_src, BraveNewCoinSource)

    if keys_dict["bravenewcoin"]:
        ampl_source = BraveNewCoinSource(api_key=keys_dict["bravenewcoin"])

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
    else:
        print("No BraveNewCoin api key ")


@pytest.mark.asyncio
async def test_ampl_usd_vwap_source(keys_dict):
    """Test getting median updated AMPL/USD/VWAP value."""

    if not all(keys_dict.values()):
        print("No api keys found")
    else:
        ampl_source = AmpleforthCustomSpotPriceSource()
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
