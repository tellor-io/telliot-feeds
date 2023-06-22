import time
from typing import Any
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

    async def deposit_stake(self, amount: int) -> Tuple[bool, ResponseStatus]:
        """Deposits stake into the oracle contract"""
        # check allowance to avoid unnecessary approval transactions
        allowance, allowance_status = await self.token.read(
            "allowance", owner=self.acct_address, spender=self.oracle.address
        )
        if not allowance_status.ok:
            msg = "Unable to check allowance:"
            return False, error_status(msg, e=allowance_status.error, log=logger.error)

        logger.debug(f"Current allowance: {allowance / 1e18!r}")
        # calculate and set gas params
        status = self.update_gas_fees()
        if not status.ok:
            return False, error_status("unable to calculate fees for approve txn", e=status.error, log=logger.error)

        fees = self.get_gas_info_core()
        # if allowance is less than amount_to_stake then approve
        if allowance < amount:
            # Approve token spending
            logger.info(f"Approving {self.oracle.address} token spending: {amount}...")
            approve_receipt, approve_status = await self.token.write(
                func_name="approve",
                gas_limit=self.gas_limit,
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
            gas_limit=self.gas_limit,
            _amount=amount,
            **fees,
        )
        if not deposit_status.ok:
            msg = "Unable to deposit stake!"
            return False, error_status(msg, e=deposit_status.error, log=logger.error)
        logger.debug(f"Deposit transaction status: {deposit_receipt.status}, block: {deposit_receipt.blockNumber}")
        return True, deposit_status
