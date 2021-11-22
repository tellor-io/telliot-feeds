from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from pydantic import BaseModel
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource
from telliot_core.types.datapoint import datetime_now_utc
from telliot_core.types.datapoint import OptionalDataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class BittrexQuote(BaseModel):
    Bid: float
    Ask: float
    Last: float


class PriceResponse(BaseModel):
    success: bool
    message: str
    result: Optional[BittrexQuote]


class BittrexPriceService(WebPriceService):
    """Bittrex Price Service"""

    def __init__(self, **kwargs: Any):
        super().__init__(
            name="Bittrex Price Service", url="https://api.bittrex.com", **kwargs
        )

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Bittrex API

        Note that the timestamp returned form the coinbase API could be used
        instead of the locally generated timestamp.
        """

        request_url = "/api/v1.1/public/getticker?market={}-{}".format(
            currency.lower(), asset.lower()
        )

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        else:
            r = PriceResponse.parse_obj(d["response"])
            if r.success:
                if r.result is not None:
                    return r.result.Last, datetime_now_utc()
                else:
                    return None, None
            else:
                logger.error(r.message)
                return None, None


@dataclass
class BittrexPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: BittrexPriceService = field(
        default_factory=BittrexPriceService, init=False
    )
