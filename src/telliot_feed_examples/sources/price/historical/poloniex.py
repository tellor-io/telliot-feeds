from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import urlencode

from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.dtypes.datapoint import OptionalDataPoint
from telliot_core.pricing.price_service import WebPriceService
from telliot_core.pricing.price_source import PriceSource

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported assets/urrencies pairs
poloniex_pairs = {"DAI_ETH", "TUSD_ETH"}


class PoloniexHistoricalPriceService(WebPriceService):
    """Poloniex Historical Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Poloniex Historical Price Service"
        kwargs["url"] = "https://poloniex.com/"
        super().__init__(**kwargs)

    async def get_price(
        self, asset: str, currency: str, ts: int
    ) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the historical price from
        the Poloniex API using a timestamp."""

        asset = asset.upper()
        currency = currency.upper()
        pair = asset + "_" + currency

        if pair not in poloniex_pairs:
            raise Exception(f"Currency pair not supported: {pair}")

        url_params = urlencode(
            {
                "currencyPair": pair,
                "start": ts - 1e4,
                "end": ts + 1e4,
            }
        )

        # Source: https://docs.Poloniex.com/rest/#operation/getRecentTrades
        request_url = f"public?command=returnTradeHistory&{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[0]["rate"])
            except KeyError as e:
                msg = f"Error parsing Poloniex API response: KeyError: {e}"
                logger.critical(msg)

        else:
            raise Exception("Invalid response from get_url")

        return price, datetime_now_utc()


@dataclass
class PoloniexHistoricalPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PoloniexHistoricalPriceService = field(
        default_factory=PoloniexHistoricalPriceService, init=False
    )
