import datetime
from unittest.mock import patch

import pytest
from eth_abi import encode
from web3 import Web3

from telliot_feeds.feeds.landx_feed import corn
from telliot_feeds.feeds.landx_feed import rice
from telliot_feeds.feeds.landx_feed import soy
from telliot_feeds.feeds.landx_feed import wheat
from telliot_feeds.sources.landx_source import LandXSource

mock_landx_source_response = {"CORN": 231397638, "WHEAT": 251528000, "RICE": 346441008, "SOY": 534254377}


@pytest.mark.asyncio
async def test_fetch_prices():
    """Test fetching prices for LandX feeds from Landx source"""
    with patch.object(LandXSource, "fetch_commodities_prices", return_value=mock_landx_source_response):
        (value, date) = await corn.source.fetch_new_datapoint()
        assert value > 0
        assert isinstance(date, datetime.datetime)
        (value, _) = await rice.source.fetch_new_datapoint()
        assert value > 0
        assert isinstance(date, datetime.datetime)
        (value, _) = await soy.source.fetch_new_datapoint()
        assert value > 0
        assert isinstance(date, datetime.datetime)
        (value, _) = await wheat.source.fetch_new_datapoint()
        assert value > 0
        assert isinstance(date, datetime.datetime)


def test_feed_query_info():
    for feed in (corn, rice, soy, wheat):
        assert feed.query.identifier == "landx"
        assert feed.query.asset in ["corn", "rice", "soy", "wheat"]
        assert feed.query.currency == "usd"
        assert feed.query.unit == "per_kilogram"
        assert feed.query.query_id is not None
        assert isinstance(feed.query.query_id, bytes)
        assert isinstance(feed.query.query_data, bytes)
        encoded_query_params = encode(
            ["string", "string", "string", "string"],
            [feed.query.identifier, feed.query.asset, feed.query.currency, feed.query.unit],
        )
        query_data = encode(["string", "bytes"], ["CustomPrice", encoded_query_params])
        assert feed.query.query_data == query_data
        assert feed.query.query_id == Web3.keccak(query_data)
        assert feed.query.value_type.abi_type == "ufixed256x18"
