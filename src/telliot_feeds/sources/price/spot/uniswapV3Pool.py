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
uniswapV3Pool_map = {
    "oeth": "0x52299416c469843f4e0d54688099966a6c7d720f",
}


class UniswapV3PoolPriceService(WebPriceService):
    """UniswapV3 Price Service for Pool Ratios"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://api.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the UniswapV3 subgraph using the pool query
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """

        asset = asset.lower()

        pool = uniswapV3Pool_map.get(asset, None)
        if not pool:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {
            "Content-Type": "application/json",
        }

        query = "{pool" + f'(id: "{pool}")' + "{ token0Price } }"

        json_data = {"query": query}

        request_url = self.url + "/subgraphs/name/uniswap/uniswap-v3"

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
                token_price = float(response["data"]["pool"]["token0Price"])
                return token_price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing MaverickV2 response: KeyError: {}".format(e)
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
