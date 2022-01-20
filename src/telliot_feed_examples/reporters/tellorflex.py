"""TellorFlex compatible reporters"""
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

import requests
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class PolygonReporter(IntervalReporter):
    """Reports values from given datafeeds to a TellorFlex Oracle
    on Polygon."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        private_key: str,
        chain_id: int,
        oracle: Contract,
        token: Contract,
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
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.user = self.endpoint.web3.eth.account.from_key(private_key).address
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.transaction_type = transaction_type
        self.gas_limit = gas_limit
        self.max_fee = max_fee
        self.priority_fee = priority_fee
        self.legacy_gas_price = legacy_gas_price
        self.gas_price_speed = gas_price_speed

        logger.info(f"Reporting with account: {self.user}")

        self.account: LocalAccount = Account.from_key(private_key)
        assert self.user == self.account.address

    async def ensure_profitable(
        self,
        datafeed: DataFeed[Any],
    ) -> ResponseStatus:
        """Make profitability check always pass."""

        return ResponseStatus()

    async def fetch_gas_price(self, speed: str = "safeLow") -> int:
        """Fetch estimated gas prices for Polygon mainnet."""
        prices = requests.get("https://gasstation-mainnet.matic.network").json()
        price = int(prices[speed])

        return await price  # type: ignore

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked
        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to stake with
        the address's funds."""
        staker_info, read_status = await self.oracle.read(
            func_name="getStakerInfo", _staker=self.user
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
            balance:        {staker_balance}
            locked balance: {locked_balance}
            last report:    {last_report}
            total reports:  {num_reports}
            """
        )

        self.last_submission_timestamp = last_report

        # Attempt to stake
        if staker_balance < 10:
            logger.info("Address not yet staked. Approving & depositing stake.")

            gas_price_gwei = self.fetch_gas_price()
            amount = 10 - staker_balance

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
                amount=amount,
            )
            if not write_status.ok:
                msg = (
                    "Unable to stake deposit: "
                    + write_status.error
                    + f"Make sure {self.user} has enough MATIC & TRB (10)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.error)

        return True, ResponseStatus()
