from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict

from pydantic import BaseModel
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class GeminiPriceResponse(BaseModel):
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


class GeminiPriceService(WebPriceService):
    """Gemini Price Service"""

    def __init__(self, **kwargs: Any):
        super().__init__(
            name="Gemini Price Service", url="https://api.gemini.com", **kwargs
        )

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Bittrex API

        Note that the timestamp returned form the coinbase API could be used
        instead of the locally generated timestamp.
        """

        request_url = "/v1/pubticker/{}{}".format(asset.lower(), currency.lower())

        d = self.get_url(request_url)
        if "error" in d:
            logger.error(d)
            return None, None

        else:
            r = GeminiPriceResponse.parse_obj(d["response"])

            if r.last is not None:
                return r.last, datetime_now_utc()
            else:
                logger.error(r)
                return None, None


@dataclass
class GeminiPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: GeminiPriceService = field(default_factory=GeminiPriceService, init=False)
