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
pulsechain_subgraph_supporten_tokens = {"pls": "0x8a810ea8b121d08342e9e7696f4a9915cbe494b7"}


class PulsechainSupgraphService(WebPriceService):
    """Pulsechain Supgraph Price Service for PLS/USD feed"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Pulsechain Supgraph Price Service"
        kwargs["url"] = "https://graph.v2b.testnet.pulsechain.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Pulsechain hosted subgraphs

        """

        asset = asset.lower()
        currency = currency.lower()

        if currency != "usd":
            logger.error(f"Currency not supported: {currency}")
            return None, None

        token = pulsechain_subgraph_supporten_tokens.get(asset, None)
        if not token:
            logger.error(f"Asset not supported: {asset}")
            return None, None

        headers = {
            "Content-Type": "application/json",
        }

        query = "{pls: token" + f'(id: "{token}") {{ derivedUSD }}' + " }"

        json_data = {
            "query": query,
            "variables": None,
            "operationName": None,
        }

        request_url = self.url + "/subgraphs/name/pulsechain/pulsex"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from Pulsechain Supgraph")
                return None, None

            except Exception as e:
                logger.warning(f"No prices retrieved from Pulsechain Supgraph with Exception {e}")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                price = float(response["data"][asset]["derivedUSD"])
                return price, datetime_now_utc()
            except KeyError as e:
                msg = f"Error parsing Pulsechain Supgraph response: KeyError: {e}"
                logger.critical(msg)
                return None, None

        else:
            logger.error("Invalid response from get_url")
            return None, None


@dataclass
class PulsechainSubgraphSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PulsechainSupgraphService = field(default_factory=PulsechainSupgraphService, init=False)
