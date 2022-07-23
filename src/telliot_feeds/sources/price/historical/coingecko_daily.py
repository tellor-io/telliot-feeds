from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Dict
from typing import List
from urllib.parse import urlencode
import pandas as pd
import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


# Hardcoded supported assets & currencies
coingecko_asset_id = {"eth": "ethereum"}
coingecko_supported_currencies = {"usd"}


class CoingeckoDailyHistoricalPriceService(WebPriceService):
    """Coingecko Historical Price Service, default is daily for 30 days"""

    def __init__(
        self,
        days: int,
        timeout: float = 0.5,
        name: str = "Coingecko Historical Price Service",
        url: str = "https://api.coingecko.com",
    ):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.days = days

    def get_url(self, url: str = "") -> dict[str, Any]:
        """Helper function to get URL JSON response while handling exceptions

        Args:
            url: URL to fetch

        Returns:
            A dictionary with the following (optional) keys:
                json (dict or list): Result, if no error occurred
                error (str): A description of the error, if one occurred
                exception (Exception): The exception, if one occurred
        """

        request_url = self.url + url

        with requests.Session() as s:
            try:
                r = s.get(request_url, timeout=self.timeout)
                json_data = r.json()
                return {"response": json_data}

            except requests.exceptions.ConnectTimeout as e:
                return {"error": "Timeout Error", "exception": e}

            except Exception as e:
                return {"error": str(type(e)), "exception": e}

    def get_request_url(self, asset: str, currency: str, days: int) -> str:
        """Assemble request url.
        example_url: # https://api.coingecko.com/api/v3/coins/ethereum/market_chart?
        vs_currency=usd&days=30&interval=daily
        """
        asset = asset.lower()
        currency = currency.lower()

        if asset not in coingecko_asset_id:
            raise Exception(f"Asset not supported: {asset}")
        if currency not in coingecko_supported_currencies:
            raise Exception(f"Currency not supported: {currency}")

        url_params = urlencode({"vs_currency": currency, "days": days, "interval": "daily"})

        # Source: https://www.coingecko.com/en/api/documentation
        return f"/api/v3/coins/{coingecko_asset_id[asset]}/market_chart?{url_params}"

    def calculate_volatitlity(self, days: int, resp: Dict[str, List[float]]) -> Optional[float]:
        """Calculate volitility using pandas."""
        try:
            if len(resp["prices"]) < days + 1:
                logger.error(f"Not enough data to generate a {days} volatility index")
                return None

            prices_df = pd.DataFrame(resp["prices"])
            volatility = prices_df[1].pct_change().std()
            return float(volatility)
        except KeyError as e:
            msg = f"Error parsing Coingecko API response: KeyError: {e}"
            logger.critical(msg)
            return None

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface"""
        req_url = self.get_request_url(asset, currency, self.days)

        d = self.get_url(req_url)

        if "error" in d:
            logger.error(d)
            return None, None

        elif "response" in d:
            response = d["response"]
            volatility_index = self.calculate_volatitlity(resp=response, days=self.days)

        else:
            raise Exception("Invalid response from get_url")

        return volatility_index, datetime_now_utc()


@dataclass
class CoingeckoDailyHistoricalPriceSource(PriceSource):
    days: int = 30   # Data up to number of days ago (eg. 1,14,30,max)
    asset: str = ""
    currency: str = ""
    service: CoingeckoDailyHistoricalPriceService = CoingeckoDailyHistoricalPriceService(days=days)

    def __post_init__(self) -> None:
        self.service.days = self.days
