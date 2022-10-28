from unittest import mock

import pytest
import requests

from telliot_feeds.pricing.price_service import WebPriceService


@pytest.mark.asyncio
async def test_webpriceservice_errors(caplog):
    """ "Test failures of WebPriceService class"""

    class FakePriceService(WebPriceService):
        """Must implement get_price or NotImplementedError will be raised"""

        async def get_price(self, asset, currency):
            return None, None

    def json_decode_error(*args, **kwargs):
        """Override get method and raise JSONDecodeError"""
        raise requests.exceptions.JSONDecodeError("JSON Decode Error", "", 0)

    with mock.patch("requests.Session.get", side_effect=json_decode_error):
        wsp = FakePriceService(name="FakePriceService", url="https://fakeurl.xyz")
        result = wsp.get_url()

        assert "error" in result
        assert "JSON Decode Error" == result["error"]
