#adding bct-usd price from coinmarketcap

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger

logger = get_logger(__name__)


# Check supported assets here: https://api.exchange.coinbase.com/products

class CoinMarketCapPriceService(WebPriceService):
    """CoinMarketCap Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CoinMarketCap Price Service"
        kwargs["url"] = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        super().__init__(**kwargs)

    async def get_price(self, symbol: str, key: str) -> OptionalDataPoint[float]:

        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        parameters = {
            'symbol': symbol
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': key,
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            # print(data)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)

        price = data['data']['BCT']['quote']['USD']['price']
        return price, datetime_now_utc()




@dataclass
class CoinMarketCapPriceSource(PriceSource):
    symbol: str = ""
    key: str = ""
    service: CoinMarketCapPriceService = field(
        default_factory=CoinMarketCapPriceService, init=False
    )
