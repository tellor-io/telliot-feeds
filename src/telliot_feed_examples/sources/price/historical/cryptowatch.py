from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional
from urllib.parse import urlencode

from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported asset/currency pairs
CRYPTOWATCH_PAIRS = {"ethusd"}


class CryptowatchHistoricalPriceService(WebPriceService):
    """Cryptowatch Historical Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Cryptowatch Historical Price Service"
        kwargs["url"] = "https://api.cryptowat.ch/"
        super().__init__(**kwargs)

    async def get_price(
        self, asset: str, currency: str, ts: Optional[int]
    ) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Cryptowatch API using a timestamp. Historical prices are
        fetched from Cryptowatch's recorded Coinbase-pro data.

        Documentation for Cryptowatch API:
        https://docs.cryptowat.ch/rest-api/markets/ohlc
        """
        if ts is None:
            ts = self.ts

        asset = asset.lower()
        currency = currency.lower()
        pair = asset + currency

        if pair not in CRYPTOWATCH_PAIRS:
            raise Exception(f"Currency pair not supported: {pair}")

        periods = 1800  # 30min
        url_params = urlencode(
            {"after": int(ts - 1e4), "before": ts, "periods": periods}
        )

        request_url = f"markets/coinbase-pro/{pair}/ohlc?{url_params}"

        d = self.get_url(request_url)
        price = None

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response["result"][str(periods)][-1][4])
            except KeyError as e:
                msg = f"Error parsing Cryptowatch API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class CryptowatchHistoricalPriceSource(PriceSource):
    ts: int = 0
    asset: str = ""
    currency: str = ""
    service: CryptowatchHistoricalPriceService = field(
        default_factory=CryptowatchHistoricalPriceService, init=False
    )
