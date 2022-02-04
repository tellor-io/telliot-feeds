"""Helper functions for reporting data for Diva Protocol."""
import logging
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.api import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.queries.diva_protocol import divaProtocolPolygon
from telliot_core.tellor.tellorflex.diva import DivaProtocolContract

from telliot_feed_examples.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed


logger = logging.getLogger(__name__)


DATAFEED_LOOKUP = {
    "ETH/USD": eth_usd_median_feed,
    "BTC/USD": btc_usd_median_feed,
}


async def assemble_diva_datafeed(
    pool_id: int, node: RPCEndpoint, account: ChainedAccount
) -> Optional[DataFeed[float]]:
    """Returns datafeed using user input option ID and corresponding
    asset information."""

    diva = DivaProtocolContract(node, account)
    diva.connect()

    params = await diva.get_pool_parameters(pool_id)
    if params is None:
        logger.error("Could not assemble diva datafeed: error getting pool params.")
        return None

    asset = params[0]
    feed = DATAFEED_LOOKUP[asset]
    if feed is None:
        logger.error(
            "Could not assemble diva datafeed: error"
            f"getting feed based on asset: {asset}"
        )
    feed.query = divaProtocolPolygon(pool_id)

    return feed
