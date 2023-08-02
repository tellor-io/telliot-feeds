from decimal import Decimal
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Union

from chained_accounts import ChainedAccount
from eth_utils import to_checksum_address
from telliot_core.apps.core import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.contract import ContractFunction
from web3.types import FeeHistory
from web3.types import Wei

from telliot_feeds.reporters.types import GasParams
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import fee_history_priority_fee_estimate


logger = get_logger(__name__)

FEE = Literal["maxPriorityFeePerGas", "maxFeePerGas", "gasPrice", "gas"]
FEES = Dict[FEE, Optional[Union[Wei, int]]]


class GasFees:
    """Set gas fees for a transaction.

    call update_gas_prices() to update/set gas prices
    then call get_gas_prices() to get the gas prices for a transaction assembled manually
    or call get_gas_params_core() to get the gas prices for a transaction assembled by telliot_core
    returns gas_info for the transaction type
    """

    gas_info: GasParams = {
        "maxPriorityFeePerGas": None,
        "maxFeePerGas": None,
        "gasPrice": None,
        "gas": None,
    }

    @staticmethod
    def to_gwei(value: Union[Wei, int]) -> Union[int, float]:
        """Converts wei to gwei."""
        converted_value = Web3.fromWei(value, "gwei")
        # Returns float if Gwei value is Decimal, otherwise returns int
        if isinstance(converted_value, Decimal):
            return float(converted_value)
        return converted_value

    @staticmethod
    def from_gwei(value: Union[int, float, Decimal]) -> Wei:
        """Converts gwei to wei."""
        return Web3.toWei(value, "gwei")

    @staticmethod
    def optional_to_gwei(value: Union[Wei, int, None]) -> Union[int, float, None]:
        """Converts wei to gwei and if value is None, returns None."""
        if value is None:
            return None
        return GasFees.to_gwei(value)

    @staticmethod
    def optional_from_gwei(value: Union[int, float, Decimal, None]) -> Optional[Wei]:
        """Converts gwei to wei and if value is None, returns None."""
        if value is None:
            return None
        return GasFees.from_gwei(value)

    @staticmethod
    def to_ether(value: Union[Wei, int]) -> Union[int, float]:
        """Converts wei to ether. ie 1e18 wei = 1 ether"""
        converted_value = Web3.fromWei(value, "ether")
        if isinstance(converted_value, Decimal):
            return float(converted_value)
        return converted_value

    @staticmethod
    def from_ether(value: Union[int, float, Decimal]) -> Wei:
        """Converts ether to wei. ie 1 ether = 1e18 wei"""
        return Web3.toWei(value, "ether")

    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        transaction_type: int,
        gas_limit: Optional[int] = None,  # Amount of a transaction will need to be executed
        legacy_gas_price: Optional[int] = None,  # Type 0 transaction pre London fork in Gwei
        gas_multiplier: int = 1,  # 1 percent
        # Max priority fee range that shouldn't be exceeded when auto calculating gas price in Gwei
        max_priority_fee_range: int = 5,
        priority_fee_per_gas: Optional[int] = None,
        base_fee_per_gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        reward_percentile: Optional[List[float]] = None,
        block_count: int = 10,  # Number of blocks to use for gas price calculation
        min_native_token_balance: int = 0,  # Minimum native token balance to be considered for gas price calculation
    ):
        self.endpoint = endpoint
        self.account = account
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.gas_multiplier = gas_multiplier
        self.legacy_gas_price = self.optional_from_gwei(legacy_gas_price)
        self.max_fee_per_gas = self.optional_from_gwei(max_fee_per_gas)
        self.priority_fee_per_gas = self.optional_from_gwei(priority_fee_per_gas)
        self.base_fee_per_gas = self.optional_from_gwei(base_fee_per_gas)
        self.max_priority_fee_range = self.from_gwei(max_priority_fee_range)
        self.reward_percentile = reward_percentile or [25.0, 50.0, 75.0]
        self.block_count = block_count
        self.min_native_token_balance = min_native_token_balance

        self.acct_address = to_checksum_address(account.address)
        self.web3: Web3 = endpoint._web3
        assert self.web3 is not None, f"Web3 is not initialized, check endpoint {endpoint}"

    def set_gas_info(self, fees: FEES) -> None:
        """Set class variable gas_info keys to values in fees"""
        for fee in fees:
            logger.debug(f"Setting gas info {fee} to {fees[fee]}")
            self.gas_info[fee] = fees[fee]

    def _reset_gas_info(self) -> None:
        """Resets class variable gas_info keys to None values
        This is used to reset gas_info before updating gas_info
        """
        self.gas_info = {
            "maxPriorityFeePerGas": None,
            "maxFeePerGas": None,
            "gasPrice": None,
            "gas": None,
        }

    def get_gas_info(self) -> Dict[str, Any]:
        """Get gas info and remove None values"""
        return {k: v for k, v in self.gas_info.items() if v is not None}

    def get_gas_info_core(self) -> Dict[str, Union[int, float, Wei, None]]:
        """Convert gas info to gwei and update keys to follow telliot core param convention"""
        gas = self.gas_info
        return {
            "max_fee_per_gas": self.optional_to_gwei(gas["maxFeePerGas"]),
            "max_priority_fee_per_gas": self.optional_to_gwei(gas["maxPriorityFeePerGas"]),
            "legacy_gas_price": self.optional_to_gwei(gas["gasPrice"]),
            "gas_limit": gas["gas"],
        }

    def estimate_gas_amount(self, pre_built_transaction: ContractFunction) -> Tuple[Optional[int], ResponseStatus]:
        """Estimate the gas amount for a given transaction
        ie how many gas units will a transaction need to be executed

        Returns:
            - gas amount in wei int
        """
        if self.gas_limit is not None:
            self.set_gas_info({"gas": self.gas_limit})
            return self.gas_limit, ResponseStatus()
        try:
            gas = pre_built_transaction.estimateGas({"from": self.acct_address})
            self.set_gas_info({"gas": gas})
            return gas, ResponseStatus()
        except Exception as e:
            return None, error_status("Error estimating gas amount:", e, logger.error)

    def get_legacy_gas_price(self) -> Tuple[Optional[FEES], ResponseStatus]:
        """Fetch the legacy gas price for a type 0 (legacy) transaction from the node

        Returns:
            - gas_price in gwei int
        """
        if self.legacy_gas_price is not None:
            return {"gasPrice": self.legacy_gas_price}, ResponseStatus()

        try:
            gas_price = self.web3.eth.gas_price
            if gas_price is None:
                return None, error_status("Error fetching legacy gas price, rpc returned None", log=logger.error)
            multiplier = 1.0 + (self.gas_multiplier / 100.0)  # 1 percent default extra
            legacy_gas_price = int(gas_price * multiplier)
            return {"gasPrice": Wei(legacy_gas_price)}, ResponseStatus()
        except Exception as e:
            return None, error_status("Error fetching legacy gas price", e=e, log=logger.error)

    def fee_history(self) -> Tuple[Optional[FeeHistory], ResponseStatus]:
        """Fetch the fee history for a type 2 (EIP1559) transaction from the node
        This function uses the `fee_history` method of `web3.eth` to get the history of
        transaction fees from the EVM network. The number of blocks to retrieve and the
        reward percentiles to compute are hardcoded to 5 blocks and [25, 50, 75] percentiles
        meaning for each block get the 25th, 50th and 75th percentile of priority fee per gas

        Returns:
            - fee_history: FeeHistory
        """
        try:
            fee_history = self.web3.eth.fee_history(
                block_count=self.block_count, newest_block="latest", reward_percentiles=self.reward_percentile
            )
            if fee_history is None:
                return None, error_status("unable to fetch fee history from node")
            return fee_history, ResponseStatus()
        except Exception as e:
            return None, error_status("Error fetching fee history", e=e, log=logger.error)

    def get_max_fee(self, base_fee: Wei) -> Wei:
        """Calculate the max fee for a type 2 (EIP1559) transaction"""
        if self.max_fee_per_gas is not None:
            return self.max_fee_per_gas
        # if a block is 100% full, the base fee per gas is set to increase by 12.5% for the next block
        # adding 12.5% to base_fee arg to ensure inclusion to at least the next block if not included in current block
        return Wei(int(base_fee * 1.125))

    def get_max_priority_fee(self, fee_history: Optional[FeeHistory] = None) -> Tuple[Optional[Wei], ResponseStatus]:
        """Return the max priority fee for a type 2 (EIP1559) transaction
        if priority fee is provided then return the provided priority fee
        else try to fetch a priority fee suggestion from the node using Eth._max_priority_fee method
        with a fallback that returns the max priority fee based on the fee history

        Args:
            - fee_history: Optional[FeeHistory]

        Returns:
            - max_priority_fee: Wei
            - ResponseStatus
        """
        priority_fee = self.priority_fee_per_gas
        max_range = self.max_priority_fee_range
        if priority_fee is not None:
            return priority_fee, ResponseStatus()
        else:
            try:
                max_priority_fee = self.web3.eth._max_priority_fee()
                return max_priority_fee if max_priority_fee < max_range else max_range, ResponseStatus()
            except ValueError:
                logger.warning("unable to fetch max priority fee from node using eth._max_priority_fee_per_gas method.")
        if fee_history is not None:
            return fee_history_priority_fee_estimate(fee_history, max_range), ResponseStatus()
        else:
            fee_history, status = self.fee_history()
            if fee_history is None:
                msg = "unable to fetch history to calculate max priority fee"
                return None, error_status(msg, e=status.error, log=logger.error)
            else:
                return fee_history_priority_fee_estimate(fee_history, max_range), ResponseStatus()

    def get_base_fee(self) -> Tuple[Optional[Union[Wei, FeeHistory]], ResponseStatus]:
        """Return the base fee for a type 2 (EIP1559) transaction.
        if base fee is provided then return the provided base fee
        else return the base fee based on the Eth.feed_history method response
        """
        base_fee = self.base_fee_per_gas
        if base_fee is not None:
            return base_fee, ResponseStatus()
        else:
            fee_history, status = self.fee_history()
            if fee_history is None:
                msg = "unable to fetch history to set base fee"
                return None, error_status(msg, e=status.error, log=logger.error)
            else:
                return fee_history, ResponseStatus()

    def get_eip1559_gas_price(self) -> Tuple[Optional[FEES], ResponseStatus]:
        """Get the gas price for a type 2 (EIP1559) transaction
        if at least two user args for gas aren't provided then fetch fee history and assemble the gas params
        for args that aren't provided, else use the provided args to assemble the gas params

        Returns:
            - Dict[str, Wei]; {priority_fee_per_gas: Wei, max_fee_per_gas: Wei}
            - ResponseStatus
        """
        fee_args = [self.base_fee_per_gas, self.priority_fee_per_gas, self.max_fee_per_gas]
        provided_fee_args = [arg for arg in fee_args if arg is not None]
        if len(provided_fee_args) < 2:
            # Get base fee
            _base_fee, status = self.get_base_fee()  # returns FeeHistory if base fee is not provided
            if _base_fee is None:
                msg = "no base fee set"
                return None, error_status(msg, e=status.error, log=logger.error)
            else:
                if not isinstance(_base_fee, int):
                    base_fee = _base_fee["baseFeePerGas"][-1]
                    fee_history = _base_fee
                else:
                    fee_history = None
                    base_fee = _base_fee
            # Get priority fee
            priority_fee, status = self.get_max_priority_fee(fee_history)
            if priority_fee is None:
                msg = "no priority fee set"
                return None, error_status(msg, e=status.error, log=logger.error)
            # Get max fee
            max_fee = self.get_max_fee(base_fee)
            logger.debug(f"base fee: {base_fee}, priority fee: {priority_fee}, max fee: {max_fee}")
        else:
            # if two args are given then we can calculate the third
            if self.base_fee_per_gas is not None and self.priority_fee_per_gas is not None:
                # calculate max fee
                max_fee = self.get_max_fee(self.base_fee_per_gas)
                priority_fee = self.priority_fee_per_gas

            elif self.base_fee_per_gas is not None and self.max_fee_per_gas is not None:
                # calculate priority fee
                priority_fee = Wei(self.max_fee_per_gas - self.base_fee_per_gas)
                max_fee = self.max_fee_per_gas
            elif self.priority_fee_per_gas is not None and self.max_fee_per_gas is not None:
                priority_fee = self.priority_fee_per_gas
                max_fee = self.max_fee_per_gas
            else:
                return None, error_status("Error calculating EIP1559 gas price no args provided", logger.error)

        return {
            "maxPriorityFeePerGas": priority_fee,
            "maxFeePerGas": max_fee if max_fee > priority_fee else priority_fee,
        }, ResponseStatus()

    def update_gas_fees(self) -> ResponseStatus:
        """Update class gas_info with the latest gas fees whenever called"""
        self._reset_gas_info()
        self.set_gas_info({"gas": self.gas_limit})
        if self.transaction_type == 0:
            legacy_gas_fees, status = self.get_legacy_gas_price()
            if legacy_gas_fees is None:
                return error_status(
                    "Failed to update gas fees for legacy type transaction", e=status.error, log=logger.error
                )
            self.set_gas_info(legacy_gas_fees)
            logger.debug(f"Legacy transaction gas price: {legacy_gas_fees} status: {status}")
            return status
        elif self.transaction_type == 2:
            eip1559_gas_fees, status = self.get_eip1559_gas_price()
            if eip1559_gas_fees is None:
                return error_status(
                    "Failed to update gas fees for EIP1559 type transaction", e=status.error, log=logger.debug
                )
            self.set_gas_info(eip1559_gas_fees)
            logger.debug(f"Gas fees: {eip1559_gas_fees} status: {status}")
            return status
        else:
            msg = f"Failed to update gas fees: invalid transaction type: {self.transaction_type}"
            return error_status(msg, log=logger.error)
