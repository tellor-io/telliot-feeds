from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Tuple

from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import middleware
from web3 import Web3
from web3.exceptions import ContractLogicError
from web3.exceptions import ExtraDataLengthError
from web3.types import BlockIdentifier

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.source_utils import update_web3


logger = get_logger(__name__)


@dataclass
class EVMCallSource(DataSource[Any]):
    """DataSource for returning the result of a read function on an EVM contract."""

    chainId: Optional[int] = None
    contractAddress: Optional[str] = None  # example: '0x1234567890123456789012345678901234567890'
    calldata: Optional[bytes] = None
    web3: Optional[Web3] = None
    cfg: TelliotConfig = TelliotConfig()

    def get_response(self, block_number: BlockIdentifier = "latest") -> Optional[Tuple[HexBytes, int]]:
        """Makes requested EVM call and returns the response from the contract

        EVM call query is validated as best as possible and for known invalid EVM call requests
        empty bytes are returned as the response to be submitted to the oracle.
        Things that prompt an empty bytes response are:
        - calldata with length of less than four bytes
        - contract address that returns zero length bytecode
        - function selector that isn't available in the bytecode
        """
        if not self.contractAddress:
            raise ValueError("Contract address not provided")
        if not self.calldata:
            raise ValueError("Calldata not provided")
        if not self.web3:
            raise ValueError("Web3 not provided")

        empty_bytes = HexBytes(bytes(32))

        try:
            self.web3.eth.get_block(block_number)
        except ExtraDataLengthError as e:
            logger.info(f"EVMCall to POA chain detected. Injecting POA middleware in response to exception: {e}")

            try:
                self.web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)
            except ValueError as e:
                logger.warning(f"Unable to inject web3 middleware for POA chain connection: {e}")

        try:
            block = self.web3.eth.get_block(block_number)
            ts = int(block["timestamp"])
        except Exception as e:
            logger.warning(f"Unable to retrieve current block timestamp: {e}")
            return None

        self.contractAddress = self.web3.toChecksumAddress(self.contractAddress)

        if len(self.calldata) < 4:  # A function selector is 4 bytes long, so calldata must be at least of length 4
            logger.info(f"Invalid calldata: {self.calldata!r}, too short, submitting empty bytes")
            return (empty_bytes, ts)
        try:
            result = self.web3.eth.call(
                {"gasPrice": 0, "to": self.contractAddress, "data": self.calldata}, block_number
            )
        # Is there a scenario where a contract call for a view/pure function would revert when the callData is valid?
        except ContractLogicError as e:
            bytecode = self.web3.eth.getCode(self.contractAddress)
            if self.calldata[:4] not in bytecode:
                logger.info(f"function selector: {self.calldata!r}, not found in bytecode, submitting empty bytes")
                return (empty_bytes, ts)
            else:
                # It could be safe to submit zerobytes for most contract logic errors since this error is
                # indicative of bad calldata ie bad function arguments or bad contract logic, but don't
                # know if there are cases where you shouldn't so consider submitting manually based on reason
                logger.warning(f"ContractLogicError read exception for reason: {e}")
                return None
        except Exception as e:
            if e.__module__.startswith("web3"):
                logger.warning(f"Web3 exception occurred: {e}")
                return None
            raise e

        if result is None or not isinstance(result, HexBytes):
            raise ValueError(f"Result is not bytes: {str(result)}")

        if result == HexBytes("0x"):
            # A Non-contract address returns zero bytes so we check here to see
            # if thats the reason for the zero bytes result; if so submit empty bytes to oracle
            bytecode = self.web3.eth.getCode(self.contractAddress)
            if len(bytecode) <= 0:  # if no code means address isn't a contractAddress
                logger.info(f"Invalid contract address: {self.contractAddress}, no bytecode, submitting empty bytes")
                return (empty_bytes, ts)
            logger.info("Result is empty bytes, call might be to a non-view function")
            return None

        logger.info(f"EVMCallSource result bytes: {result.hex()}")

        return (result, ts)

    async def fetch_new_datapoint(self, block_number: BlockIdentifier = "latest") -> OptionalDataPoint[Any]:
        """Update current value with time-stamped value fetched from EVM contract.

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

        try:
            val = self.get_response(block_number=block_number)
            if val is None:
                logger.warning("Call to contract failed to return a response")
                return None, None
        except Exception as e:
            logger.warning(f"Error occurred while getting response: {e}")
            return None, None

        datapoint = (val, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
