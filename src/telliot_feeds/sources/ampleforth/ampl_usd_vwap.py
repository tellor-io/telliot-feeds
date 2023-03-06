import asyncio
import datetime
import statistics
import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar

import requests
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.sources.ampleforth.bitfinex import get_value_from_bitfinex
from telliot_feeds.sources.ampleforth.symbols import SYMBOLS
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
T = TypeVar("T")


def get_yesterday_start_end() -> Tuple[datetime.datetime, datetime.datetime]:
    """Get start and end times of yesterday in UTC."""
    today = datetime.datetime.utcnow().date()
    yesterday_date = today - datetime.timedelta(days=1)
    yesterday_start = datetime.datetime(year=yesterday_date.year, month=yesterday_date.month, day=yesterday_date.day)
    yesterday_end = datetime.datetime.combine(yesterday_start, datetime.time.max)
    return yesterday_start, yesterday_end


def to_unix_milli(dt: datetime.datetime) -> int:
    """Convert datetime to UNIX milliseconds."""
    return int(time.mktime(dt.timetuple()) * 1000)


async def get_float_from_api(
    url: str,
    params: Sequence[Any],
    headers: Optional[dict[str, str]] = None,
) -> OptionalDataPoint[float]:
    """Helper function for retrieving datapoint values."""

    with requests.Session() as s:
        try:
            r = None
            if headers:
                r = s.get(url, headers=headers)
            else:
                r = s.get(url)
            data = r.json()

            for param in params:
                data = data[param]

            timestamp = datetime_now_utc()
            datapoint = (data, timestamp)

            return datapoint

        except requests.exceptions.ConnectTimeout:
            return (None, None)

        except Exception:
            return (None, None)


@dataclass
class BitfinexSource(DataSource[float]):
    """Data source for retrieving AMPL/USD VWAP from Bitfinex API."""

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value."""

        yesterday_start, yesterday_end = get_yesterday_start_end()
        start_milli = to_unix_milli(yesterday_start)
        end_milli = to_unix_milli(yesterday_end)

        try:
            dict_rsp = await get_value_from_bitfinex(SYMBOLS["AMPL_USD_via_ALL"], start_milli, end_milli, True)
        except Exception as e:
            logger.error(f"Error getting VWAP from Bitfinex: {e}")
            return (None, None)

        if dict_rsp is None:
            logger.warning("No response from Bitfinex")
            return (None, None)

        try:
            v = float(dict_rsp["overall_vwap"])
        except Exception as e:
            logger.error(f"Error parsing VWAP from Bitfinex: {e}")
            return (None, None)

        t = datetime_now_utc()
        if v is not None and t is not None:
            self.store_datapoint((v, t))

        return (v, t)


@dataclass
class BraveNewCoinSource(DataSource[float]):
    """Data source for retrieving AMPL/USD/VWAP from
    bravenewcoin api."""

    api_key: str = ""

    async def get_bearer_token(self) -> Tuple[Optional[str], ResponseStatus]:
        """Get authorization token for using bravenewcoin api."""

        with requests.Session() as s:
            try:
                url = "https://bravenewcoin.p.rapidapi.com/oauth/token"

                payload = """{\r
                    \"audience\": \"https://api.bravenewcoin.com\",\r
                    \"client_id\": \"oCdQoZoI96ERE9HY3sQ7JmbACfBf55RY\",\r
                    \"grant_type\": \"client_credentials\"\r
                }"""
                headers = {
                    "content-type": "application/json",
                    "x-rapidapi-host": "bravenewcoin.p.rapidapi.com",
                    "x-rapidapi-key": self.api_key,
                }

                response = s.post(url, data=payload, headers=headers)

                bearer_token = response.json()["access_token"]

                return bearer_token, ResponseStatus()

            except requests.exceptions.ConnectTimeout as e:
                msg = "Timeout Error"
                return None, ResponseStatus(ok=False, error=msg, e=e)

            except Exception as e:
                return None, ResponseStatus(ok=False, error=str(type(e)), e=e)

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value."""

        access_token, status = await self.get_bearer_token()

        if not status.ok:
            return (None, None)

        url = (
            "https://bravenewcoin.p.rapidapi.com/ohlcv?"
            + "size=1&indexId=551cdbbe-2a97-4af8-b6bc-3254210ed021&indexType=GWA"
        )
        params = ["content", 0, "vwap"]

        headers = {
            "authorization": f"Bearer {access_token}",
            "x-rapidapi-host": "bravenewcoin.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
        }

        datapoint = await get_float_from_api(url=url, params=params, headers=headers)

        v, t = datapoint
        if v is not None and t is not None:
            self.store_datapoint((v, t))

        return datapoint


@dataclass
class AmpleforthCustomSpotPriceSource(DataSource[float]):
    #: Asset
    asset: str = "ampl"

    #: Currency of returned price
    currency: str = "usd"

    #: Data sources
    sources: List[DataSource[float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        keys = TelliotConfig().api_keys
        self.sources = [
            BitfinexSource(),
            BraveNewCoinSource(api_key=keys.find("bravenewcoin")[0].key),
        ]

    async def update_sources(self) -> List[OptionalDataPoint[float]]:
        """Update data feed sources

        Returns:
            Dictionary of updated source values, mapping data source UID
            to the time-stamped answer for that data source
        """

        sources = self.sources
        datapoints = await asyncio.gather(*[source.fetch_new_datapoint() for source in sources])
        return datapoints

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from source

        Args:
            store:  If true and applicable, updated value will be stored
                    to the database

        Returns:
            Current time-stamped value
        """
        updates = await self.update_sources()

        prices = [v for v, _ in updates if v is not None]

        if not prices:
            logger.warning("No prices retrieved for AMPL/USD/VWAP Source.")
            return None, None

        logger.info(f"Nubmer of sources used for AMPL/USD VWAP: {len(prices)}")
        # Get median price
        result = statistics.median(prices)
        datapoint = (result, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info("AMPL/USD VWAP {} retrieved at time {}".format(datapoint[0], datapoint[1]))

        return datapoint
