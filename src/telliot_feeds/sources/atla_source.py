from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class atlaHelperService(WebPriceService):
    """Service to set ATLA to $1 for internal telliot functionality"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "ATLA $1 Price Service"
        kwargs["url"] = ""
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Get $1 price for ATLA (which hasn't launched yet on mainnet)"""

        asset = asset.lower()
        currency = currency.lower()

        if currency != "usd":
            logger.error("ATLA price service only works for usd")
            return None, None

        if asset != "atla":
            logger.error("this feed can only be used with an asset name of atla")
            return None, None

        return 1.00, datetime_now_utc()


@dataclass
class atlaMockSource(PriceSource):
    """ "Get $1 price for ATLA (which is free)"""

    asset: str = "atla"
    currency: str = "usd"
    service: atlaHelperService = field(default_factory=atlaHelperService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = atlaMockSource(asset="atla", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
