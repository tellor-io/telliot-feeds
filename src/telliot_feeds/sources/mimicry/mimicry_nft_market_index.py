import asyncio
import time
from dataclasses import dataclass
from typing import Any
from typing import Optional

from requests import JSONDecodeError
from requests.adapters import HTTPAdapter
from requests.adapters import Retry
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from requests.exceptions import Timeout
from requests.sessions import Session
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class NFTGoSource(DataSource[str]):
    """DataSource for NFTGo expected response data."""

    metric_currency: Optional[str] = None
    api_key = TelliotConfig().api_keys.find(name="nftgo")[0].key

    async def fetch_nftgo_api(self, retries: int = 3) -> Optional[Any]:
        """
        Request NFTGo data from the api
        """

        url = "https://data-api.nftgo.io/eth/v1/market/rank/collection/all"
        headers = {"X-API-KEY": self.api_key, "accept": "application/json"}
        params = {"by": "market_cap", "with_rarity": "false", "asc": "false", "offset": 0, "limit": 50}

        with Session() as session:
            session.headers.update(headers)
            retry_strat = Retry(total=retries, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry_strat)
            session.mount("https://", adapter)
            for i in range(retries):
                try:
                    response = session.get(url, params=params, timeout=(5, 10))  # type: ignore
                    response.raise_for_status()
                except (HTTPError, Timeout, ConnectionError, RequestException) as e:
                    if i == retries - 1:
                        logger.error(f"Request errored: {e}.")
                        return None
                    else:
                        backoff = 2**i
                        logger.warning(f"Request errored: {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
        try:
            collection = response.json()["collections"]
            return collection
        except (JSONDecodeError, KeyError) as e:
            logger.error(f"Response JSON decode error: {e}.")
            return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch new data point from NFTGo API."""
        collections = await self.fetch_nftgo_api()
        if collections is None:
            return None, None
        try:
            market_cap = sum(cap[self.metric_currency] for cap in collections)
        except Exception as e:
            logger.error(f"Failed to parse NFTGo response: {e}")
            return None, None
        datapoint = (market_cap, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    source = NFTGoSource(metric_currency="market_cap_usd")
    print(asyncio.run(source.fetch_new_datapoint()))
    # https://docs.nftgo.io/docs/faq##Currently,
    # NFTGo supports the Ethereum blockchain and is looking to support more mainstream blockchains in time to come.
