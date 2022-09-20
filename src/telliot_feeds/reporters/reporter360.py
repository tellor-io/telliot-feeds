from dataclasses import dataclass
import math
import time
from datetime import timedelta
from typing import Any
from typing import Union
from typing import Tuple
from typing import Optional

from chained_accounts import ChainedAccount
from eth_utils import to_checksum_address

from telliot_core.utils.response import ResponseStatus
from telliot_core.utils.response import error_status
from telliot_core.utils.timestamp import TimeStamp
from telliot_core.contract.contract import Contract
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds import DataFeed
from telliot_feeds.utils.log import get_logger
from telliot_feeds.reporters.tellorflex import TellorFlexReporter


logger = get_logger(__name__)


@dataclass
class StakerInfo:
    """Data types for staker info
    start_date: TimeStamp
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: TimeStamp
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool
    """
    start_date: TimeStamp
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: TimeStamp
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool


class reporter360(TellorFlexReporter):
    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        oracle: Contract,
        token: Contract,
        autopay: Contract,
        stake: Optional[int] = None,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = "YOLO",
        transaction_type: int = 2,
        gas_limit: int = 350000,
        max_fee: Optional[int] = None,
        priority_fee: int = 100,
        legacy_gas_price: Optional[int] = None,
        gas_price_speed: str = "safeLow",
        wait_period: int = 7,
    ) -> None:

        self.endpoint = endpoint
        self.oracle = oracle
        self.token = token
        self.autopay = autopay
        self.stake: Optional[int] = stake  # type: ignore
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.acct_addr = to_checksum_address(account.address)
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.wait_period = wait_period
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_price_speed = gas_price_speed
        self.autopaytip = 0
        self.staked_amount: Optional[float] = None
        self.staker_info: Optional[StakerInfo] = None
        self.allowed_stake_amount = 0

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        # get oracle required stake amount
        stake, status = await self.oracle.read("getStakedAmount")

        if (not status.ok) or (stake is None):
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

        if self.stake is None:
            self.stake = stake
        else:
            msg = "Stake amount has changed due to TRB price change."
            logger.info(msg)

        if self.staker_info is None:
            self.staker_info = StakerInfo(*staker_info)
        elif self.staker_info.stake_balance > staker_info[1]:
            # update balance after depositing more stake
            self.staker_info.stake_balance = staker_info[1]
            logger.info("your staked balance has decreased and account might be in dispute")

        account_staked_bal = self.staker_info.stake_balance

        if self.stake > account_staked_bal:
            msg = (
                "Current stake is low. "
                # Add more TRB to continue reporting
                + "Approving & depositing stake."

            )
            logger.info(msg)

            gas_price_gwei = await self.fetch_gas_price()
            if gas_price_gwei is None:
                return False, error_status("Unable to fetch matic gas price for staking", log=logger.info)

            # diff in required stake and account staked balance
            stake_diff = self.stake - account_staked_bal

            # check TRB wallet balance!
            wallet_balance = self.token.read("balanceOf", account=self.acct_addr)
            logger.info(f"Current wallet TRB balance: {wallet_balance}")

            if stake_diff > wallet_balance:
                msg = "Not enough TRB in the account to cover the stake"
                return False, error_status(msg, log=logger.warning)

            txn_kwargs = {"gas_limit": 300000, "legacy_gas_price": gas_price_gwei, "_amount": stake_diff}
            # approve token spending
            _, approve_status = await self.token.write(
                func_name="approve", spender=self.oracle.address, **txn_kwargs
            )
            if not approve_status.ok:
                msg = "Unable to approve staking"
                return False, error_status(msg, log=logger.error)

            # deposit stake
            _, deposit_status = self.oracle.write(
                "depositStake", **txn_kwargs
            )
            if not deposit_status.ok:
                msg = (
                    "Unable to stake deposit: "
                    + deposit_status.error
                    + f"Make sure {self.acct_addr} has enough of the current chain's "
                    + "currency and the oracle's currency (TRB)"
                )
                return False, error_status(msg, log=logger.error)

        return True, ResponseStatus()

    async def check_reporter_lock(self) -> ResponseStatus:

        account_staked_bal = self.staker_info.stake_balance  # type: ignore
        reporter_lock = 43200 / math.floor(account_staked_bal / self.stake)  # type: ignore

        time_remaining = round(self.staker_info.last_report + reporter_lock - time.time())
        if time_remaining > 0:
            hr_min_sec = str(timedelta(seconds=time_remaining))
            msg = "Currently in reporter lock. Time left: " + hr_min_sec
            return error_status(msg, log=logger.info)

        return ResponseStatus()
