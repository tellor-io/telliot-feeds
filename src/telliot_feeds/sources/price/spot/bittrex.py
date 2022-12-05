from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class BittrexQuote:
    Bid: float
    Ask: float
    Last: float


@dataclass
class PriceResponse:
    success: bool
    message: str
    result: Optional[BittrexQuote]


class BittrexSpotPriceService(WebPriceService):
    """Bittrex Price Service"""

    def __init__(self, **kwargs: Any):
        super().__init__(name="Bittrex Price Service", url="https://api.bittrex.com", **kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Bittrex API

        Note that the timestamp returned form the coinbase API could be used
        instead of the locally generated timestamp.
        """

        request_url = "/api/v1.1/public/getticker?market={}-{}".format(currency.lower(), asset.lower())

        d = self.get_url(request_url)

        if "error" in d:

            if "JSON Decode Error" in d["error"]:
                logger.error("Unable to decode Bittrex JSON")
                return None, None

            if "restrictions that prevent you from accessing the site" in d["exception"].strerror:
                logger.warning("Bittrex API rate limit exceeded")
                return None, None

            logger.error(d)
            return None, None

        else:
            r = PriceResponse(**d["response"])
            if r.success:
                if r.result is not None:
                    return r.result.Last, datetime_now_utc()
                else:
                    return None, None
            else:
                logger.error(r.message)
                return None, None


@dataclass
class BittrexSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BittrexSpotPriceService = field(default_factory=BittrexSpotPriceService, init=False)
