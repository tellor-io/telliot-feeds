import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional

from eth_abi.abi import decode_abi

from telliot_feeds.reporters.customized import ChainLinkFeeds
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger


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
class BackupReporter(Tellor360Reporter):
    """Backup Reporter that inherits from Tellor360Reporter and
    implements conditions when intended as backup to chainlink"""

    def __init__(
        self, chainlink_is_frozen_timeout: int, chainlink_max_price_deviation: float, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.chainlink_is_frozen_timeout = chainlink_is_frozen_timeout
        self.chainlink_max_price_deviation = chainlink_max_price_deviation

    def current_time(self) -> int:
        return round(datetime.now().timestamp())

    def get_chainlink_latest_round_data(self) -> Optional[RoundData]:
        try:
            data = self.web3.eth.call(
                {"gasPrice": 0, "to": ChainLinkFeeds[self.chain_id], "data": "0xfeaf968c"}, "latest"
            )
            latest_round_data = decode_abi(["uint80", "int256", "uint256", "uint256", "uint80"], data)
            return RoundData(*latest_round_data)
        except Exception as e:
            logger.warning(f"error getting chainlink round data: {e}")
            return None

    def get_chainlink_previous_round_data(self, latest_round_id: int) -> Optional[RoundData]:
        try:
            previous_round_id = latest_round_id - 1
            # getRoundData(uint80) sig
            function_selector = "0x9a6fc8f5"
            calldata = function_selector + f"{previous_round_id:064x}"
            data = self.web3.eth.call({"gasPrice": 0, "to": ChainLinkFeeds[self.chain_id], "data": calldata}, "latest")

            previous_round_data = decode_abi(["uint80", "int256", "uint256", "uint256", "uint80"], data)
            return RoundData(*previous_round_data)
        except Exception as e:
            logger.warning(f"error getting chainlink previous round data: {e}")
            return None

    def chainlink_price_change_above_max(
        self, chainlink_latest_round_data: RoundData, chainlink_previous_round_data: RoundData
    ) -> bool:
        current_price = chainlink_latest_round_data.answer
        previous_price = chainlink_previous_round_data.answer

        min_price = min(current_price, previous_price)
        max_price = max(current_price, previous_price)

        percent_change = (max_price - min_price) / max_price
        if percent_change > self.chainlink_max_price_deviation:
            logger.info("chainlink price change above max")
            return True
        else:
            return False

    def chainlink_is_frozen(self, chainlink_latest_round_data: RoundData) -> bool:
        current_timestamp = self.current_time()
        latest_timestamp = chainlink_latest_round_data.updatedAt
        if current_timestamp - latest_timestamp > self.chainlink_is_frozen_timeout:
            logger.info(f"chainlink is almost frozen. latest timestamp: {latest_timestamp}")
            return True
        else:
            return False

    def chainlink_is_broken(self, chainlink_latest_round_data: RoundData) -> bool:
        current_timestamp = self.current_time()
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
        if self.datafeed is None:
            logger.debug(f"no datafeed set: {self.datafeed}")
            return None
        data, status = await self.oracle.read("getDataBefore", self.datafeed.query.query_id, self.current_time())
        if not status.ok:
            logger.warning(f"error getting tellor data: {status.e}")
            return None
        return GetDataBefore(*data)

    async def conditions_met(self) -> bool:
        """Trigger methods to check conditions if reporting spot is necessary"""
        logger.info("checking conditions and reporting if necessary")
        tellor_data = await self.get_tellor_latest_data()

        current_time = self.current_time()
        time_passed_since_tellor_report = current_time - tellor_data.timestampRetrieved if tellor_data else current_time
        if (
            tellor_data is None  # if there is tellor data check chainlink feeds
            or tellor_data.retrieved is False
            # if tellor data is old check chainlink feeds
            or time_passed_since_tellor_report > self.chainlink_is_frozen_timeout
        ):
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
            logger.info("chainLink ETH/USD data is recent enough")
            return False
        else:
            logger.info("tellor ETH/USD data is recent enough")
            return False

    async def report(self, report_count: Optional[int] = None) -> None:
        """Submit values to Tellor oracles on an interval."""

        while report_count is None or report_count > 0:
            online = await self.is_online()
            if online:
                if self.has_native_token() and await self.conditions_met():
                    _, _ = await self.report_once()
            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)

            if report_count is not None:
                report_count -= 1
