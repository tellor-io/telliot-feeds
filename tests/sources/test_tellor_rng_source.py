from datetime import datetime
from unittest import mock

import pytest
import requests

from telliot_feeds.sources.blockhash_aggregator import get_btc_hash
from telliot_feeds.sources.blockhash_aggregator import get_eth_hash
from telliot_feeds.sources.blockhash_aggregator import get_mainnet_web3
from telliot_feeds.sources.blockhash_aggregator import TellorRNGManualSource


@pytest.mark.asyncio
async def test_rng():
    """Retrieve random number."""
    # "1652075943"  # BCT block num: 731547
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["1652075943", ""]):
        rng_source = TellorRNGManualSource()
        v, t = await rng_source.fetch_new_datapoint()

        assert v == b"\x9diF\xd9R\xf1>q%\x13F\x11\xad\x9f]\xccA\x08\xd9\x03Y\xb0#\x94\xd8\xefgi\xcc\x85t\xb3"

        assert isinstance(v, bytes)
        assert isinstance(t, datetime)


def test_no_mainnet_endpoint():
    with mock.patch("telliot_core.apps.telliot_config.TelliotConfig.get_endpoint", side_effect=ValueError):
        w3 = get_mainnet_web3()
        assert w3 is None


@pytest.mark.asyncio
async def test_no_mainnet_configured(caplog, monkeypatch):
    """Test that no eth blockhash is fetched if no mainnet endpoint is configured."""
    monkeypatch.setattr("telliot_feeds.sources.blockhash_aggregator.get_mainnet_web3", lambda: None)
    v = await get_eth_hash(0)
    assert v is None
    assert "Web3 not connected" in caplog.text


@pytest.mark.asyncio
async def test_rng_failures(caplog):
    """Simulate API failures."""
    timestamp = 1649769707

    def conn_timeout(url, *args, **kwargs):
        raise requests.exceptions.ConnectTimeout()

    with mock.patch("requests.Session.get", side_effect=conn_timeout):
        for hash_source in [
            get_eth_hash,
        ]:
            h = await hash_source(timestamp)
            assert h is None
            assert "Connection timeout" in caplog.text
        for hash_source in [
            get_btc_hash,
        ]:
            h, j = await hash_source(timestamp)
            assert h is None
            assert "Connection timeout" in caplog.text

    def bad_json(url, *args, **kwargs):
        rsp = requests.Response()
        rsp.status_code = 200
        rsp.data = "<!DOCTYPE html>"
        return rsp

    with mock.patch("requests.Session.get", side_effect=bad_json):
        for hash_source in [
            get_eth_hash,
        ]:
            h = await hash_source(timestamp)
            assert h is None
            assert "invalid JSON" in caplog.text
        for hash_source in [
            get_btc_hash,
        ]:
            h, j = await hash_source(timestamp)
            assert h is None
            assert "invalid JSON" in caplog.text

    def bad_block_num(url, *args, **kwargs):
        rsp = requests.Response()
        rsp.status_code = 200
        rsp.json = lambda: {"status": "1", "result": "not an int"}
        return rsp

    with mock.patch("requests.Session.get", side_effect=bad_block_num):
        for hash_source in [
            get_eth_hash,
        ]:
            h = await hash_source(timestamp)
            assert h is None
            assert "invalid block number" in caplog.text
