from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
pancakeswap_map = {
    "wbnb": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    "fuse": "0x5857c96dae9cf8511b08cb07f85753c472d36ea3",
}


class PancakeswapPriceService(WebPriceService):
    """Pancakeswap Price Service in USD and BNB"""

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

        token_addr = pancakeswap_map.get(asset, None)

        if not token_addr:
            raise Exception("Asset not supported: {}".format(asset))

        request_url = f"/api/v2/tokens/{token_addr}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]
            print(response)

            try:
                price = response["data"]["price"] if currency.lower() == "usd" else response["data"]["price_BNB"]
            except KeyError as e:
                msg = "Error parsing Pancakeswap API response: KeyError: {}".format(e)
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")
        logger.info(f"price for {asset} in {currency}: {price}")
        return float(price), datetime_now_utc()


@dataclass
class PancakeswapPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PancakeswapPriceService = field(default_factory=PancakeswapPriceService, init=False)
