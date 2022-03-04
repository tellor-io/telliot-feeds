from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)
uniswapV3_map = {
    "wbtc": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "matic": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "fuse": "0x970b9bb2c0444f5e81e9d0efb84c8ccdcdcaf84d",
}


class UniswapV3EthPriceService(WebPriceService):
    """UniswapV3 Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://api.thegraph.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the UniswapV3 subgraph
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """

        asset = asset.lower()

        token = uniswapV3_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {
            "Content-Type": "application/json",
        }

        query = "{token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = self.url + "/subgraphs/name/uniswap/uniswap-v3"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=5.0)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout as e:
                data = {"error": "Timeout Error", "exception": e}

            except Exception as e:
                data = {"error": str(type(e)), "exception": e}

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                print(response)
                token_data = response["data"]["token"]["derivedETH"]
                price = float(token_data)
                return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing UniswapV3Eth response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class UniswapV3EthPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: UniswapV3EthPriceService = field(
        default_factory=UniswapV3EthPriceService, init=False
    )
