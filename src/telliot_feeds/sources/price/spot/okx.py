from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class OKXSpotPriceService(WebPriceService):
    """OKX Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "OKX Price Service"
        kwargs["url"] = "https://www.okx.com/api"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the OKX api.
        e.g. request https://www.okx.com/api/v5/market/ticker?instId=TRB-USDT
        """

        market_symbol = f"{format(asset.upper())}-{format(currency.upper())}"
        request_url = f"/v5/market/ticker?instId={market_symbol}"

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
            raise Exception("Invalid response from get_url")
        try:
            code = response.get("code")
            msg = response.get("msg") or response.get("message")
            if code is not None and str(code) != "0":
                logger.error(f"API ERROR ({self.name}): code={code} msg={msg}")
                return None, None

            data = response.get("data")
            if not data or not isinstance(data, list):
                logger.warning(f"No ticker data returned from {self.name} for request: {request_url}")
                return None, None

            first_entry = data[0]
            if not isinstance(first_entry, dict):
                logger.error(f"Unexpected ticker format from {self.name}: first entry not a dict")
                return None, None

            last_price_str = first_entry.get("last")
            if last_price_str is None:
                logger.warning(f"Missing 'last' field in ticker from {self.name} for request: {request_url}")
                return None, None

            price = float(last_price_str)
            return price, datetime_now_utc()

        except (TypeError, ValueError) as e:
            logger.error(f"Failed to parse price from {self.name} response: {e}")
            return None, None


@dataclass
class OKXSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: OKXSpotPriceService = field(default_factory=OKXSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = OKXSpotPriceSource(asset="trb", currency="usdt")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
