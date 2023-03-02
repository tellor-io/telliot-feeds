from __future__ import annotations

import asyncio
import time
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

# for coingecko api chain ids
block_chains = {"ethereum-mainnet": "ethereum", "solanamainnet": "solana"}


@dataclass
class NFTMashupSource(DataSource[str]):
    """
    DataSource for NFT market-cap mash up expected response data.
    """

    api_key = TelliotConfig().api_keys.find(name="nftgo")[0].key
    metric: Optional[str] = None
    currency: Optional[str] = None
    collections: Optional[Any] = None
    tokens: Optional[Any] = None

    async def fetch(self, url: str, retries: int = 3) -> Optional[Any]:
        """
        Request NFTGo data from the api.

        Args:
            url (str): URL to fetch data from.
            retries (int): Number of times to retry failed requests.

        Returns:
            Response data from the API, or None if the request fails.

        """
        url = url
        headers = {"X-API-KEY": self.api_key, "accept": "application/json"}

        with Session() as session:
            session.headers.update(headers)
            retry_strat = Retry(total=retries, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry_strat)
            session.mount("https://", adapter)
            for i in range(retries):
                try:
                    response = session.get(url, timeout=(5, 10))
                    response.raise_for_status()
                    return response.json()
                except HTTPError as e:
                    logger.error(f"Request failed with HTTP error: {e}.")
                    return None
                except Timeout as e:
                    if i == retries - 1:
                        logger.error(f"Request timed out after {e}.")
                        return None
                    else:
                        backoff = 2**i
                        logger.warning(f"Request timed out after {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        continue
                except ConnectionError as e:
                    if i == retries - 1:
                        logger.error(f"Request failed due to network error: {e}.")
                        return None
                    else:
                        backoff = 2**i
                        logger.warning(f"Request failed due to network error: {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        continue
                except RequestException as e:
                    if i == retries - 1:
                        logger.error(f"Request failed with unknown error: {e}.")
                        return None
                    else:
                        backoff = 2**i
                        logger.warning(f"Request failed with unknown error: {e}. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        continue
        return None

    async def fetch_nftgo(self) -> Optional[Any]:
        """
        Fetch NFTGo API response.

        Returns:
            List of NFTGo collection market cap values, or None if the request fails.

        """
        collection_mcaps = []
        metric = f"{self.metric}-{self.currency}".replace("-", "_")
        if not self.collections:
            logger.info("No NFTGo collections specified.")
            return None
        for item in self.collections:
            try:
                contract_address = item[1]
            except Exception as e:
                logger.warning(f"Specified NFTGo collection is not valid: {e}.")
                return None
            nftgo_url = f"https://data-api.nftgo.io/eth/v1/collection/{contract_address}/metrics"
            response = await self.fetch(nftgo_url)
            if response is not None:
                try:
                    market_cap = response[metric]
                    collection_mcaps.append(market_cap)
                except Exception as e:
                    logger.warning(f"Failed to parse NFTGo response: {e}.")
                    return None
            else:
                return None

        return collection_mcaps

    async def fetch_coingecko_api(self) -> Optional[Any]:
        """
        Fetch CoinGecko API response.

        Returns:
            List of CoinGecko token market cap values, or None if the request fails.

        """
        if not self.tokens or not self.currency:
            logger.info("No tokens specified, check query.")
            return None
        token_mcaps = []
        for item in self.tokens:
            try:
                network = block_chains[item[0]]
                contract_address = item[2]
            except Exception as e:
                logger.warning(f"Specified CoinGecko token is not valid: {e}.")
                return None
            coingecko_url = f"https://api.coingecko.com/api/v3/coins/{network}/contract/{contract_address}"
            response = await self.fetch(coingecko_url)
            if response is not None:
                try:
                    market_cap = response["market_data"]["market_cap"][self.currency.lower()]
                    token_mcaps.append(market_cap)
                except Exception as e:
                    logger.warning(f"Failed to parse CoinGecko response: {e}.")
                    return None
            else:
                return None

        return token_mcaps

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch new data point from NFTGo API."""
        collections_mcaps = await self.fetch_nftgo()
        if collections_mcaps is None:
            logger.warning("Failed to fetch from NFTGo collections list market caps.")
            return None, None
        tokens_mcaps = await self.fetch_coingecko_api()
        if tokens_mcaps is None:
            logger.warning("Failed to fetch from CoinGecko tokens list market caps.")
            return None, None
        sum_mcap = sum(collections_mcaps + tokens_mcaps)
        datapoint = (round(sum_mcap), datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    get_market_caps = NFTMashupSource(
        metric="market-cap",
        currency="usd",
        collections=(
            ("ethereum-mainnet", "0x50f5474724e0ee42d9a4e711ccfb275809fd6d4a"),
            ("ethereum-mainnet", "0xf87e31492faf9a91b02ee0deaad50d51d56d5d4d"),
            ("ethereum-mainnet", "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258"),
        ),
        tokens=(
            ("ethereum-mainnet", "sand", "0x3845badAde8e6dFF049820680d1F14bD3903a5d0"),
            ("ethereum-mainnet", "mana", "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942"),
            ("ethereum-mainnet", "ape", "0x4d224452801ACEd8B2F0aebE155379bb5D594381"),
        ),
    )

    print(asyncio.run(get_market_caps.fetch_new_datapoint()))
