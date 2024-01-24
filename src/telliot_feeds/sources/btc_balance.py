from dataclasses import dataclass
from typing import Any, Optional
import asyncio

import requests
from requests import JSONDecodeError
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger
from telliot_feeds.dtypes.datapoint import datetime_now_utc

logger = get_logger(__name__)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)

@dataclass
class BTCBalanceSource(DataSource[Any]):
    """DataSource for returning the balance of a BTC address at a given timestamp."""

    address: Optional[str] = None
    timestamp: Optional[int] = None

    async def get_response(self) -> Optional[Any]:
        """gets balance of address from https://blockchain.info/multiaddr?active=$address|$address"""
        if not self.address:
            raise ValueError("BTC address not provided")
        if not self.timestamp:
            raise ValueError("Timestamp not provided")
        
        block_num = await self.block_num_from_timestamp(self.timestamp)
        if block_num is None:
            return None

        with requests.Session() as s:
            url = f"https://blockchain.info/multiaddr?active={self.address}|{self.address}"
            try:
                rsp = s.get(url)
            except requests.exceptions.ConnectTimeout:
                logger.error("Connection timeout getting BTC balance")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Blockchain.info API error: {e}")
                return None

            try:
                data = rsp.json()
            except JSONDecodeError:
                logger.error("Blockchain.info API returned invalid JSON")
                return None

            if 'txs' not in data:
                logger.warning("Blockchain.info response doesn't contain needed data")
                return None
            
            if 'addresses' not in data:
                logger.warning("Blockchain.info response doesn't contain needed data")
                return None
            
            if int(data['addresses'][0]['n_tx']) == 0:
                # No transactions for this address
                logger.info("No transactions for this address")
                return 0

            # Sort transactions by time in ascending order
            sorted_txs = sorted(data['txs'], key=lambda tx: (tx['block_height'], tx['tx_index']))

            #    Find the most recent transaction before the query's timestamp
            last_tx = None
            for tx in sorted_txs:
                if tx['block_height'] > block_num:
                    break
                last_tx = tx
            if last_tx is None:
                # No transactions before the query's timestamp
                logger.info("No transactions before the query's timestamp")
                return 0

            # Use the balance from the last transaction as the BTC balance
            btc_balance = last_tx['balance']
            return btc_balance
        
    async def block_num_from_timestamp(self, timestamp: int) -> Optional[int]:
            """Fetches next Bitcoin blockhash after timestamp from API."""
            with requests.Session() as s:
                s.mount("https://", adapter)
            ts = timestamp + 480 * 60

            try:
                rsp = s.get(f"https://blockchain.info/blocks/{ts * 1000}?format=json")
            except requests.exceptions.ConnectTimeout:
                logger.error("Connection timeout getting BTC block num from timestamp")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Blockchain.info API error: {e}")
                return None

            try:
                blocks = rsp.json()
            except JSONDecodeError:
                logger.error("Blockchain.info API returned invalid JSON")
                return None
            
            if not isinstance(blocks, list):
                logger.warning("Blockchain.info API response is not a list")
                return None

            if len(blocks) == 0:
                logger.warning("Blockchain.info API returned no blocks")
                return None

            if "time" not in blocks[0]:
                logger.warning("Blockchain.info response doesn't contain needed data")
                return None
            
            sorted_blocks = sorted(blocks, key=lambda block: block['time'])

            block = sorted_blocks[0]
            next_block = sorted_blocks[1]
            for b in sorted_blocks:
                if b["time"] > timestamp:
                    next_block = b
                    break
                block = b

            if block["time"] > timestamp:
                logger.warning("Blockchain.info API returned no blocks before or equal to timestamp")
                return None
            logger.info(f"Using BTC block number {block['height']}")
            return int(block["height"])

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetches the balance of a BTC address."""
        balance = await self.get_response()
        if balance is None:
            return None, None
        datapoint = (balance, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint
    

if __name__ == "__main__":
    btc_balance_source = BTCBalanceSource(address='bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03', timestamp=1706051389)
    
    async def main():
        bal = await btc_balance_source.fetch_new_datapoint()
        print("query timestamp: ", btc_balance_source.timestamp)
        print("BTC Balance: ", bal[0])

    asyncio.run(main())
