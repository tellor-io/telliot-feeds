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
# Add contract addresses for new assets to uniV3Optimism_map.
# Test that values work as expected before using this source in production!
uniV3Optimism_map = {
    "op": "0x4200000000000000000000000000000000000042",
}

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class UniV3OptimismPriceService(WebPriceService):
    """Uniswap V3 on Optimism Price Service in USD and ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Uniswap V3 on Optimism Price Service"
        kwargs["url"] = "https://gateway-arbitrum.network.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Uniswap V3 on Optimism subgraph
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """

        asset = asset.lower()

        token = uniV3Optimism_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        query = "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = f"{self.url}/api/subgraphs/id/Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj"

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
                msg = "Error parsing Uniswap V3 on Optimism response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class UniV3OptimismPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: UniV3OptimismPriceService = field(default_factory=UniV3OptimismPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = UniV3OptimismPriceSource(asset="reth", currency="eth")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
