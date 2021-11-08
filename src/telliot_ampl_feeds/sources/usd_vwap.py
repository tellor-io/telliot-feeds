import asyncio
import statistics
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar

import requests
from telliot.datasource import DataSource
from telliot.types.datapoint import datetime_now_utc
from telliot.types.datapoint import OptionalDataPoint
from telliot.utils.response import ResponseStatus

from telliot_ampl_feeds.config import AMPLConfig


T = TypeVar("T")


async def get_float_from_api(
    url: str,
    params: Sequence[Any],
    headers: Optional[Mapping[str, str]] = None,
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
class AnyBlockSource(DataSource[float]):
    """Data source for retrieving AMPL/USD/VWAP from AnyBlock api."""

    api_key: str = ""

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value."""

        url = (
            "https://api.anyblock.tools/market/AMPL_USD_via_ALL/daily-volume"
            + "?roundDay=false&debug=false&access_token="
            + self.api_key
        )
        params = ["overallVWAP"]

        datapoint = await get_float_from_api(url, params)

        v, t = datapoint
        if v is not None and t is not None:
            self.store_datapoint((v, t))

        return datapoint


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
class AMPLUSDVWAPSource(DataSource[float]):
    #: Asset
    asset: str = "ampl"

    #: Currency of returned price
    currency: str = "usd"

    #: Access tokens for apis
    cfg: AMPLConfig = field(default_factory=AMPLConfig)

    #: Data sources
    sources: List[DataSource[float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sources = [
            AnyBlockSource(api_key=self.cfg.main.anyblock_api_key),
            BraveNewCoinSource(api_key=self.cfg.main.rapid_api_key),
        ]

    async def update_sources(self) -> List[OptionalDataPoint[float]]:
        """Update data feed sources

        Returns:
            Dictionary of updated source values, mapping data source UID
            to the time-stamped answer for that data source
        """

        sources = self.sources
        datapoints = await asyncio.gather(
            *[source.fetch_new_datapoint() for source in sources]
        )
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

        # Get median price
        result = statistics.median(prices)
        datapoint = (result, datetime_now_utc())
        self.store_datapoint(datapoint)

        print(
            "AMPL/USD/VWAP {} retrieved at time {}".format(datapoint[0], datapoint[1])
        )

        return datapoint
