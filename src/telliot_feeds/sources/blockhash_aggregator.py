import asyncio
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Tuple

import requests
from requests import JSONDecodeError
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from web3 import Web3

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.cfg import mainnet_config
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


cfg = mainnet_config()
cfg.get_endpoint().connect()
w3 = cfg.get_endpoint().web3

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


def block_num_from_timestamp(timestamp: int) -> Optional[int]:
    with requests.Session() as s:
        s.mount("https://", adapter)
        try:
            rsp = s.get(
                "https://api.etherscan.io/api"
                "?module=block"
                "&action=getblocknobytime"
                f"&timestamp={timestamp}"
                "&closest=before"
                "&apikey="
            )
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timeout getting ETH block num from timestamp")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Etherscan API error: {e}")
            return None

        try:
            this_block = rsp.json()
        except JSONDecodeError:
            logger.error("Etherscan API returned invalid JSON")
            return None

        try:
            if this_block["status"] != "1":
                logger.error(f"Etherscan API returned error: {this_block['message']}")
                return None
        except KeyError:
            logger.error("Etherscan API returned JSON without status")
            return None

        return int(this_block["result"])


async def get_eth_hash(timestamp: int) -> Optional[str]:
    """Fetches next Ethereum blockhash after timestamp from API."""

    try:
        this_block = w3.eth.get_block("latest")
    except Exception as e:
        logger.error(f"Unable to retrieve latest block: {e}")
        return None

    if this_block["timestamp"] < timestamp:
        logger.error(f"Timestamp {timestamp} is older than current block timestamp {this_block['timestamp']}")
        return None

    block_num = block_num_from_timestamp(timestamp)
    if block_num is None:
        logger.warning("Unable to retrieve block number from Etherscan API")
        return None

    try:
        block = w3.eth.get_block(block_num)
    except Exception as e:
        logger.error(f"Unable to retrieve block {block_num}: {e}")
        return None

    logger.info(f"Using ETH block number {block_num}")
    return str(block["hash"].hex())


async def get_btc_hash(timestamp: int) -> Tuple[Optional[str], Optional[int]]:
    """Fetches next Bitcoin blockhash after timestamp from API."""
    with requests.Session() as s:
        s.mount("https://", adapter)
        ts = timestamp + 480 * 60

        try:
            rsp = s.get(f" https://blockchain.info/blocks/{ts * 1000}?format=json")
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timeout getting BTC block num from timestamp")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Blockchain.info API error: {e}")
            return None, None

        try:
            blocks = rsp.json()
        except JSONDecodeError:
            logger.error("Blockchain.info API returned invalid JSON")
            return None, None

        if len(blocks) == 0:
            logger.warning("Blockchain.info API returned no blocks")
            return None, None

        if "time" not in blocks[0]:
            logger.warning("Blockchain.info response doesn't contain needed data")
            return None, None

        block = blocks[0]
        for b in blocks[::-1]:
            if b["time"] < timestamp:
                continue
            block = b
            break

        if block["time"] < timestamp:
            logger.warning("Blockchain.info API returned no blocks after timestamp")
            return None, None
        logger.info(f"Using BTC block number {block['height']}")
        return str(block["hash"]), block["time"]


@dataclass
class TellorRNGManualSource(DataSource[Any]):
    """DataSource for TellorRNG manually-entered timestamp."""

    timestamp = 0

    def set_timestamp(self, timestamp: int) -> None:
        self.timestamp = timestamp

    def parse_user_val(self) -> int:
        """Parse timestamp from user input."""
        print("Enter timestamp for generating a random number: ")

        data = None
        while data is None:
            inpt = input()

            try:
                inpt = int(inpt)  # type: ignore
            except ValueError:
                print("Invalid input. Enter decimal value (int).")
                continue

            print(f"Generating random number from timestamp: {inpt}\nPress [ENTER] to confirm.")
            _ = input()
            data = inpt

        self.timestamp = data
        return data

    async def fetch_new_datapoint(self) -> OptionalDataPoint[bytes]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """

        if self.timestamp == 0:
            timestamp = self.parse_user_val()
        else:
            timestamp = self.timestamp

        btc_hash, btc_timestamp = await get_btc_hash(timestamp)

        if btc_hash is None:
            logger.warning("Unable to retrieve Bitcoin blockhash")
            return None, None
        if btc_timestamp is None:
            logger.warning("Unable to retrieve Bitcoin timestamp")
            return None, None
        eth_hash = await get_eth_hash(btc_timestamp)
        if eth_hash is None:
            logger.warning("Unable to retrieve Ethereum blockhash")
            return None, None

        data = Web3.solidityKeccak(["string", "string"], [eth_hash, btc_hash])
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        datapoint = (data, dt)

        self.store_datapoint(datapoint)
        logger.info(f"Stored random number for timestamp {timestamp}: {data.hex()}")
        return datapoint


async def main() -> None:
    """Runs the data source."""
    source = TellorRNGManualSource()
    await source.fetch_new_datapoint()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
