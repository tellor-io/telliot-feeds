"""Submits price of Wrapped Ampleforth in USD to TellorX on Rinkeby."""
import asyncio

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feed_examples.cli import get_tellor_contracts
from telliot_feed_examples.feeds.wampl_usd_feed import wampl_usd_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


if __name__ == "__main__":
    cfg = TelliotConfig()

    rinkeby_endpoint = cfg.get_endpoint()

    master, oracle = get_tellor_contracts(
        private_key=cfg.main.private_key,
        chain_id=cfg.main.chain_id,  # 4: rinkeby
        endpoint=rinkeby_endpoint,
    )

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeed=wampl_usd_median_feed,
        profit_threshold=0,  # does not check profit
        gas_price=3,
    )

    asyncio.run(reporter.report_once())
