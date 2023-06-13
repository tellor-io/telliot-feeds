import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Optional

from eth_abi.abi import decode_abi

from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import current_time

logger = get_logger(__name__)


@dataclass
class RoundData:
    roundId: int
    answer: int
    startedAt: int
    updatedAt: int
    answeredInRound: int


@dataclass
class GetDataBefore:
    retrieved: bool
    value: bytes
    timestampRetrieved: int


@dataclass
class ChainlinkBackupReporter(Tellor360Reporter):
    """Backup Reporter that inherits from Tellor360Reporter and
    implements conditions when intended as backup to chainlink"""

    def __init__(
        self,
        chainlink_is_frozen_timeout: int,
        chainlink_max_price_change: float,
        chainlink_feed: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.chainlink_is_frozen_timeout = chainlink_is_frozen_timeout
        self.chainlink_max_price_change = chainlink_max_price_change
        self.chainlink_feed = chainlink_feed

    def get_chainlink_latest_round_data(self) -> Optional[RoundData]:
        """Get latest round data from chainlink feed

        Returns:
        - Optional[RoundData]: latest round data from chainlink feed
        """
        try:
            data = self.web3.eth.call({"gasPrice": 0, "to": self.chainlink_feed, "data": "0xfeaf968c"}, "latest")
            latest_round_data = decode_abi(["uint80", "int256", "uint256", "uint256", "uint80"], data)
            return RoundData(*latest_round_data)
        except Exception as e:
            if "Tried to read 32 bytes.  Only got 0 bytes" in str(e):
                msg = f"Make sure you're using the correct chainlink feed address {self.chainlink_feed}: {e}"
                logger.warning(msg)
            else:
                logger.warning(f"error getting chainlink latest round data: {e}")
            return None

    def get_chainlink_previous_round_data(self, latest_round_id: int) -> Optional[RoundData]:
        """Get previous round data from chainlink feed
        param:
        - latest_round_id: latest round id from chainlink feed
        Returns:
        - Optional[RoundData]: previous round data from chainlink feed
        """
        try:
            previous_round_id = latest_round_id - 1
            # getRoundData(uint80) sig
            function_selector = "0x9a6fc8f5"
            calldata = function_selector + f"{previous_round_id:064x}"
            data = self.web3.eth.call({"gasPrice": 0, "to": self.chainlink_feed, "data": calldata}, "latest")

            previous_round_data = decode_abi(["uint80", "int256", "uint256", "uint256", "uint80"], data)
            return RoundData(*previous_round_data)
        except Exception as e:
            logger.warning(f"error getting chainlink previous round data: {e}")
            return None

    def chainlink_price_change_above_max(
        self, chainlink_latest_round_data: RoundData, chainlink_previous_round_data: RoundData
    ) -> bool:
        """Check if price change between latest and previous round is above max price deviation
        params:
        - chainlink_latest_round_data: latest round data from chainlink feed
        - chainlink_previous_round_data: previous round data from chainlink feed

        Returns:
        - bool: True if price change is above max price deviation, False otherwise
        """
        current_price = chainlink_latest_round_data.answer
        previous_price = chainlink_previous_round_data.answer

        min_price = min(current_price, previous_price)
        max_price = max(current_price, previous_price)

        percent_change = (max_price - min_price) / max_price
        if percent_change > self.chainlink_max_price_change:
            logger.info("chainlink price change above max")
            return True
        else:
            return False

    def chainlink_is_frozen(self, chainlink_latest_round_data: RoundData) -> bool:
        """Check if chainlink is frozen based on latest round data

        params:
        - chainlink_latest_round_data: latest round data from chainlink feed

        Returns:
        - bool: True if chainlink is data is stale, False otherwise
        """
        current_timestamp = current_time()
        latest_timestamp = chainlink_latest_round_data.updatedAt
        if current_timestamp - latest_timestamp > self.chainlink_is_frozen_timeout:
            logger.info(f"chainlink is almost frozen. latest timestamp: {latest_timestamp}")
            return True
        else:
            return False

    def chainlink_is_broken(self, chainlink_latest_round_data: RoundData) -> bool:
        """Check if chainlink is broken based on latest round data ie returns 0 for any of the fields

        params:
        - chainlink_latest_round_data: latest round data from chainlink feed

        Returns:
        - bool: True if chainlink is broken, False otherwise
        """
        current_timestamp = current_time()
        round_id = chainlink_latest_round_data.roundId
        updated_at = chainlink_latest_round_data.updatedAt
        answer = chainlink_latest_round_data.answer
        if round_id == 0:
            logger.info(f"chainlink is broken. round id: {round_id}")
            return True
        if updated_at == 0 or int(updated_at) > current_timestamp:
            logger.info(f"chainlink is broken. updated at: {updated_at}")
            return True
        if answer == 0:
            logger.info(f"chainlink is broken. answer: {answer}")
            return True
        return False

    async def get_tellor_latest_data(self) -> Optional[GetDataBefore]:
        """Get latest data from tellor oracle (getDataBefore with current time)

        Returns:
        - Optional[GetDataBefore]: latest data from tellor oracle
        """
        if self.datafeed is None:
            logger.debug(f"no datafeed set: {self.datafeed}")
            return None
        data, status = await self.oracle.read("getDataBefore", self.datafeed.query.query_id, current_time())
        if not status.ok:
            logger.warning(f"error getting tellor data: {status.e}")
            return None
        return GetDataBefore(*data)

    async def conditions_met(self) -> bool:
        """Trigger methods to check conditions if reporting spot is necessary

        Returns:
        - bool: True if conditions are met, False otherwise
        """
        logger.info("checking conditions and reporting if necessary")
        if self.datafeed is None:
            logger.debug(f"no datafeed was setß: {self.datafeed}")
            return False
        tellor_data = await self.get_tellor_latest_data()
        time = current_time()
        time_passed_since_tellor_report = time - tellor_data.timestampRetrieved if tellor_data else time
        if tellor_data is None:
            logger.debug("tellor data returned None")
        elif not tellor_data.retrieved:
            logger.debug(f"No oracle submissions in tellor for query: {self.datafeed.query.descriptor}")
        elif time_passed_since_tellor_report > self.chainlink_is_frozen_timeout:
            logger.debug(f"tellor data is stale, time elapsed since last report: {time_passed_since_tellor_report}")
        else:
            logger.info(f"tellor {self.datafeed.query.descriptor} data is recent enough")
            return False

        chainlink_latest_round_data = self.get_chainlink_latest_round_data()

        if chainlink_latest_round_data is None:
            return True
        if self.chainlink_is_broken(chainlink_latest_round_data):
            return True
        if self.chainlink_is_frozen(chainlink_latest_round_data):
            return True
        chainlink_previous_round_data = self.get_chainlink_previous_round_data(chainlink_latest_round_data.roundId)

        if chainlink_previous_round_data is None:
            return True

        if self.chainlink_price_change_above_max(chainlink_latest_round_data, chainlink_previous_round_data):
            return True
        logger.info(f"chainLink {self.datafeed.query.descriptor} data is recent enough")
        return False

    async def report(self, report_count: Optional[int] = None) -> None:
        """Submit values to Tellor oracles on an interval."""

        while report_count is None or report_count > 0:
            online = await self.is_online()
            if online:
                if self.has_native_token():
                    if await self.conditions_met():
                        _, _ = await self.report_once()
                    else:
                        logger.info("feeds are recent enough, no need to report")

            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)

            if report_count is not None:
                report_count -= 1
