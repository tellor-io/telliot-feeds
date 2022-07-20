from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# Check supported assets here: https://www.exchangerate-api.com/docs/supported-currencies


class OpenExchangeRateCurrencyPriceService(WebPriceService):
    """OpenExchangeRate Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "OpenExchangeRate Price Service"
        kwargs["url"] = "https://open.er-api.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the OpenExchangeRate API
        using the interface described at:
        https://www.exchangerate-api.com/docs/free API

        Note that the timestamp returned form the OpenExchangeRate API could be used
        instead of the locally generated timestamp.
        """

        try:
            request_url = f"/v6/latest/{asset.upper()}"

            d = self.get_url(request_url)
            if "error" in d:
                logger.error(d)
                return None, None

            elif "response" in d:
                response = d["response"]

                if "message" in response:
                    logger.error(f"API ERROR ({self.name}): {response['message']}")
                    return None, None

            else:
                logger.error("Invalid response from get_url")
                return None, None

            price = float(response["rates"][currency.upper()])
            return price, datetime_now_utc()

        except KeyError as e:
            msg = f"Error parsing Coinbase Currency API response: KeyError: {e}"
            logger.critical(msg)
            return None, None


@dataclass
class OpenExchangeRateCurrencyPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: OpenExchangeRateCurrencyPriceService = field(
        default_factory=OpenExchangeRateCurrencyPriceService, init=False
    )
