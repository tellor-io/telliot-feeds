from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coingecko import coingecko_coin_id
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceService
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.stdev_calculator import stdev_calculator


logger = get_logger(__name__)


class CoingeckoDailyHistoricalPriceService(CoinGeckoSpotPriceService):
    def __init__(self, days: int, **kwargs: Any) -> None:
        self.days = days
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Coingecko API

        Note that coingecko does not return a timestamp so one is
        locally generated.
        """

        asset = asset.lower()
        currency = currency.lower()

        coin_id = coingecko_coin_id.get(asset, None)
        if not coin_id:
            raise Exception("Asset not supported: {}".format(asset))

        url_params = urlencode({"vs_currency": currency, "days": self.days, "interval": "daily"})
        request_url = f"/api/v3/coins/{coin_id}/market_chart?{url_params}"

        d = self.get_url(request_url)

        if "error" in d:
            if "api.coingecko.com used Cloudflare to restrict access" in str(d["exception"]):
                logger.warning("CoinGecko API rate limit exceeded")
            else:
                logger.error(d)
            return None, None
        elif "response" in d:
            response = d["response"]

            if len(response["prices"]) < self.days + 1:
                logger.error(f"Not enough data to generate a {self.days} volatility index")
                return None, None

            try:
                close_prices = [float(i[1]) for i in response["prices"]]
                volatility = stdev_calculator(close_prices)
                return volatility, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing Coingecko API response: KeyError: {}".format(e)
                logger.error(msg)
                return None, None
            except Exception as e:
                logger.error(e)
                return None, None

        else:
            msg = "Invalid response from get_url"
            logger.error(msg)
            return None, None


@dataclass
class CoingeckoDailyHistoricalPriceSource(PriceSource):
    days: int = 29  # Data up to number of days ago (eg. 1,14,30,max)
    asset: str = ""
    currency: str = ""
    service: CoingeckoDailyHistoricalPriceService = CoingeckoDailyHistoricalPriceService(days=days)

    def __post_init__(self) -> None:
        self.service.days = self.days
