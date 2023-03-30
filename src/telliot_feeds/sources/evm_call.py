from dataclasses import dataclass
from typing import Any
from typing import Optional

from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3
from web3.exceptions import ContractLogicError

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
        """Validate evm call type args
        chain-id is checked by default if web3 connection fails
        address format, length, and if checksum is checked by default
        cause the encoding fails if not address type.  Address is checked here if its contract or EOA
        calldata is checked for length being at least 4 bytes and if exists in bytecode

        in cases of known errors and failures the response will be empty-bytes and current timestamp
        """
        if not self.contractAddress:
            raise ValueError("Contract address not provided")
        if not self.calldata:
            raise ValueError("Calldata not provided")
        if not self.web3:
            raise ValueError("Web3 not provided")

        empty_bytes = HexBytes(bytes(32))
        ts = int(datetime_now_utc().timestamp())

        self.contractAddress = self.web3.toChecksumAddress(self.contractAddress)

        if len(self.calldata) < 4:  # function signature is 4 bytes long, so calldata must be at least of length 4
            logger.info(f"Invalid calldata: {self.calldata!r}, too short, submitting empty bytes")
            return (empty_bytes, ts)
        try:
            result = self.web3.eth.call({"gasPrice": 0, "to": self.contractAddress, "data": self.calldata}, "latest")
        # Is there a scenario where a contract call for a view/pure function would revert when the callData is valid?
        except ContractLogicError as e:
            logger.warning(f"ContractLogicError perhaps bad calldata: {e}")
            return (empty_bytes, ts)
        except Exception as e:
            if e.__module__.startswith("web3"):
                logger.warning(f"Web3 exception occurred: {e}")
                return (None, None)
            raise e

        if result is None or not isinstance(result, HexBytes):
            raise ValueError(f"Result is not bytes: {str(result)}")

        if result == HexBytes("0x"):
            # if response is empty bytes, then make call to test if contractAddress is valid ie EOA or contract address
            bytecode = self.web3.eth.getCode(self.contractAddress)
            if len(bytecode) <= 0:  # if no code means address isn't a contractAddress
                logger.info(f"Invalid contract address: {self.contractAddress}, no bytecode, submitting empty bytes")
                return (HexBytes(bytes(32)), ts)
            elif self.calldata[:4] not in bytecode:
                logger.info(f"function selector: {self.calldata!r}, not found in bytecode, submitting empty bytes")
                return (HexBytes(bytes(32)), ts)
            else:
                # TODO: should the result be empty bytes instead of returning None None?
                # wrong contract address or non-view function return empty bytes
                # are there other scenarios where the call spec is valid but the call fails?
                logger.info("Result is empty bytes, call might be to a non-view function")
                return (None, None)

        logger.info(f"EVMCallSource result bytes: {result.hex()}")

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
