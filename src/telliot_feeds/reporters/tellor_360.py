import math
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from typing import Optional
from typing import Tuple

from eth_utils import to_checksum_address
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.feeds import DataFeed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.tellor_flex import TellorFlexReporter
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import suggest_random_feed

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

    start_date: int
    stake_balance: int
    locked_balance: int
    reward_debt: int
    last_report: int
    reports_count: int
    gov_vote_count: int
    vote_count: int
    in_total_stakers: bool


class Tellor360Reporter(TellorFlexReporter):
    def __init__(self, stake: float = 0, use_random_feeds: bool = False, *args: Any, **kwargs: Any) -> None:
        self.stake_amount: Optional[int] = None
        self.staker_info: Optional[StakerInfo] = None
        self.allowed_stake_amount = 0
        super().__init__(*args, **kwargs)
        self.stake: float = stake
        self.use_random_feeds: bool = use_random_feeds

        assert self.acct_addr == to_checksum_address(self.account.address)

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Compares stakeAmount and stakerInfo every loop to monitor changes to the stakeAmount or stakerInfo
        and deposits stake if needed for continuous reporting

        Return:
        - (bool, ResponseStatus)
        """
        # get oracle required stake amount
        stake_amount: int
        stake_amount, status = await self.oracle.read("getStakeAmount")

        if (not status.ok) or (stake_amount is None):
            msg = "Unable to read current stake amount"
            return False, error_status(msg, log=logger.info)

        logger.info(f"Current Oracle stakeAmount: {stake_amount / 1e18!r}")

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
            _, approve_status = await self.token.write(
                func_name="approve", spender=self.oracle.address, amount=stake_diff, **txn_kwargs
            )
            if not approve_status.ok:
                msg = "Unable to approve staking"
                return False, error_status(msg, log=logger.error)
            # deposit stake
            _, deposit_status = await self.oracle.write("depositStake", _amount=stake_diff, **txn_kwargs)

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

    async def check_reporter_lock(self) -> ResponseStatus:
        """Checks reporter lock time to determine when reporting is allowed

        Return:
        - ResponseStatus: yay or nay
        """
        if self.staker_info is None or self.stake_amount is None:
            msg = "Unable to calculate reporter lock remaining time"
            return error_status(msg, log=logger.info)

        # 12hrs in seconds is 43200
        reporter_lock = 43200 / math.floor(self.staker_info.stake_balance / self.stake_amount)

        time_remaining = round(self.staker_info.last_report + reporter_lock - time.time())
        if time_remaining > 0:
            hr_min_sec = str(timedelta(seconds=time_remaining))
            msg = "Currently in reporter lock. Time left: " + hr_min_sec
            return error_status(msg, log=logger.info)

        return ResponseStatus()

    async def rewards(self) -> int:
        """Fetches total time based rewards plus tips for current datafeed"""
        time_based_rewards: int = 0
        fetch_autopay_tip: int = 0
        total_rewards: int = 0

        if self.datafeed is not None:
            fetch_autopay_tip = await fetch_feed_tip(self.autopay, self.datafeed.query.query_id)
            if fetch_autopay_tip is not None:
                total_rewards += fetch_autopay_tip

        if self.chain_id in (1, 5):
            time_based_rewards = await get_time_based_rewards(self.oracle)
            if time_based_rewards is not None:
                total_rewards += time_based_rewards

        return total_rewards

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        """Fetches datafeed

        If the user did not select a query tag, there will have been no datafeed passed to
        the reporter upon instantiation.
        If the user uses the random feeds flag, the datafeed will be chosen randomly.
        If the user did not select a query tag or use the random feeds flag, the datafeed will
        be chosen based on the most funded datafeed in the AutoPay contract.

        If the no-rewards-check flag is used, the reporter will not check profitability or
        available tips for the datafeed unless the user has not selected a query tag or
        used the random feeds flag.
        """
        if self.use_random_feeds:
            self.datafeed = suggest_random_feed()

        # Fetch datafeed based on whichever is most funded in the AutoPay contract
        if self.datafeed is None:
            suggested_feed, tip_amount = await get_feed_and_tip(self.autopay)

            if suggested_feed is not None:
                self.autopaytip = tip_amount  # type: ignore
                self.datafeed = suggested_feed
                return self.datafeed

        # TODO: This should be removed and moved to profit check method perhaps
        if self.check_rewards:
            self.autopaytip = await self.rewards()

        return self.datafeed
