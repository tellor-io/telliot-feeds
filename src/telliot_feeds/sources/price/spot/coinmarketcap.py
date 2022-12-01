import json
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from requests import Session
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from requests.exceptions import TooManyRedirects
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

coinmarketcap_assets = {"BCT", "ALBT"}
coinmarketcap_currencies = {"USD"}

API_KEY = TelliotConfig().api_keys.find(name="coinmarketcap")[0].key


class CoinMarketCapSpotPriceService(WebPriceService):
    """CoinMarketCap Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CoinMarketCap Price Service"
        kwargs["url"] = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:

        # check for api key in config
        if API_KEY == "":
            logger.warn("To use the CoinMarketCap source, add CoinMarketCap api key to ampl.yaml")
            return None, None

        asset = asset.upper()
        currency = currency.upper()

        if asset not in coinmarketcap_assets:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in coinmarketcap_currencies:
            raise Exception(f"Currency not supported: {currency}")

        request_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

        parameters = {"symbol": asset}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": API_KEY,
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(request_url, params=parameters)

            if response.status_code >= 400:
                logger.warning(f"CoinMarketCap Error Status {response.status_code}")
                return None, None

            data = json.loads(response.text)

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            logger.warning(e)
            return None, None

        try:
            price = data["data"][asset]["quote"][currency]["price"]
            return price, datetime_now_utc()
        except Exception as e:
            msg = f"Error parsing CoinMarketCap API response: Exception: {e}"
            logger.critical(msg)
            return None, None


@dataclass
class CoinMarketCapSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinMarketCapSpotPriceService = field(default_factory=CoinMarketCapSpotPriceService, init=False)
