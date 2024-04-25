from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class sFuelSpotPriceService(WebPriceService):
    """Custom sFUEL Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "sFUEL $1 Price Service"
        kwargs["url"] = ""
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Get $1 price for sFUEL (which is free)"""

        asset = asset.lower()
        currency = currency.lower()

        if currency != "usd":
            logger.error("sfuel price service only works for usd")
            return None, None

        if asset != "sfuel":
            logger.error("this feed can only be used with an asset name of sfuel")
            return None, None

        return 1, None


@dataclass
class sFuelSpotPriceSource(PriceSource):
    """ "Get $1 price for sFUEL (which is free)"""

    asset: str = "sfuel"
    currency: str = "usd"
    service: sFuelSpotPriceService = field(default_factory=sFuelSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = sFuelSpotPriceSource(asset="sfuel", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

        # res = await source.service.get_total_liquidity_of_pools()
        # print(res)

    asyncio.run(main())
