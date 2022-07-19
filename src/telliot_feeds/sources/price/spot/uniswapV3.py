from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
uniswapV3_map = {
    "eth": "0x0000000000000000000000000000000000000000",
    "wbtc": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "matic": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "fuse": "0x970b9bb2c0444f5e81e9d0efb84c8ccdcdcaf84d",
}


class UniswapV3PriceService(WebPriceService):
    """UniswapV3 Price Service in USD and ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://api.thegraph.com"
        kwargs["timeout"] = 10.0
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

        query = "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = self.url + "/subgraphs/name/uniswap/uniswap-v3"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from Uniswap")
                return None, None

            except Exception:
                logger.warning("No prices retrieved from Uniswap")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                ethprice = float(response["data"]["bundles"][0]["ethPriceUSD"])
                if asset.lower() == "eth":
                    token_data = 1
                elif currency.lower() == "eth":
                    ethprice = 1
                    token_data = response["data"]["token"]["derivedETH"]
                else:
                    token_data = response["data"]["token"]["derivedETH"]
                price = ethprice * float(token_data)
                if price == 0.0:
                    msg = "Uniswap API not included, because price response is 0"
                    logger.warning(msg)
                    return None, None
                else:
                    return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing UniswapV3 response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class UniswapV3PriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: UniswapV3PriceService = field(default_factory=UniswapV3PriceService, init=False)
