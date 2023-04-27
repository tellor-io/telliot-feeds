import asyncio
from asyncio.exceptions import TimeoutError
from dataclasses import dataclass
from typing import Any
from typing import Optional

from aiohttp import ClientConnectionError
from aiohttp import ClientError
from aiohttp import ClientResponseError
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

# for coingecko api chain ids
block_chains = {"ethereum-mainnet": "ethereum", "solana-mainnet": "solana"}


@dataclass
class NFTMashupSource(DataSource[str]):
    """
    DataSource for NFT market-cap mash up expected response data.
    For testing purposes this endpoint can be used to check the numbers:
    https://runkit.io/aslangoldenhour/macro-market-mashup/branches/master?queryData=<queryData>
    """

    metric: Optional[str] = None  # ("market_cap")
    currency: Optional[str] = None  # ("usd")
    collections: Optional[list[tuple[str, str]]] = None  # ("chain-name", "contract-address")
    tokens: Optional[list[tuple[str, str, str]]] = None  # ("chain-name", "token-symbol", "contract-address")
    retries: int = 3

    async def fetch(self, url: str, headers: Optional[dict[str, str]]) -> Optional[Any]:
        """
        Fetches data from a given URL.

        Args:
            url (str): The URL to fetch data from.
            headers (Optional[dict[str, str]]): Headers to send with the request.

        Returns:
            Response data from the API, or None if the request fails.

        """
        async with ClientSession(headers=headers) as session:
            timeout = ClientTimeout(total=10)
            async with session.get(url, timeout=timeout) as response:
                return await response.json()

    async def fetch_urls(self, urls: list[str], headers: Optional[dict[str, str]] = None) -> Any:
        """
        Fetches a list of URLs and returns a list of responses.

        Args:
            urls (list[str]): A list of URLs to fetch.
            headers (Optional[dict[str, str]]): Headers to send with the request.

        Returns:
            Any: A list of responses.
        """
        tasks = [asyncio.create_task(self.fetch_url_with_retry(url=url, headers=headers)) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses

    async def fetch_url_with_retry(self, url: str, headers: Optional[dict[str, str]]) -> Optional[Any]:
        """
        Fetches a response from an api with retry logic.

        Args:
            url (str): A single URL to fetch.
            headers (Optional[dict[str, str]]): Headers to send with the request.

        Returns:
            Any: A list of responses.
        """
        retries = self.retries
        for attempt in range(retries):
            try:
                response = await self.fetch(url=url, headers=headers)
                return response
            except (ClientError, ClientConnectionError, ClientResponseError, TimeoutError) as e:
                if attempt == retries - 1:
                    logger.warning(f"Failed to fetch from {url} after {retries} attempts: {type(e).__name__}.")
                    return None
                wait_time = 2**attempt
                await asyncio.sleep(wait_time)
        return None

    async def fetch_collections_mcap(self) -> Optional[Any]:
        """
        Fetch market cap for a list collection from NFTGo API response.

        Returns:
            Sum of collections' market cap, or None if the request fails.

        Requires:
            an api key from NFTGo (https://developer.nftgo.io/)
        """
        if not self.collections:
            logger.info("No NFTGo collections specified.")
            return None

        api_key = TelliotConfig().api_keys.find(name="nftgo")
        if not api_key:
            logger.info("API key required for NFTGo source to fetch collection market cap.")
            return None

        nftgo_url = "https://data-api.nftgo.io/eth/v1/collection/{contract_address}/metrics"
        headers = {"X-API-KEY": api_key[0].key, "accept": "application/json"}

        urls = []
        for item in self.collections:
            try:
                contract_address = item[1]
            except IndexError as e:
                logger.warning(f"Specified NFTGo collection is not valid: {e}.")
                return None
            urls.append(nftgo_url.format(contract_address=contract_address))

        responses = await self.fetch_urls(urls=urls, headers=headers)
        collection_mcaps = []
        metric = f"{self.metric}_{self.currency}".replace("-", "_")
        for idx, response in enumerate(responses):
            if response is not None:
                try:
                    market_cap = response[metric]
                    if not market_cap:
                        logger.debug(f"No value fetched for collection: {self.collections[idx]}")
                        return None
                    collection_mcaps.append(market_cap)
                except KeyError as e:
                    logger.warning(
                        f"Failed to fetch collection's: {self.collections[idx]} "
                        f"market cap, metric: ({metric}), not found: {e}."
                    )
                    return None
            else:
                return None

        return sum(collection_mcaps)

    async def fetch_tokens_mcap(self) -> Optional[Any]:
        """
        Fetch list of tokens' market cap from coingecko api.

        Returns:
            Sum of all tokens' market cap, or None if the request fails.

        """
        if not self.tokens or not self.currency:
            logger.info("No tokens specified, check query.")
            return None
        coingecko_url = "https://api.coingecko.com/api/v3/coins/{network}/contract/{contract_address}"
        urls = []
        for item in self.tokens:
            try:
                network = block_chains[item[0]]
                contract_address = item[2]
            except Exception as e:
                logger.warning(f"Specified CoinGecko token is not valid: {e}.")
                return None

            urls.append(coingecko_url.format(network=network, contract_address=contract_address))

        responses = await self.fetch_urls(urls=urls)
        token_mcaps = []
        for idx, response in enumerate(responses):
            if response is not None:
                try:
                    market_cap = response["market_data"]["market_cap"][self.currency.lower()]
                    if not market_cap:
                        logger.debug(f"No value fetched for token: {self.tokens[idx]}")
                        return None
                    token_mcaps.append(market_cap)
                except Exception as e:
                    logger.warning(f"Failed to fetch token's market cap: {e}.")
                    return None
            else:
                return None

        return sum(token_mcaps)

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch new data point from NFTGo API."""
        collections_mcaps = await self.fetch_collections_mcap()
        tokens_mcaps = await self.fetch_tokens_mcap()

        if not collections_mcaps or not tokens_mcaps:
            logger.warning(
                f"Failed to fetch all market caps. tokens = {tokens_mcaps}, collections = {collections_mcaps}"
            )
            return None, None

        total_mcap = collections_mcaps + tokens_mcaps
        datapoint = (round(total_mcap), datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint


if __name__ == "__main__":
    from telliot_feeds.feeds.mimicry.macro_market_mashup_feed import COLLECTIONS, TOKENS

    get_market_caps = NFTMashupSource(
        metric="market-cap",
        currency="usd",
        collections=COLLECTIONS,  # type: ignore
        tokens=TOKENS,  # type: ignore
    )

    print(asyncio.run(get_market_caps.fetch_new_datapoint()))
