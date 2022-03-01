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
from telliot_feed_examples.sources.price.historical.cryptowatch import (
    CryptowatchHistoricalPriceSource,
)
from telliot_feed_examples.sources.price.historical.kraken import (
    KrakenHistoricalPriceSource,
)
from telliot_feed_examples.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceSource,
)
from telliot_feed_examples.sources.price_aggregator import PriceAggregator

# from telliot_feed_examples.sources.diva_protocol import DivaManualSource


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

    ref_asset = params[0].lower()  # Reference asset
    if "eth" in ref_asset:
        asset = "eth"
    elif "btc" in ref_asset:
        asset = "btc"
    else:
        logger.warning("Reference asset not supported")
        return None

    ts = params[8]  # Expiry date
    feed = DataFeed(
        query=divaProtocolPolygon(pool_id),
        # source=DivaManualSource(reference_asset=asset, timestamp=ts),
        source=PriceAggregator(
            asset=asset,
            currency="usd",
            algorithm="median",
            sources=[
                CryptowatchHistoricalPriceSource(asset=asset, currency="usd", ts=ts),
                KrakenHistoricalPriceSource(asset=asset, currency="usd", ts=ts),
                PoloniexHistoricalPriceSource(asset=asset, currency="dai", ts=ts),
                PoloniexHistoricalPriceSource(asset=asset, currency="tusd", ts=ts),
            ],
        ),
    )

    return feed
