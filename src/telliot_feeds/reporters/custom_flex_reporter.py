"""TellorFlex compatible reporters"""
from typing import Any
from typing import Optional
from typing import Tuple

from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict

from telliot_feeds.reporters.tellor_360 import StakerInfo
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class CustomFlexReporter(Tellor360Reporter):
    """Use custom contract to report through to tellorflex."""

    def __init__(self, custom_contract: Contract, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.custom_contract = custom_contract

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Compares stakeAmount and stakerInfo every loop to monitor changes to the stakeAmount or stakerInfo
        and deposits stake if needed for continuous reporting

        Return:
        - (bool, ResponseStatus)
        """
        # get oracle required stake amount
        stake_amount: int
        stake_amount, status = await self.oracle.read("getStakeAmount")
        logger.info(f"Current Oracle stakeAmount: {stake_amount / 1e18!r}")

        if (not status.ok) or (stake_amount is None):
            msg = "Unable to read current stake amount"
            return False, error_status(msg, log=logger.info)

        # get accounts current stake total
        staker_info, status = await self.oracle.read(
            "getStakerInfo",
            _stakerAddress=self.acct_addr,
        )
        if (not status.ok) or (staker_info is None):
            msg = "Unable to read reporters staker info"
            return False, error_status(msg, log=logger.info)

        # first when reporter start set stakerInfo
        if self.staker_info is None:
            self.staker_info = StakerInfo(*staker_info)

        # on subsequent loops keeps checking if staked balance in oracle contract decreased
        # if it decreased account is probably dispute barring withdrawal
        if self.staker_info.stake_balance > staker_info[1]:
            # update balance in script
            self.staker_info.stake_balance = staker_info[1]
            logger.info("your staked balance has decreased and account might be in dispute")

        # after the first loop keep track of the last report's timestamp to calculate reporter lock
        self.staker_info.last_report = staker_info[4]
        self.staker_info.reports_count = staker_info[5]

        logger.info(
            f"""
            STAKER INFO
            start date: {staker_info[0]}
            stake_balance: {staker_info[1] / 1e18!r}
            locked_balance: {staker_info[2]}
            last report: {staker_info[4]}
            reports count: {staker_info[5]}
            """
        )

        account_staked_bal = self.staker_info.stake_balance

        # after the first loop, logs if stakeAmount has increased or decreased
        if self.stake_amount is not None:
            if self.stake_amount < stake_amount:
                logger.info("Stake amount has increased possibly due to TRB price change.")
            elif self.stake_amount > stake_amount:
                logger.info("Stake amount has decreased possibly due to TRB price change.")

        self.stake_amount = stake_amount

        # deposit stake if stakeAmount in oracle is greater than account stake or
        # a stake in cli is selected thats greater than account stake
        if self.stake_amount > account_staked_bal or (self.stake * 1e18) > account_staked_bal:
            logger.info("Approving and depositing stake...")

            gas_price_gwei = await self.fetch_gas_price()
            if gas_price_gwei is None:
                return False, error_status("Unable to fetch gas price for staking", log=logger.info)

            # amount to deposit whichever largest difference either chosen stake or stakeAmount to keep reporting
            stake_diff = max(int(self.stake_amount - account_staked_bal), int((self.stake * 1e18) - account_staked_bal))

            # check TRB wallet balance!
            wallet_balance, wallet_balance_status = await self.token.read("balanceOf", account=self.acct_addr)

            if not wallet_balance_status.ok:
                msg = "unable to read account TRB balance"
                return False, error_status(msg, log=logger.info)

            logger.info(f"Current wallet TRB balance: {wallet_balance / 1e18!r}")

            if stake_diff > wallet_balance:
                msg = "Not enough TRB in the account to cover the stake"
                return False, error_status(msg, log=logger.warning)

            txn_kwargs = {"gas_limit": 350000, "legacy_gas_price": gas_price_gwei}

            # approve token spending
            _, approve_status = await self.custom_contract.write(func_name="approve", _amount=stake_diff, **txn_kwargs)
            if not approve_status.ok:
                msg = "Unable to approve staking"
                return False, error_status(msg, log=logger.error)
            # deposit stake
            _, deposit_status = await self.custom_contract.write("depositStake", _amount=stake_diff, **txn_kwargs)

            if not deposit_status.ok:
                msg = (
                    "Unable to stake deposit: "
                    + deposit_status.error
                    + f"Make sure {self.acct_addr} has enough of the current chain's "
                    + "currency and the oracle's currency (TRB)"
                )
                return False, error_status(msg, log=logger.error)
            # add staked balance after successful stake deposit
            self.staker_info.stake_balance += stake_diff

        return True, ResponseStatus()

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
            # Reset previous submission timestamp
            self.last_submission_timestamp = 0
            # Point to relevant explorer
            logger.info(f"View reported data: \n{tx_url}")
        else:
            logger.error(status)

        return tx_receipt, status
