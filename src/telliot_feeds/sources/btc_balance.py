from dataclasses import dataclass
from typing import Any, Optional
import asyncio

import requests
from requests import JSONDecodeError
from requests.adapters import HTTPAdapter

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger
from telliot_feeds.dtypes.datapoint import datetime_now_utc

logger = get_logger(__name__)

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
                return 0
            
            # Sort transactions by time in ascending order
            sorted_txs = sorted(data['txs'], key=lambda tx: tx['time'])

            #    Find the most recent transaction before the query's timestamp
            last_tx = None
            for tx in sorted_txs:
                if tx['time'] > self.timestamp:
                    break
                last_tx = tx
            if last_tx is None:
                # No transactions before the query's timestamp
                return 0

            # Use the balance from the last transaction as the BTC balance
            btc_balance = last_tx['balance']

            return btc_balance

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetches the balance of a BTC address."""
        datapoint = (self.get_response(), datetime_now_utc())
        self.store_datapoint(datapoint)
        return self.get_response()
    

if __name__ == "__main__":
    btc_balance_source = BTCBalanceSource(address='', timestamp=1706033856)
    
    async def main():
        bal = await btc_balance_source.get_response()
        print("query timestamp: ", btc_balance_source.timestamp)
        print("BTC Balance: ", bal)

    asyncio.run(main())
