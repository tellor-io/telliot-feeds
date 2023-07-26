import time
from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.reporters.gas import GasFees
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class Stake(GasFees):
    """Stake tokens to tellor oracle"""

    def __init__(
        self,
        oracle: Contract,
        token: Contract,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.oracle = oracle
        self.token = token

    async def get_current_token_balance(self) -> Tuple[Optional[int], ResponseStatus]:
        """Reads the current balance of the account"""
        wallet_balance: int
        wallet_balance, status = await self.token.read("balanceOf", account=self.acct_address)
        if not status.ok:
            msg = f"Unable to read account balance: {status.error}"
            return None, error_status(msg, status.e, log=logger.error)

        logger.info(f"Current wallet TRB balance: {self.to_ether(wallet_balance)!r}")
        return wallet_balance, status

    async def check_allowance(self, amount: int) -> Tuple[Optional[int], ResponseStatus]:
        """ "Read the spender allowance for the accounts TRB"""
        allowance, allowance_status = await self.token.read(
            "allowance", owner=self.acct_address, spender=self.oracle.address
        )
        if not allowance_status.ok:
            msg = "Unable to check allowance:"
            return None, error_status(msg, e=allowance_status.error, log=logger.error)

        logger.debug(f"Current allowance: {self.to_ether(allowance):.04f}")
        return allowance, allowance_status

    async def approve_spending(self, amount: int) -> Tuple[bool, ResponseStatus]:
        """Approve contract to spend TRB tokens"""
        logger.info(f"Approving {self.oracle.address} token spending: {amount}...")
        # calculate and set gas params
        status = self.update_gas_fees()
        if not status.ok:
            return False, error_status("unable to calculate fees for approve txn", e=status.error, log=logger.error)
        fees = self.get_gas_info_core()

        approve_receipt, approve_status = await self.token.write(
            func_name="approve",
            # have to convert to gwei because of telliot_core where numbers are converted to wei
            # consider changing this in telliot_core
            spender=self.oracle.address,
            amount=amount,
            **fees,
        )
        if not approve_status.ok:
            msg = "Unable to approve staking: "
            return False, error_status(msg, e=approve_status.error, log=logger.error)
        logger.debug(f"Approve transaction status: {approve_receipt.status}, block: {approve_receipt.blockNumber}")
        return True, approve_status

    async def deposit_stake(self, amount: int) -> Tuple[bool, ResponseStatus]:
        """Deposits stake into the oracle contract"""
        # check TRB wallet balance!
        wallet_balance, wallet_balance_status = await self.get_current_token_balance()
        if wallet_balance is None or not wallet_balance_status.ok:
            return False, wallet_balance_status

        if amount > wallet_balance:
            msg = (
                f"Amount to stake: {self.to_ether(amount):.04f} "
                f"is greater than your balance: {self.to_ether(wallet_balance):.04f} so "
                "not enough TRB to cover the stake"
            )
            return False, error_status(msg, log=logger.warning)

        # check allowance to avoid unnecessary approval transactions
        allowance, allowance_status = await self.check_allowance(amount)
        if allowance is None or not allowance_status.ok:
            return False, allowance_status

        # if allowance is less than amount_to_stake then approve
        if allowance < amount:
            approve_receipt, approve_status = await self.approve_spending(amount - allowance)
            if not approve_receipt or not approve_status.ok:
                return False, approve_status
            # Add this to avoid nonce error from txn happening too fast
            time.sleep(1)

        # deposit stake
        logger.info(f"Now depositing stake: {amount}...")
        # calculate and set gas params
        status = self.update_gas_fees()
        if not status.ok:
            return False, error_status("unable to calculate fees for deposit txn", e=status.error, log=logger.error)

        fees = self.get_gas_info_core()
        deposit_receipt, deposit_status = await self.oracle.write(
            func_name="depositStake",
            _amount=amount,
            **fees,
        )
        if not deposit_status.ok:
            msg = "Unable to deposit stake!"
            return False, error_status(msg, e=deposit_status.error, log=logger.error)
        logger.debug(f"Deposit transaction status: {deposit_receipt.status}, block: {deposit_receipt.blockNumber}")
        return True, deposit_status
