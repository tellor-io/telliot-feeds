"""Helper functions for reporting data for Diva Protocol."""
import logging
from dataclasses import dataclass
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.api import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.queries.diva_protocol import divaProtocolPolygon
from telliot_core.tellor.tellorflex.diva import DivaProtocolContract

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


logger = logging.getLogger(__name__)


SUPPORTED_REFERENCE_ASSETS = {"ETH/USD", "BTC/USD"}


@dataclass
class DivaPoolParameters:
    """More info: https://github.com/divaprotocol/oracles#diva-smart-contract"""

    reference_asset: str
    expiry_date: int


async def get_pool_params(
    pool_id: int, node: RPCEndpoint, account: ChainedAccount
) -> Optional[DivaPoolParameters]:
    """Fetches and parses needed parameters for a given pool."""

    diva = DivaProtocolContract(node, account)
    diva.connect()

    params = await diva.get_pool_parameters(pool_id)
    if params is None:
        logger.error("Error getting pool params from Diva contract.")
        return None

    print("PARAMS:", params)
    pool_params = DivaPoolParameters(
        reference_asset=params.reference_asset, expiry_date=params.expiry_time
    )
    if pool_params.reference_asset not in SUPPORTED_REFERENCE_ASSETS:
        logger.error(f"Reference asset not supported: {pool_params.reference_asset}")
        return None

    return pool_params


def get_source(asset: str, ts: int) -> PriceAggregator:
    """Returns PriceAggregator with sources adjusted based on given asset."""
    source = PriceAggregator(
        asset=asset,
        currency="usd",
        algorithm="median",
        sources=[
            CryptowatchHistoricalPriceSource(asset=asset, currency="usd", ts=ts),
            KrakenHistoricalPriceSource(asset=asset, currency="usd", ts=ts),
            PoloniexHistoricalPriceSource(asset=asset, currency="dai", ts=ts),
            PoloniexHistoricalPriceSource(asset=asset, currency="tusd", ts=ts),
        ],
    )
    if asset == "btc":
        source.sources[1].asset = "xbt"

    return source


async def assemble_diva_datafeed(
    pool_id: int, node: RPCEndpoint, account: ChainedAccount
) -> Optional[DataFeed[float]]:
    """Returns datafeed using user input pool ID and corresponding
    asset information.

    Reference assets are currently whitelisted & hard-coded."""

    params = await get_pool_params(pool_id, node, account)
    if params is None:
        logger.error("Error getting pool parameters.")
        return None

    asset = params.reference_asset.split("/")[0].lower()
    ts = params.expiry_date

    feed = DataFeed(
        query=divaProtocolPolygon(pool_id),
        source=get_source(asset, ts),
    )

    return feed
