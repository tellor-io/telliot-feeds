"""TellorFlex compatible reporters"""
import asyncio
import time
from datetime import timedelta
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from chained_accounts import ChainedAccount
from eth_abi.exceptions import EncodingTypeError
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.interval import IntervalReporter
from telliot_feeds.reporters.reporter_autopay_utils import autopay_suggested_report
from telliot_feeds.reporters.reporter_autopay_utils import CATALOG_QUERY_IDS
from telliot_feeds.reporters.reporter_autopay_utils import get_feed_tip
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import get_native_token_feed
from telliot_feeds.utils.reporter_utils import tellor_suggested_report
from telliot_feeds.utils.reporter_utils import tkn_symbol


logger = get_logger(__name__)


class TellorFlexReporter(IntervalReporter):
    """Reports values from given datafeeds to a TellorFlex."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        oracle: Contract,
        token: Contract,
        autopay: Contract,
        stake: float = 10.0,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = "YOLO",
        transaction_type: int = 2,
        gas_limit: Optional[int] = None,
        max_fee: int = 0,
        priority_fee: float = 0.0,
        legacy_gas_price: Optional[int] = None,
        gas_multiplier: int = 1,  # 1 percent
        max_priority_fee_range: int = 80,  # 80 gwei
        wait_period: int = 7,
        min_native_token_balance: int = 10**18,
        check_rewards: bool = True,
        ignore_tbr: bool = False,  # relevant only for eth-mainnet and eth-testnets
    ) -> None:

        self.endpoint = endpoint
        self.oracle = oracle
        self.token = token
        self.autopay = autopay
        self.stake = stake
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
        self.gas_multiplier = gas_multiplier
        self.max_priority_fee_range = max_priority_fee_range
        self.autopaytip = 0
        self.staked_amount: Optional[float] = None
        self.qtag_selected = False if self.datafeed is None else True
        self.min_native_token_balance = min_native_token_balance
        self.check_rewards: bool = check_rewards
        self.web3 = self.endpoint.web3
        self.ignore_tbr = ignore_tbr

        self.gas_info: dict[str, Union[float, int]] = {}
        logger.info(f"Reporting with account: {self.acct_addr}")

        self.account: ChainedAccount = account
        assert self.acct_addr == to_checksum_address(self.account.address)

    async def in_dispute(self, new_stake_amount: Any) -> bool:
        """Check if staker balance decreased"""
        if self.staked_amount is not None and self.staked_amount > new_stake_amount:
            return True
        return False

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked.

        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to deposit
        the given stake amount."""
        staker_info, read_status = await self.oracle.read(func_name="getStakerInfo", _staker=self.acct_addr)

        if (not read_status.ok) or (staker_info is None):
            msg = "Unable to read reporters staker info"
            return False, error_status(msg, log=logger.info)

        (
            staker_startdate,
            staker_balance,
            locked_balance,
            last_report,
            num_reports,
        ) = staker_info

        logger.info(
            f"""

            STAKER INFO
            start date:     {staker_startdate}
            desired stake:  {self.stake}
            amount staked:  {staker_balance / 1e18}
            locked balance: {locked_balance / 1e18}
            last report:    {last_report}
            total reports:  {num_reports}
            """
        )

        self.last_submission_timestamp = last_report
        # check if staker balance has decreased after initial assignment
        if await self.in_dispute(staker_balance):
            msg = "Staked balance has decreased, account might be in dispute; restart telliot to keep reporting"
            return False, error_status(msg)
        # Attempt to stake
        if staker_balance / 1e18 < self.stake:
            logger.info("Current stake too low. Approving & depositing stake.")

            gas_price_gwei = await self.fetch_gas_price()
            if gas_price_gwei is None:
                return False, error_status("Unable to fetch gas price for staking", log=logger.info)
            amount = int(self.stake * 1e18) - staker_balance

            _, write_status = await self.token.write(
                func_name="approve",
                gas_limit=100000,
                legacy_gas_price=gas_price_gwei,
                spender=self.oracle.address,
                amount=amount,
            )
            if not write_status.ok:
                msg = "Unable to approve staking"
                return False, error_status(msg, log=logger.error)

            _, write_status = await self.oracle.write(
                func_name="depositStake",
                gas_limit=300000,
                legacy_gas_price=gas_price_gwei,
                _amount=amount,
            )
            if not write_status.ok:
                msg = (
                    "Unable to stake deposit: "
                    + write_status.error
                    + f"Make sure {self.acct_addr} has enough of the current chain's "
                    + "currency and the oracle's currency (TRB)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.error)

            logger.info(f"Staked {amount / 1e18} TRB")
            self.staked_amount = self.stake
        elif self.staked_amount is None:
            self.staked_amount = staker_balance

        return True, ResponseStatus()

    async def check_reporter_lock(self) -> ResponseStatus:
        """Ensure enough time has passed since last report.

        One stake is 10 TRB. Reporter lock is depends on the
        total staked:

        reporter_lock = 12hrs / # stakes

        Returns bool signifying whether a given address is in a
        reporter lock or not."""
        staker_info, read_status = await self.oracle.read(func_name="getStakerInfo", _staker=self.acct_addr)

        if (not read_status.ok) or (staker_info is None):
            msg = "Unable to read reporters staker info"
            return error_status(msg, log=logger.error)

        _, staker_balance, _, last_report, _ = staker_info

        if staker_balance < 10 * 1e18:
            return error_status("Staker balance too low.", log=logger.info)

        self.last_submission_timestamp = last_report
        logger.info(f"Last submission timestamp: {self.last_submission_timestamp}")

        trb = staker_balance / 1e18
        num_stakes = (trb - (trb % 10)) / 10
        reporter_lock = (12 / num_stakes) * 3600

        time_remaining = round(self.last_submission_timestamp + reporter_lock - time.time())
        if time_remaining > 0:
            hr_min_sec = str(timedelta(seconds=time_remaining))
            msg = "Currently in reporter lock. Time left: " + hr_min_sec
            return error_status(msg, log=logger.info)

        return ResponseStatus()

    async def rewards(self) -> int:
        tip = 0
        datafeed: DataFeed[Any] = self.datafeed  # type: ignore
        # Skip fetching datafeed & checking profitability
        if self.expected_profit == "YOLO":
            return tip

        single_tip, status = await self.autopay.get_current_tip(datafeed.query.query_id)
        if not status.ok:
            logger.warning("Unable to fetch single tip")
        else:
            tip += single_tip

        feed_tip = await get_feed_tip(datafeed.query.query_id, self.autopay)
        if feed_tip is None:
            logger.warning("Unable to fetch feed tip")
        else:
            tip += feed_tip

        return tip

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        """Fetches datafeed suggestion plus the reward amount from autopay if query tag isn't selected
        if query tag is selected fetches the rewards, if any, for that query tag"""
        if self.datafeed:
            # add query id to catalog to fetch tip for legacy autopay
            try:
                qid = self.datafeed.query.query_id
            except EncodingTypeError:
                logger.warning(f"Unable to generate data/id for query: {self.datafeed.query}")
                return None
            if qid not in CATALOG_QUERY_IDS:
                CATALOG_QUERY_IDS[qid] = self.datafeed.query.descriptor
            self.autopaytip = await self.rewards()
            return self.datafeed

        suggested_qtag, autopay_tip = await autopay_suggested_report(self.autopay)
        if suggested_qtag:
            self.autopaytip = autopay_tip
            self.datafeed = CATALOG_FEEDS[suggested_qtag]
            return self.datafeed

        if suggested_qtag is None:
            suggested_qtag = await tellor_suggested_report(self.oracle)
            if suggested_qtag is None:
                logger.warning("Could not suggest query tag")
                return None
            elif suggested_qtag not in CATALOG_FEEDS:
                logger.warning(f"Suggested query tag not in catalog: {suggested_qtag}")
                return None
            else:
                self.datafeed = CATALOG_FEEDS[suggested_qtag]
                self.autopaytip = await self.rewards()
                return self.datafeed
        return None

    async def ensure_profitable(self, datafeed: DataFeed[Any]) -> ResponseStatus:

        status = ResponseStatus()
        if not self.check_rewards:
            return status

        tip = self.autopaytip
        # Fetch token prices in USD
        native_token_feed = get_native_token_feed(self.chain_id)
        price_feeds = [native_token_feed, trb_usd_median_feed]
        _ = await asyncio.gather(*[feed.source.fetch_new_datapoint() for feed in price_feeds])
        price_native_token = native_token_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]

        if price_native_token is None or price_trb_usd is None:
            return error_status("Unable to fetch token price", log=logger.warning)

        if not self.gas_info:
            return error_status("Gas info not set", log=logger.warning)

        gas_info = self.gas_info

        if gas_info["type"] == 0:
            txn_fee = gas_info["gas_price"] * gas_info["gas_limit"]
            logger.info(
                f"""

                Tips: {tip/1e18}
                Transaction fee: {self.web3.fromWei(txn_fee, 'gwei'):.09f} {tkn_symbol(self.chain_id)}
                Gas price: {gas_info["gas_price"]} gwei
                Gas limit: {gas_info["gas_limit"]}
                Txn type: 0 (Legacy)
                """
            )
        if gas_info["type"] == 2:
            txn_fee = gas_info["max_fee"] * gas_info["gas_limit"]
            logger.info(
                f"""

                Tips: {tip/1e18}
                Max transaction fee: {self.web3.fromWei(txn_fee, 'gwei'):.18f} {tkn_symbol(self.chain_id)}
                Max fee per gas: {gas_info["max_fee"]} gwei
                Max priority fee per gas: {gas_info["priority_fee"]} gwei
                Gas limit: {gas_info["gas_limit"]}
                Txn type: 2 (EIP-1559)
                """
            )

        # Calculate profit
        rev_usd = tip / 1e18 * price_trb_usd
        costs_usd = txn_fee / 1e9 * price_native_token  # convert gwei costs to eth, then to usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")
        logger.info(f"tip price: {round(rev_usd, 2)}, gas costs: {costs_usd}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")
        if (self.expected_profit != "YOLO") and (
            isinstance(self.expected_profit, float) and percent_profit < self.expected_profit
        ):
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            # reset datafeed for a new suggestion if qtag wasn't selected in cli
            if self.qtag_selected is False:
                self.datafeed = None
            return status
        # reset autopay tip to check for tips again
        self.autopaytip = 0
        # reset datafeed for a new suggestion if qtag wasn't selected in cli
        if self.qtag_selected is False:
            self.datafeed = None

        return status
