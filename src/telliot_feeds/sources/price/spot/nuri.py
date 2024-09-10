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

# use the pool address here if token0
nuri_token0__pool_map = {
    "stone": "0x97a90e651b0a5cf76484513469249d9bffe4c73b",
}

# use the pool address here if token1
nuri_token1__pool_map = {
    "weth": "0x5300000000000000000000000000000000000004",
}

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class nuriPriceService(WebPriceService):
    """nuri Price Service for Pool Ratios"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Nuri Price Service"
        kwargs["url"] = "https://gateway.thegraph.com/api"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface
        This implementation gets the price from the Nuri subgraph using the pool query
        """
        asset = asset.lower()
        currency = currency.lower()
        pool0 = nuri_token0__pool_map.get(asset, None)
        pool1 = nuri_token1__pool_map.get(asset, None)

        if not pool0 and not pool1:
            raise Exception("Asset not supported: {}".format(asset))

        if pool0:
            query = "{bundles{ethPriceUSD}pool" + f'(id: "{pool0}")' + "{ token0Price } }"
            key = "token0Price"

        if pool1:
            query = "{bundles{ethPriceUSD}pool" + f'(id: "{pool1}")' + "{ token1Price } }"
            key = "token1Price"

        headers = {
            "Content-Type": "application/json",
        }

        json_data = {"query": query}

        request_url = f"{self.url}/subgraphs/id/Eqr2CueSusTohoTsXCiQgQbaApjuK2ikFvpqkVTPo1y5"
        logger.info(f"{request_url}")

        session = Session()
        if API_KEY != "":
            headers = {"Accepts": "application/json", "Authorization": f"Bearer {API_KEY}"}
            session.headers.update(headers)

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}
                logger.info(f"{data}")

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No pool prices retrieved from Nuri")
                return None, None

            except Exception:
                logger.warning("No pool prices retrieved from Nuri")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]
            eth_usd_price = None
            token_price = None
            try:
                eth_usd_price = float(response["data"]["bundles"][0]["ethPriceUSD"])
                logger.info(f"eth price: {eth_usd_price}")
                if currency == "usd":
                    token_price = (float(response["data"]["pool"][key])) * eth_usd_price
                elif currency == "eth":
                    vs_eth_usd_price = (float(response["data"]["pool"][key])) * eth_usd_price
                    token_price = vs_eth_usd_price / eth_usd_price
                return token_price, datetime_now_utc()

                if not token_price:
                    logger.error("Nuri was reached, but query failed! (check source)")
                    return None, None

            except KeyError as e:
                msg = "Error parsing Nuri pool response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class nuriSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: nuriPriceService = field(default_factory=nuriPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = nuriSpotPriceSource(asset="stone", currency="usd")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
