"""TellorFlex compatible reporters"""
import time
from datetime import timedelta
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

import requests
from chained_accounts import ChainedAccount
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class PolygonReporter(IntervalReporter):
    """Reports values from given datafeeds to a TellorFlex
    on Polygon."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        chain_id: int,
        oracle: Contract,
        token: Contract,
        stake: float = 10.0,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: Union[str, float] = "YOLO",
        transaction_type: int = 2,
        gas_limit: int = 350000,
        max_fee: Optional[int] = None,
        priority_fee: int = 100,
        legacy_gas_price: Optional[int] = None,
        gas_price_speed: str = "safeLow",
    ) -> None:

        self.endpoint = endpoint
        self.oracle = oracle
        self.token = token
        self.stake = stake
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.acct_addr = to_checksum_address(account.address)
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_price_speed = gas_price_speed

        logger.info(f"Reporting with account: {self.acct_addr}")

        self.account: ChainedAccount = account
        assert self.acct_addr == to_checksum_address(self.account.address)

    async def ensure_profitable(
        self,
        datafeed: DataFeed[Any],
    ) -> ResponseStatus:
        """Make profitability check always pass."""

        return ResponseStatus()

    async def fetch_gas_price(self, speed: str = "safeLow") -> int:
        """Fetch estimated gas prices for Polygon mainnet."""
        prices = requests.get("https://gasstation-mainnet.matic.network").json()

        return int(prices[speed])

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked.

        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to deposit
        the given stake amount."""
        staker_info, read_status = await self.oracle.read(
            func_name="getStakerInfo", _staker=self.acct_addr
        )

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

        # Attempt to stake
        if staker_balance / 1e18 < self.stake:
            logger.info("Current stake too low. Approving & depositing stake.")

            gas_price_gwei = await self.fetch_gas_price()
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
                    + f"Make sure {self.acct_addr} has enough MATIC & TRB (10)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.error)

            logger.info(f"Staked {amount / 1e18} TRB")

        return True, ResponseStatus()

    async def check_reporter_lock(self) -> ResponseStatus:
        """Ensure enough time has passed since last report.

        One stake is 10 TRB. Reporter lock is depends on the
        total staked:

        reporter_lock = 12hrs / # stakes

        Returns bool signifying whether a given address is in a
        reporter lock or not."""
        staker_info, read_status = await self.oracle.read(
            func_name="getStakerInfo", _staker=self.acct_addr
        )

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

        time_remaining = round(
            self.last_submission_timestamp + reporter_lock - time.time()
        )
        if time_remaining > 0:
            hr_min_sec = str(timedelta(seconds=time_remaining))
            msg = "Currently in reporter lock. Time left: " + hr_min_sec
            return error_status(msg, log=logger.info)

        return ResponseStatus()

    async def get_num_reports_by_id(
        self, query_id: bytes
    ) -> Tuple[int, ResponseStatus]:
        count, read_status = await self.oracle.read(
            func_name="getNewValueCountbyQueryId", _queryId=query_id
        )
        return count, read_status
