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
kim_map = {
    "mode": "0xdfc7c877a950e49d2610114102175a06c2e3167a",
}


class kimexchangePriceService(WebPriceService):
    """Kim exchange Price Service in USD and ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Kim exchange subgraph"
        kwargs["url"] = "https://api.goldsky.com/api/public"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Kim exchange subgraph
        https://api.goldsky.com/api/public/project_clmqdcfcs3f6d2ptj3yp05ndz/subgraphs/Algebra/0.0.1/gn
        """

        asset = asset.lower()

        token = kim_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {
            "Content-Type": "application/json",
        }

        query = "{bundles{maticPriceUSD}token" + f'(id: "{token}")' + "{ derivedMatic } }"

        json_data = {"query": query}

        request_url = self.url + "/project_clmqdcfcs3f6d2ptj3yp05ndz/subgraphs/Algebra/0.0.1/gn"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from Kim exchange")
                return None, None

            except Exception:
                logger.warning("No prices retrieved from kim exchange")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                token_price_eth = float(response["data"]["token"]["derivedMatic"])
                eth_price_usd = float(response["data"]["bundles"][0]["maticPriceUSD"])
                token_price = token_price_eth * eth_price_usd
                return token_price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing MaverickV2 response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class kimexchangePriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: kimexchangePriceService = field(default_factory=kimexchangePriceService, init=False)
