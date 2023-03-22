import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Optional

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

retry_strat = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strat)


@dataclass
class NFTGoSource(DataSource[str]):
    """DataSource for NFTGo expected response data.
    For testing purposes this endpoint can be used to check the numbers:
    https://runkit.io/aslangoldenhour/calculate-nft-market-index-via-nftgo/branches/master?queryData
    """

    currency: Optional[str] = None

    async def fetch_nftgo_api(self) -> Optional[Any]:
        """
        Request NFTGo data from the api
        """
        api_key = TelliotConfig().api_keys.find(name="nftgo")
        if not api_key:
            logger.info("API key required for NFTGo API to fetch collection market cap.")
            return None
        url = "https://data-api.nftgo.io/eth/v1/market/rank/collection/all"
        headers = {"X-API-KEY": api_key[0].key, "accept": "application/json"}
        params = {"by": "market_cap", "with_rarity": "false", "asc": "false", "offset": 0, "limit": 50}

        with Session() as session:
            session.headers.update(headers)
            session.mount("https://", adapter)
            try:
                response = session.get(url, params=params, timeout=(5, 10))  # type: ignore
                response.raise_for_status()
            except (HTTPError, Timeout, ConnectionError, RequestException) as e:
                logger.error(f"Request errored: {e}.")
                return None

        try:
            collection = response.json()["collections"]
            return collection
        except KeyError as e:
            logger.error(f"Bad API response fetching top 50 collections market caps: {e}.")
            return None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch new data point from NFTGo API."""
        collections = await self.fetch_nftgo_api()
        if collections is None:
            logger.error("Failed to fetch collections details from NFTGo API.")
            return None, None
        try:
            market_cap = sum(cap[f"market_cap_{self.currency}"] for cap in collections)
        except Exception as e:
            logger.error(f"Failed to calculate total market cap for top 50 collections: {e}")
            return None, None
        datapoint = (market_cap, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    source = NFTGoSource(currency="usd")
    print(asyncio.run(source.fetch_new_datapoint()))
    # https://docs.nftgo.io/docs/faq##Currently,
    # NFTGo supports the Ethereum blockchain and is looking to support more mainstream blockchains in time to come.
