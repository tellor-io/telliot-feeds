from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests
from requests import Session
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

uniswapV3token0__pool_map = {
    "oeth": "0x52299416c469843f4e0d54688099966a6c7d720f",
    "primeeth": "0xb6934f4cf655c93e897514dc7c2af5a143b9ca22",
}


uniswapV3token1__pool_map = {
    "ogv": "0xa0b30e46f6aeb8f5a849241d703254bb4a719d92",
}

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class UniswapV3PoolPriceService(WebPriceService):
    """UniswapV3 Price Service for Pool Ratios"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://gateway-arbitrum.network.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface
        This implementation gets the price from the UniswapV3 subgraph using the pool query
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """
        asset = asset.lower()
        pool0 = uniswapV3token0__pool_map.get(asset, None)
        pool1 = uniswapV3token1__pool_map.get(asset, None)

        if not pool0 and not pool1:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        if pool0:
            query = "{pool" + f'(id: "{pool0}")' + "{ token0Price } }"
            key = "token0Price"

        if pool1:
            query = "{pool" + f'(id: "{pool1}")' + "{ token1Price } }"
            key = "token1Price"

        json_data = {"query": query}

        request_url = f"{self.url}/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"

        session = Session()
        if API_KEY != "":
            headers = {"Accepts": "application/json", "Authorization": f"Bearer {API_KEY}"}
            session.headers.update(headers)

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No pool prices retrieved from Uniswap")
                return None, None

            except Exception:
                logger.warning("No pool prices retrieved from Uniswap")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                token_price = float(response["data"]["pool"][key])
                return token_price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing UniswapV3 pool response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class UniswapV3PoolPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: UniswapV3PoolPriceService = field(default_factory=UniswapV3PoolPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = UniswapV3PoolPriceSource(asset="oeth", currency="eth")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
