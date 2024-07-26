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
maverickV2_map = {
    "oeth": "0x856c4efb76c1d1ae02e20ceb03a2a6a08b0b8dc3",
}


class MaverickV2PriceService(WebPriceService):
    """maverickV2 Price Service in ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "maverickV2 Price Service"
        kwargs["url"] = "https://api.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the maverickV2 subgraph,
        which is similar to the UniswapV3 subgraph:
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """

        asset = asset.lower()

        token = maverickV2_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        if currency.lower() != "eth":
            raise Exception("Eth only: {}".format(currency))

        headers = {
            "Content-Type": "application/json",
        }

        query = "{token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = self.url + "/subgraphs/name/maverickprotocol/maverick-mainnet-app"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from MaverickV2")
                return None, None

            except Exception:
                logger.warning("No prices retrieved from MaverickV2")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                token_price = float(response["data"]["token"]["derivedETH"])
                return token_price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing MaverickV2 response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class MaverickV2PriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: MaverickV2PriceService = field(default_factory=MaverickV2PriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = MaverickV2PriceSource(asset="oeth", currency="eth")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
