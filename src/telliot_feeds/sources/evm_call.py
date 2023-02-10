from dataclasses import dataclass
from typing import Any
from typing import Optional

from hexbytes import HexBytes
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

    chainId: Optional[int] = None
    contractAddress: Optional[str] = None  # example: '0x1234567890123456789012345678901234567890'
    calldata: Optional[bytes] = None
    web3: Optional[Web3] = None
    cfg: TelliotConfig = TelliotConfig()

    def update_web3(self) -> None:
        """Return a web3 instance for the given chain ID."""
        if not self.chainId:
            raise ValueError("Chain ID not provided")

        eps = self.cfg.endpoints.find(chain_id=self.chainId)
        if len(eps) > 0:
            endpoint = eps[0]
        else:
            raise ValueError(f"Endpoint not found for chain_id={self.chainId}")

        if not endpoint.connect():
            raise Exception(f"Endpoint not connected for chain_id={self.chainId}")

        self.web3 = endpoint.web3

    def get_response(self) -> Optional[Any]:
        """Return the response from the EVM contract."""
        if not self.contractAddress:
            raise ValueError("Contract address not provided")
        if not self.calldata:
            raise ValueError("Calldata not provided")
        if not self.web3:
            raise ValueError("Web3 not provided")

        # convert address to checksum address
        self.contractAddress = self.web3.toChecksumAddress(self.contractAddress)

        try:
            result = self.web3.eth.call({"gasPrice": 0, "to": self.contractAddress, "data": self.calldata}, "latest")
        except Exception as e:
            if e.__module__.startswith("web3"):
                logger.warning(f"Web3 exception occurred: {e}")
                return (None, None)
            raise e

        if result is None or not isinstance(result, HexBytes):
            raise ValueError(f"Result is not bytes: {str(result)}")

        if result == HexBytes("0x"):
            logger.info("Result is empty bytes, likely tried to call a non-view function")
            return (None, None)

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
