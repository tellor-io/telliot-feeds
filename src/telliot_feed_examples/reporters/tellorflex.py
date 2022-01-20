"""TellorFlex compatible reporters"""
from typing import Any
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus

from web3.datastructures import AttributeDict
from eth_account.signers.local import LocalAccount
from eth_account.account import Account


from telliot_feed_examples.utils.log import get_logger
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_core.utils.response import error_status
import requests


logger = get_logger(__name__)



class PolygonReporter(IntervalReporter):
    """Reports values from given datafeeds to a TellorFlex Oracle
    on Polygon."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        private_key: str,
        chain_id: int,
        oracle_contract: Contract,
        token_contract: Contract,
        datafeed: Optional[DataFeed[Any]] = None,
        expected_profit: float = 100.0,
        transaction_type: int = 2,
        gas_limit: int = 350000,
        max_fee: Optional[int] = None,
        priority_fee: int = 100,
        legacy_gas_price: Optional[int] = None,
        gas_price_speed: str = "fast",
    ) -> None:

        self.endpoint = endpoint
        self.oracle_contract = oracle_contract
        self.token_contract = token_contract
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
    
    async def fetch_gas_price(self, speed: str = "average") -> int:
        """Fetch estimated gas prices for Polygon mainnet."""
        prices = await requests.get('https://gasstation-mainnet.matic.network').json()

        return int(prices[speed])

    async def ensure_staked(self) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked
        Returns a bool signifying whether the current address is
        staked. If the address is not initially, it attempts to stake with
        the address's funds."""
        status = ResponseStatus()

        gas_price_gwei = await self.fetch_gas_price()

        staker_info, read_status = await self.master.read(
            func_name="getStakerInfo", _staker=self.user
        )

        if (not read_status.ok) or (staker_info is None):
            status.ok = False
            status.error = (
                "Unable to read reporters staker status: " + read_status.error
            )  # error won't be none # noqa: E501
            status.e = read_status.e
            return False, status

        logger.info(f"Stake status: {staker_info[0]}")

        # Status 1: staked
        if staker_info[0] == 1:
            return True, status

        # Status 0: not yet staked
        elif staker_info[0] == 0:
            logger.info("Address not yet staked. Depositing stake.")

            _, write_status = await self.master.write_with_retry(
                func_name="depositStake",
                gas_limit=350000,
                legacy_gas_price=gas_price_gwei,
                extra_gas_price=20,
                retries=5,
            )

            if write_status.ok:
                return True, status
            else:
                msg = (
                    "Unable to stake deposit: "
                    + write_status.error
                    + f"Make sure {self.user} has enough ETH & TRB (100)"
                )  # error won't be none # noqa: E501
                return False, error_status(msg, log=logger.info)

        # Status 3: disputed
        if staker_info[0] == 3:
            msg = "Current address disputed. Switch address to continue reporting."  # noqa: E501
            return False, error_status(msg, log=logger.info)

        # Statuses 2, 4, and 5: stake transition
        else:
            msg = (
                "Current address is locked in dispute or for withdrawal."  # noqa: E501
            )
            return False, error_status(msg, log=logger.info)