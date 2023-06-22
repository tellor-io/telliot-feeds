import statistics
from dataclasses import dataclass
from typing import Any
from typing import Optional

from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
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


@dataclass
class GasPriceOracleSource(DataSource[Any]):
    chainId: Optional[int] = None
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

    def search_block_by_timestamp(self) -> Optional[BlockData]:
        """Binary search for the block closest to the target timestamp (not later)

        Returns:
            The block closest to the target timestamp (not later)
        """
        if not self.web3:
            raise ValueError("Web3 not instantiated")
        if not self.timestamp:
            raise ValueError("Timestamp not provided")

        right_block_number: int = self.web3.eth.block_number
        left_block_number = 0
        target_timestamp = self.timestamp

        while left_block_number <= right_block_number:
            mid = (left_block_number + right_block_number) // 2
            mid_block = self.get_block(self.web3, mid)
            if not mid_block:
                return None
            mid_block_timestamp = mid_block["timestamp"]

            # Check for exact match
            if mid_block_timestamp == target_timestamp:
                return mid_block

            if mid_block_timestamp < target_timestamp:
                left_block_number = mid + 1
            else:
                right_block_number = mid - 1

        # If we've exited the loop, that means the target timestamp is not equal to any block timestamp,
        # we'll find the block that is closest the target timestamp (not later).
        left_block = self.web3.eth.get_block(left_block_number)
        right_block = self.web3.eth.get_block(right_block_number)
        if left_block["timestamp"] > target_timestamp:
            return right_block
        if right_block["timestamp"] > target_timestamp:
            return left_block

        return left_block if left_block["timestamp"] >= right_block["timestamp"] else right_block

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Fetch median gas price for a given timestamp by fetching
        block info for the closest block.

        Returns:
            Current time-stamped value
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

        nearest_block = self.search_block_by_timestamp()
        if nearest_block is None:
            logger.error("Unable to find block closest to target timestamp")
            return None, None

        block_data = self.get_block(self.web3, nearest_block["number"], full_transaction=True)
        if not block_data:
            logger.error(f"Error occurred while fetching block data closest to target timestamp {self.timestamp}")
            return None, None
        # sort the transactions by gas price
        gas_prices = [tx["gasPrice"] for tx in block_data["transactions"] if not isinstance(tx, HexBytes)]
        sorted_gas_prices = sorted(gas_prices)
        # find the median gas price
        gas_price = statistics.median(sorted_gas_prices)

        datapoint = (gas_price / 1e9, datetime_now_utc())

        self.store_datapoint(datapoint)

        return datapoint
