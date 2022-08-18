from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from chained_accounts import ChainedAccount
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.interval import IntervalReporter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class CustomXReporter(IntervalReporter):
    """Custom reporter contract
    Use by entering an abi and contract address through the command line
    requires depositstake and submitValue signature functions to work
    """

    def __init__(
        self,
        custom_contract: Contract,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        master: Contract,
        oracle: Contract,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = 100.0,
        transaction_type: int = 0,
        gas_limit: int = 350000,
        max_fee: Optional[int] = None,
        priority_fee: int = 5,
        legacy_gas_price: Optional[int] = None,
        gas_price_speed: str = "fast",
    ) -> None:

        self.endpoint = endpoint
        self.account = account
        self.master = master
        self.oracle = oracle
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.acct_addr = to_checksum_address(custom_contract.address)
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_price_speed = gas_price_speed
        self.trb_usd_median_feed = trb_usd_median_feed
        self.eth_usd_median_feed = eth_usd_median_feed
        self.custom_contract = custom_contract

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked
        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to stake with
        the address's funds."""
        status = ResponseStatus()

        gas_price_gwei = await self.fetch_gas_price()
        if not gas_price_gwei:
            note = "Unable to fetch gas price during during ensure_staked()"
            return False, error_status(note=note, log=logger.warning)

        staker_info, read_status = await self.master.read(func_name="getStakerInfo", _staker=self.acct_addr)

        if (not read_status.ok) or (staker_info is None):
            msg = "Unable to read reporters staker status: " + read_status.error  # error won't be none # noqa: E501
            status = error_status(msg, log=logger.info)
            status.e = read_status.e
            return False, status

        logger.info(f"Stake status: {staker_info[0]}")

        # Status 1: staked
        if staker_info[0] == 1:
            return True, status

        # Status 0: not yet staked
        elif staker_info[0] == 0:
            logger.info("Address not yet staked. Depositing stake.")

            _, write_status = await self.custom_contract.write(
                func_name="depositStake",
                gas_limit=350000,
                legacy_gas_price=gas_price_gwei,
            )

            if write_status.ok:
                return True, status
            else:
                msg = (
                    "Unable to stake deposit: "
                    + write_status.error
                    + f"Make sure {self.acct_addr} has enough ETH & TRB (100)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.info)

        # Status 3: disputed
        if staker_info[0] == 3:
            msg = "Current address disputed. Switch address to continue reporting."  # noqa: E501
            return False, error_status(msg, log=logger.info)

        # Statuses 2, 4, and 5: stake transition
        else:
            msg = "Current address is locked in dispute or for withdrawal."  # noqa: E501
            return False, error_status(msg, log=logger.info)

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once
        This method checks to see if a user is able to submit
        values to the TellorX oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""
        # Check staker status
        staked, status = await self.ensure_staked()
        if not staked or not status.ok:
            logger.warning(status.error)
            return None, status

        status = await self.check_reporter_lock()
        if not status.ok:
            return None, status

        # Get suggested datafeed if none provided
        datafeed = await self.fetch_datafeed()
        if not datafeed:
            msg = "Unable to suggest datafeed"
            return None, error_status(note=msg, log=logger.info)

        logger.info(f"Current query: {datafeed.query.descriptor}")

        status = await self.ensure_profitable(datafeed)
        if not status.ok:
            return None, status

        status = ResponseStatus()

        address = to_checksum_address(self.account.address)

        # Update datafeed value
        await datafeed.source.fetch_new_datapoint()
        latest_data = datafeed.source.latest
        if latest_data[0] is None:
            msg = "Unable to retrieve updated datafeed value."
            return None, error_status(msg, log=logger.info)

        # Get query info & encode value to bytes
        query = datafeed.query
        query_id = query.query_id
        query_data = query.query_data
        try:
            value = query.value_type.encode(latest_data[0])
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        # Get nonce
        report_count, read_status = await self.get_num_reports_by_id(query_id)

        if not read_status.ok:
            status.error = "Unable to retrieve report count: " + read_status.error  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        # Start transaction build
        submit_val_func = self.custom_contract.contract.get_function_by_name("submitValue")
        submit_val_tx = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=report_count,
            _queryData=query_data,
        )
        acc_nonce = self.endpoint._web3.eth.get_transaction_count(address)

        # Add transaction type 2 (EIP-1559) data
        if self.transaction_type == 2:
            logger.info(f"maxFeePerGas: {self.max_fee}")
            logger.info(f"maxPriorityFeePerGas: {self.priority_fee}")

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "maxFeePerGas": Web3.toWei(self.max_fee, "gwei"),  # type: ignore
                    # TODO: Investigate more why etherscan txs using Flashbots have
                    # the same maxFeePerGas and maxPriorityFeePerGas. Example:
                    # https://etherscan.io/tx/0x0bd2c8b986be4f183c0a2667ef48ab1d8863c59510f3226ef056e46658541288 # noqa: E501
                    "maxPriorityFeePerGas": Web3.toWei(self.priority_fee, "gwei"),  # noqa: E501
                    "chainId": self.chain_id,
                }
            )
        # Add transaction type 0 (legacy) data
        else:
            # Fetch legacy gas price if not provided by user
            if not self.legacy_gas_price:
                gas_price = await self.fetch_gas_price(self.gas_price_speed)
                if not gas_price:
                    note = "Unable to fetch gas price for tx type 0"
                    return None, error_status(note, log=logger.warning)
            else:
                gas_price = self.legacy_gas_price

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "gasPrice": Web3.toWei(gas_price, "gwei"),
                    "chainId": self.chain_id,
                }
            )

        lazy_unlock_account(self.account)
        local_account = self.account.local_account
        tx_signed = local_account.sign_transaction(built_submit_val_tx)

        # Ensure reporter lock is checked again after attempting to submit val
        self.last_submission_timestamp = 0

        try:
            logger.debug("Sending submitValue transaction")
            tx_hash = self.endpoint._web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        except Exception as e:
            note = "Send transaction failed"
            return None, error_status(note, log=logger.error, e=e)

        try:
            # Confirm transaction
            tx_receipt = self.endpoint._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)

            tx_url = f"{self.endpoint.explorer}/tx/{tx_hash.hex()}"

            if tx_receipt["status"] == 0:
                msg = f"Transaction reverted. ({tx_url})"
                return tx_receipt, error_status(msg, log=logger.error)

        except Exception as e:
            note = "Failed to confirm transaction"
            return None, error_status(note, log=logger.error, e=e)

        if status.ok and not status.error:
            logger.info(f"View reported data: \n{tx_url}")
        else:
            logger.error(status)

        return tx_receipt, status
