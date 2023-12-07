import asyncio
from unittest.mock import Mock, MagicMock
from typing import Any
from telliot_feeds.feeds import DataFeed

import asyncio
import math
import time
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from eth_abi.exceptions import EncodingTypeError
from eth_utils import to_checksum_address
from telliot_core.contract.contract import Contract
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3.contract import ContractFunction
from web3.types import TxParams
from web3.types import TxReceipt

from telliot_feeds.constants import CHAINS_WITH_TBR
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.reporters.rewards.time_based_rewards import get_time_based_rewards
from telliot_feeds.reporters.stake import Stake
from telliot_feeds.reporters.tips.suggest_datafeed import get_feed_and_tip
from telliot_feeds.reporters.tips.tip_amount import fetch_feed_tip
from telliot_feeds.reporters.types import GasParams
from telliot_feeds.reporters.types import StakerInfo
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import get_native_token_feed
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.reporter_utils import suggest_random_feed
from telliot_feeds.utils.reporter_utils import tkn_symbol
from telliot_feeds.utils.stake_info import StakeInfo

logger = get_logger(__name__)

class MockReporter:
    def __init__(self):
        self.autopay = Mock()
        self.datafeed = None
        self.use_random_feeds = False
        self.check_rewards = True
        self.autopaytip = 0

    async def rewards(self):
        return 0

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
        # reset autopay tip every time fetch_datafeed is called
        # so that tip is checked fresh every time and not carry older tips
        self.autopaytip = 0
        # TODO: This should be removed and moved to profit check method perhaps
        if self.check_rewards:
            # calculate tbr and
            _ = await self.rewards()

        if self.use_random_feeds:
            self.datafeed = suggest_random_feed()

        # Fetch datafeed based on whichever is most funded in the AutoPay contract
        if self.datafeed is None:
            suggested_feed, tip_amount = await get_feed_and_tip(self.autopay)

            if suggested_feed is not None and tip_amount is not None:
                logger.info(f"Most funded datafeed in Autopay: {suggested_feed.query.type}")
                logger.info(f"Tip amount: {self.to_ether(tip_amount)}")
                self.autopaytip += tip_amount

                self.datafeed = suggested_feed
                return self.datafeed

        return self.datafeed

# Now you can create an instance of MockReporter and call fetch_datafeed
reporter = MockReporter()
datafeed = asyncio.run(reporter.fetch_datafeed())