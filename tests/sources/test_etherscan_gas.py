from unittest import mock

import pytest
import requests

from telliot_feeds.sources.etherscan_gas import EtherscanGasPrice
from telliot_feeds.sources.etherscan_gas import EtherscanGasPriceSource


@pytest.mark.asyncio
async def test_etherscan_gas():
    c = EtherscanGasPriceSource()
    result = await c.fetch_new_datapoint()
    assert isinstance(result[0], EtherscanGasPrice)


@pytest.mark.asyncio
async def test_etherscan_gas_error(caplog):
    def conn_timeout(url, *args, **kwargs):
        raise requests.exceptions.ConnectTimeout()

    with mock.patch("requests.Session.get", side_effect=conn_timeout):
        c = EtherscanGasPriceSource()
        result = await c.fetch_new_datapoint()
        assert result[0] is None
        assert result[1] is None
        assert "Connection timeout" in caplog.text

    def json_decode_error(*args, **kwargs):
        raise requests.exceptions.JSONDecodeError("JSON decode error", "", 0)

    with mock.patch("json.loads", side_effect=json_decode_error):
        c = EtherscanGasPriceSource()
        result = await c.fetch_new_datapoint()
        assert result[0] is None
        assert result[1] is None
        assert "JSON decode error" in caplog.text

    def missing_key_rsp(url, *args, **kwargs):
        rsp = requests.Response()
        rsp.status_code = 200
        rsp._content = b'{"no_status_ke": 1}'
        return rsp

    with mock.patch("requests.Session.get", side_effect=missing_key_rsp):
        c = EtherscanGasPriceSource()
        result = await c.fetch_new_datapoint()
        assert result[0] is None
        assert result[1] is None
        assert "Key error" in caplog.text
