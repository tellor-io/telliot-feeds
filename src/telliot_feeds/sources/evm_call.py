from dataclasses import dataclass
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class EVMCallSource(DataSource[Any]):
    """DataSource for returning the result of a read function on an EVM contract."""

    chain_id: Optional[int] = None
    contract_address: Optional[str] = None  # example: '0x1234567890123456789012345678901234567890'
    calldata: Optional[bytes] = None
    web3: Optional[Web3] = None
    cfg: TelliotConfig = TelliotConfig()

    def update_web3(self) -> None:
        """Return a web3 instance for the given chain ID."""
        if not self.chain_id:
            raise ValueError("Chain ID not provided")

        eps = self.cfg.endpoints.find(chain_id=self.chain_id)
        if len(eps) > 0:
            endpoint = eps[0]
        else:
            raise ValueError(f"Endpoint not found for chain_id={self.chain_id}")

        if not endpoint.connect():
            raise Exception(f"Endpoint not connected for chain_id={self.chain_id}")

        self.web3 = endpoint.web3

    def get_response(self) -> Optional[Any]:
        """Return the response from the EVM contract."""
        if not self.contract_address:
            raise ValueError("Contract address not provided")
        if not self.calldata:
            raise ValueError("Calldata not provided")
        if not self.web3:
            raise ValueError("Web3 not provided")

        # web3.eth.call returns bytes
        result = self.web3.eth.call({"to": self.contract_address, "data": self.calldata}, "latest")
        if result is None or not isinstance(result, bytes):
            raise ValueError(f"Result is not bytes: {result}")
        logger.info(f"EVMCallSource result bytes: {result.hex()}")
        ts = int(datetime_now_utc().timestamp())
        return (result, ts)

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Update current value with time-stamped value fetched from EVM contract.

        Returns:
            Current time-stamped value
        """
        try:
            self.update_web3()
        except Exception as e:
            logger.warning(f"Error occurred while updating web3 instance: {e}")
            return None, None

        try:
            val = self.get_response()
        except Exception as e:
            logger.warning(f"Error occurred while getting response: {e}")
            return None, None

        datapoint = (val, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
