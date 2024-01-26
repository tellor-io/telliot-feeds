import time
from dataclasses import dataclass
from typing import Any
from typing import Optional

from requests.adapters import HTTPAdapter
from telliot_core.apps.telliot_config import TelliotConfig
from urllib3.util import Retry
from web3 import Web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware
from web3.types import BlockData

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.source_utils import update_web3

logger = get_logger(__name__)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class EVMBalanceSource(DataSource[Any]):
    """DataSource for returning the balance of an EVM chain address at a given timestamp."""

    chainId: Optional[int] = None
    evmAddress: Optional[str] = None
    timestamp: Optional[int] = None
    cfg: TelliotConfig = TelliotConfig()
    web3: Optional[Web3] = None

    def get_block(self, w3: Web3, block_number: int, full_transaction: bool = False) -> Optional[BlockData]:
        """Get block info with error handling for POA chains"""
        try:
            block = w3.eth.get_block(block_number, full_transaction)
        except ExtraDataLengthError as e:
            logger.info(f"POA chain detected. Injecting POA middleware in response to exception: {e}")
            try:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except ValueError as e:
                logger.error(f"Unable to inject web3 middleware for POA chain connection: {e}")
            block = w3.eth.get_block(block_number, full_transaction)
        except Exception as e:
            logger.error(f"Error fetching block info: {e}")
            block = None
        return block

    def get_balance(self, w3: Web3, address: str, block_number: int) -> Optional[int]:
        """Get balance of address at block number"""
        try:
            balance = w3.eth.get_balance(address, block_identifier=block_number)
        except ExtraDataLengthError as e:
            logger.info(f"POA chain detected. Injecting POA middleware in response to exception: {e}")
            try:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except ValueError as e:
                logger.error(f"Unable to inject web3 middleware for POA chain connection: {e}")
            balance = w3.eth.get_balance(address, block_identifier=block_number)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            balance = None
        return balance

    async def get_response(self) -> Optional[Any]:
        """gets balance of evm address at specific timestamp using web3.py"""
        if not self.chainId:
            raise ValueError("EVM chain ID not provided")
        if not self.evmAddress:
            raise ValueError("EVM address not provided")
        if not self.timestamp:
            raise ValueError("Timestamp not provided")

        # convert address to checksum address
        self.evmAddress = Web3.toChecksumAddress(self.evmAddress)

        if self.timestamp > int(time.time()):
            logger.warning("Timestamp is greater than current timestamp")
            return None

        block_num = await self.search_block_by_timestamp()
        if block_num is None:
            return None

        if not self.web3:
            raise ValueError("Web3 not instantiated")

        balance = self.get_balance(self.web3, self.evmAddress, block_num)
        if balance is None:
            return None
        return balance

    async def search_block_by_timestamp(self) -> Optional[int]:
        """Binary search for the block closest to the target timestamp

        Returns:
            The closest block number less than or equal to the target timestamp
        """
        if not self.web3:
            raise ValueError("Web3 not instantiated")
        if not self.timestamp:
            raise ValueError("Timestamp not provided")

        left_block_number = 0
        right_block_number: int = self.web3.eth.block_number
        mid_block_number = (left_block_number + right_block_number) // 2
        target_timestamp = self.timestamp

        while right_block_number - left_block_number > 2:
            mid_block = self.get_block(self.web3, mid_block_number)
            if not mid_block:
                return None
            mid_block_timestamp = mid_block["timestamp"]

            # Check for exact match
            if mid_block_timestamp == target_timestamp:
                return mid_block_number

            if mid_block_timestamp < target_timestamp:
                left_block_number = mid_block_number
            else:
                right_block_number = mid_block_number
            mid_block_number = (left_block_number + right_block_number) // 2

        mid_block = self.get_block(self.web3, mid_block_number)
        if not mid_block:
            return None
        mid_block_timestamp = mid_block["timestamp"]
        if mid_block_timestamp <= target_timestamp:
            return mid_block_number
        else:
            if left_block_number == 0:
                return None
            return left_block_number

    async def fetch_new_datapoint(self) -> OptionalDataPoint[int]:
        """Fetch balance of EVM address at a given timestamp

        Returns:
            EVM address balance at timestamp
        """
        if not self.chainId:
            raise ValueError("Chain ID not provided")
        try:
            self.web3 = update_web3(self.chainId, self.cfg)
        except Exception as e:
            logger.warning(f"Error occurred while updating web3 instance: {e}")
            return None, None

        if not self.web3:
            raise ValueError("Web3 not instantiated")
        balance = await self.get_response()
        if balance is None:
            return None, None

        datapoint = (balance, datetime_now_utc())
        self.store_datapoint(datapoint)
        return datapoint
