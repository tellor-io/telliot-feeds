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
pancakeswap_map = {
    "wbnb": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
}

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class PancakeswapPriceService(WebPriceService):
    """Pancakeswap Price Service in USD and BNB"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Pancakeswap Price Service"
        kwargs["url"] = "https://gateway-arbitrum.network.thegraph.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from a decentralized subgraph:
        https://thegraph.com/explorer/subgraphs/Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ?view=Query&chain=arbitrum-one
        """

        asset = asset.lower()

        token = pancakeswap_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        query = "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedUSD } }"

        json_data = {"query": query}

        request_url = f"{self.url}/api/subgraphs/id/Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ"

        session = Session()
        if API_KEY != "":
            headers = {"Accepts": "application/json", "Authorization": f"Bearer {API_KEY}"}
            session.headers.update(headers)
        if API_KEY == "":
            logger.warning("No Graph API key found for Uniswap prices!")

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No Uniswap prices retrieved (check thegraph api key)")
                return None, None

            except Exception as e:
                logger.warning(f"No prices retrieved from Uniswap: {e}")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        if currency.lower() == "eth":
            logger.info("Pancakeswap source is for usd pairs only")
            return None, None

        elif "response" in data:
            response = data["response"]
            logger.info(f"response: {response}")
            try:
                price = response["data"]["token"]["derivedUSD"]
                if price == 0.0:
                    msg = "Uniswap API not included, because price response is 0"
                    logger.warning(msg)
                    return None, None
                else:
                    return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing Pancakeswap response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")
        logger.info(f"price for {asset} in {currency}: {price}")
        return float(price), datetime_now_utc()


@dataclass
class PancakeswapPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PancakeswapPriceService = field(default_factory=PancakeswapPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = PancakeswapPriceSource(asset="wbnb", currency="usd")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
