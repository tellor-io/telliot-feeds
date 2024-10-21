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


API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class pancakePoolPriceService(WebPriceService):
    """PancakeSwap Price Service for Pool Ratios"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "PancakeSwap Price Service"
        kwargs["url"] = "https://gateway-arbitrum.network.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface
        This implementation gets the price from the PancakeSwap subgraph using the pool query
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        graphql_query = """
        {
        pool(id: "0x5a5ca75147550079411f6f543b729a4beab4dfeb") {
            token0Price
            token1 {
            derivedUSD
            }
        }
        }
        """

        json_data = {"query": graphql_query}
        request_url = f"{self.url}/api/subgraphs/id/Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ"

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
            response_data = data["response"]
            try:
                pool_data = response_data["data"]["pool"]
                token0_price = pool_data["token0Price"]
                solvbtc_usd_price = pool_data["token1"]["derivedUSD"]
                token_price = float(token0_price) * float(solvbtc_usd_price)
                return token_price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing Pancake pool response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class pancakePoolPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: pancakePoolPriceService = field(default_factory=pancakePoolPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = pancakePoolPriceSource(asset="solvbtcbbn", currency="usd")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
