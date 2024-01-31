from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class GeminiPriceResponse:
    bid: float
    ask: float
    last: float
    volume: Dict[str, Any]


# Example output
# {'bid': '46696.49',
#  'ask': '46706.28',
#  'volume':
#      {'BTC': '1478.8403795849',
#       'USD': '67545338.339627693826',
#       'timestamp': 1631636700000},
#  'last': '46703.47'}}


class GeminiSpotPriceService(WebPriceService):
    """Gemini Price Service"""

    def __init__(self, **kwargs: Any):
        super().__init__(name="Gemini Price Service", url="https://api.gemini.com", **kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Gemini API

        Note that the timestamp returned form the coinbase API could be used
        instead of the locally generated timestamp.
        """

        request_url = "/v1/pubticker/{}{}".format(asset.lower(), currency.lower())

        d = self.get_url(request_url)
        if d is None:
            logger.warning("No data returned from Gemini")
            return None, None
        elif "error" in d:
            if "used Cloudflare to restrict access" in str(d["exception"]):
                logger.warning("Gemini API rate limit exceeded")
                return None, None

            logger.error(d)
            return None, None

        else:
            try:
                r = GeminiPriceResponse(**d["response"])
            except Exception as e:
                logger.error(f"Error parsing response from Gemini API: {e}")
                return None, None

            if r.last is not None:
                return float(r.last), datetime_now_utc()
            else:
                logger.error(r)
                return None, None


@dataclass
class GeminiSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: GeminiSpotPriceService = field(default_factory=GeminiSpotPriceService, init=False)
