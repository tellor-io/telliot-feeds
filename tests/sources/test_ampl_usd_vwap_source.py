import os
from datetime import datetime

import pytest
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.sources.ampl_usd_vwap import AMPLUSDVWAPSource
from telliot_feed_examples.sources.ampl_usd_vwap import AnyBlockSource
from telliot_feed_examples.sources.ampl_usd_vwap import BraveNewCoinSource


@pytest.fixture()
def config():
    c = TelliotConfig()
    anyblock_key = c.api_keys.find("anyblock")[0].key
    rapid_key = c.api_keys.find("bravenewcoin")[0].key

    if not anyblock_key and "ANYBLOCK_KEY" in os.environ:
        anyblock_key = os.environ["ANYBLOCK_KEY"]

    if not rapid_key and "RAPID_KEY" in os.environ:
        rapid_key = os.environ["RAPID_KEY"]

    return c


@pytest.mark.asyncio
async def test_bravenewcoin_source(config):
    """Test retrieving AMPL/USD/VWAP data from BraveNewCoin/Rapid api.

    Retrieves bearer token and adds to headers of main data request."""

    api_key = config.api_keys.find("bravenewcoin")[0].key

    if api_key != "":
        ampl_source = BraveNewCoinSource(api_key=api_key)

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
    else:
        print("No BraveNewCoin api key ")


@pytest.mark.asyncio
async def test_anyblock_source(config):
    """Test retrieving AMPL/USD/VWAP data from AnyBlock api."""

    api_key = config.api_keys.find("anyblock")[0].key

    if api_key != "":
        ampl_source = AnyBlockSource(api_key=api_key)

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0
    else:
        print("No AnyBlock api key ")


@pytest.mark.asyncio
async def test_ampl_usd_vwap_source(config):
    """Test getting median updated AMPL/USD/VWAP value."""

    key1 = config.api_keys.find("anyblock")[0].key
    key2 = config.api_keys.find("bravenewcoin")[0].key
    if not all((key1, key2)):
        print("No api keys found")
    else:
        ampl_source = AMPLUSDVWAPSource(cfg=config)

        value, timestamp = await ampl_source.fetch_new_datapoint()

        assert isinstance(value, float)
        assert isinstance(timestamp, datetime)
        assert value > 0


@pytest.mark.asyncio
async def test_no_updated_value(config, bad_source):
    """Test no AMPL/USD/VWAP value retrieved."""

    ampl_source = AMPLUSDVWAPSource(cfg=config)

    # Switch source to test one that doesn't return an updated value
    ampl_source.sources = [bad_source]

    value, timestamp = await ampl_source.fetch_new_datapoint()

    assert value is None
    assert timestamp is None
