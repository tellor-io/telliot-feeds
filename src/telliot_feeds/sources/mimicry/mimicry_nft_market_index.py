from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional
import asyncio
import requests
from requests import JSONDecodeError
from telliot_core.utils.response import ResponseStatus
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger
import time


logger = get_logger(__name__)


@dataclass
class NFTGoSource(DataSource[str]):
    """DataSource for NFTGo expected response data."""

    market_cap_currency: Optional[str] = None
    api_key = TelliotConfig().api_keys.find(name="nftgo")[0].key


    async def fetch_nftgo_api(self, retries: int = 3) -> Optional[ResponseStatus]:
        """
        Request NFTGo data from the api
        """

        url = 'https://data-api.nftgo.io/eth/v1/market/rank/collection/all'
        headers = {'X-API-KEY': self.api_key, 'accept': 'application/json'}
        params = {
            'by': 'market_cap',
            'with_rarity': 'false',
            'asc': 'false',
            'offset': 0, 'limit': 50
        }

        with requests.Session() as session:
            session.headers.update(headers)
            retry_strat = Retry(total=retries, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry_strat)
            session.mount('https://', adapter)
            for i in range(retries):
                try:
                    response = session.get(url, params=params, timeout=(5, 10))  # type: ignore
                    response.raise_for_status()
                    data = response.json()
                except requests.exceptions.HTTPError as e:
                    logger.error(f"Request failed with HTTP error: {e}.")
                    return None
                except requests.exceptions.Timeout as e:
                    if i == retries - 1:
                        logger.error(f"Request timed out after {e}.")
                        return None
                    else:
                        backoff = 2 ** i
                        logger.warning(f"Request timed out after {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                except requests.exceptions.ConnectionError as e:
                    if i == retries - 1:
                        logger.error(f"Request failed due to network error: {e}.")
                        return None
                    else:
                        backoff = 2 ** i
                        logger.warning(f"Request failed due to network error: {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                except requests.exceptions.RequestException as e:
                    if i == retries - 1:
                        logger.error(f"Request failed with unknown error: {e}.")
                        return None
                    else:
                        backoff = 2 ** i
                        logger.warning(f"Request failed with unknown error: {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
        try:
            collection = data['collections']
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
            market_cap = sum(cap[self.market_cap_currency] for cap in collections)
        except Exception as e:
            logger.error(f"Failed to parse NFTGo response: {e}")
            return None, None
        datapoint = (market_cap, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    source = NFTGoSource(market_cap_currency="market_cap_usd")
    print(asyncio.run(source.fetch_new_datapoint()))
    # https://docs.nftgo.io/docs/faq##Currently,
    # NFTGo supports the Ethereum blockchain and is looking to support more mainstream blockchains in time to come.
