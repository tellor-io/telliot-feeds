from dataclasses import dataclass
from dataclasses import field
from typing import Any
from datetime import datetime

from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger
from telliot_feed_examples.mapping.mapping import asset_mapping


logger = get_logger(__name__)
assets = asset_mapping["pancakeswap"]


class PancakeswapPriceService(WebPriceService):
    """Pancakeswap Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Pancakeswap Price Service"
        kwargs["url"] = "https://api.pancakeswap.info"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Pancakeswap API
        Pankcakeswap official Github repo for API:
        https://github.com/pancakeswap/pancake-info-api

        """

        asset = asset.lower()

        token_addr = assets.get(asset, None)

        if not token_addr:
            raise Exception("Asset not supported: {}".format(asset))

        request_url = f"/api/v2/tokens/{token_addr}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                updated = datetime.utcfromtimestamp(response["updated_at"] / 1000)
                price = response["data"]["price"]
                logger.info(f"Pancakeswap API response on {asset}: ${price}, {updated}")
            except KeyError as e:
                msg = "Error parsing Nomics API response: KeyError: {}".format(e)
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return float(price), updated


@dataclass
class PancakeswapPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PancakeswapPriceService = field(default_factory=PancakeswapPriceService,
                                             init=False)
