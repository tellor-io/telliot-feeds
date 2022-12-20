from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import urlencode

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

# Coinbase API uses the 'id' field from /coins/list.
# Using a manual mapping for now.
nomics_coin_id = {"bct": "BCT5", "btc": "BTC", "ric": "RIC4", "idle": "IDLE", "albt": "ALBT"}

API_KEY = TelliotConfig().api_keys.find(name="nomics")[0].key


class NomicsSpotPriceService(WebPriceService):
    """Nomics Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Nomics Price Service"
        kwargs["url"] = "https://api.nomics.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Nomics API

        """

        if API_KEY == "":
            logger.warning("To use the nomics source, add nomics api key to api_keys.yaml")
            return None, None

        asset = asset.lower()
        currency = currency.upper()

        coin_id = nomics_coin_id.get(asset, None)
        if not coin_id:
            raise Exception("Asset not supported: {}".format(asset))

        url_params = urlencode(
            {
                "key": API_KEY,
                "ids": coin_id.upper(),
                "interval": "1d",
                "convert": currency,
                "per-page": 100,
            }
        )
        request_url = "/v1/currencies/ticker?{}".format(url_params)
        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[0]["price"])
            except KeyError as e:
                msg = "Error parsing Nomics API response: KeyError: {}".format(e)
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class NomicsSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: NomicsSpotPriceService = field(default_factory=NomicsSpotPriceService, init=False)
