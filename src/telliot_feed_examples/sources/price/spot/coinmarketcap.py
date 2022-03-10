# adding bct-usd price from coinmarketcap
import json
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from requests import Session
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from requests.exceptions import TooManyRedirects
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger

logger = get_logger(__name__)


API_KEY = TelliotConfig().api_keys.find(name="coinMarketCap")[0].key


class CoinMarketCapSpotPriceService(WebPriceService):
    """CoinMarketCap Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CoinMarketCap Price Service"
        kwargs["url"] = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:

        #check for api key in config
        if API_KEY == "":
            logger.warn("To use the CoinMarketCap source, add CoinMarketCap api key to ampl.yaml")
            return None, None

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {"symbol": asset.upper()}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": API_KEY,
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)

        price = data["data"][asset.upper()]["quote"][currency.upper()]["price"]
        return price, datetime_now_utc()


@dataclass
class CoinMarketCapPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinMarketCapSpotPriceService = field(
        default_factory=CoinMarketCapSpotPriceService, init=False
    )
