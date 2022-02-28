from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.mapping.mapping import asset_mapping
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

assets = asset_mapping


class UniswapV3PriceService(WebPriceService):
    """UniswapV3 Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://api.thegraph.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the UniswapV3 subgraph

        """

        asset = asset.lower()

        token = assets["uniswapV3"].get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {
            "Content-Type": "application/json",
        }

        query = (
            "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedETH } }"
        )

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
                ethprice = float(response["data"]["bundles"][0]["ethPriceUSD"])
                token_data = response["data"]["token"]["derivedETH"]
                token_price = token_data if asset != "eth" else 1
                price = ethprice * float(token_price)
                logger.info(f"Uniswap subgraph report on {asset}: ${price}")
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
    service: UniswapV3PriceService = field(
        default_factory=UniswapV3PriceService, init=False
    )
