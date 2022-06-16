"""Helper functions for reporting data for Diva Protocol."""
import logging
import random
from dataclasses import dataclass
from typing import Any
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.datasource import DataSource
from telliot_feed_examples.dtypes.datapoint import DataPoint
from telliot_feed_examples.dtypes.datapoint import datetime_now_utc
from telliot_core.model.endpoints import RPCEndpoint
from telliot_feed_examples.queries.diva_protocol import DIVAProtocolPolygon
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
# Maps token address to token name
SUPPORTED_COLLATERAL_TOKENS = {
    "0xc778417E063141139Fce010982780140Aa0cD5Ab": "BTC",
    "0x134e62bd2ee247d4186A1fdbaA9e076cb26c1355": "DIVA USD",
}

# Ropsten whitelist
# Source: https://github.com/divaprotocol/oracles#whitelist-subgraph
# SUPPORTED_COLLATERAL_TOKENS = {
#     "0xad6d458402f60fd3bd25163575031acdce07538d": "DAI",
#     "0xc778417e063141139fce010982780140aa0cd5ab": "WETH",
#     }


@dataclass
class DivaPoolParameters:
    """More info: https://github.com/divaprotocol/oracles#diva-smart-contract"""

    reference_asset: str
    expiry_date: int
    collateral_token: str


async def get_pool_params(
    pool_id: int,
    node: RPCEndpoint,
    account: ChainedAccount,
    diva_address: Optional[str] = None,
) -> Optional[DivaPoolParameters]:
    """Fetches and parses needed parameters for a given pool."""

    diva = DivaProtocolContract(node, account)
    if diva_address is not None:
        diva.address = diva_address
    diva.connect()

    params = await diva.get_pool_parameters(pool_id)
    if params is None:
        logger.error("Error getting pool params from Diva contract.")
        return None

    pool_params = DivaPoolParameters(
        reference_asset=params.reference_asset,
        expiry_date=params.expiry_time,
        collateral_token=params.collateral_token,
    )

    if pool_params.reference_asset not in SUPPORTED_REFERENCE_ASSETS:
        logger.error(f"Reference asset not supported: {pool_params.reference_asset}")
        return None
    if pool_params.collateral_token not in SUPPORTED_COLLATERAL_TOKENS:
        logger.error(f"Collateral token not supported: {pool_params.collateral_token}")
        return None

    return pool_params


@dataclass
class DivaSource(DataSource[Any]):
    """DataSource for Diva Protocol manually-entered data."""

    reference_asset_source: DataSource[float] = None
    collat_token_source: DataSource[float] = None

    async def fetch_new_datapoint(self) -> Optional[DataPoint[float]]:
        """Retrieve new datapoint from sources."""

        ref_asset_price, _ = await self.reference_asset_source.fetch_new_datapoint()
        collat_token_price, _ = await self.collat_token_source.fetch_new_datapoint()

        if ref_asset_price is None or collat_token_price is None:
            logger.warning("Missing reference asset or collateral token price.")
            return None

        data = [ref_asset_price, collat_token_price]
        dt = datetime_now_utc()
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored DIVAProtocolPolygon query response at {dt}: {data}")

        return datapoint


class DIVAUSDSource(DataSource[Any]):
    """Fake source that returns dummy price data"""

    async def fetch_new_datapoint(self) -> Optional[DataPoint[float]]:
        """Fetch fake data"""
        data = random.uniform(69, 420)
        dt = datetime_now_utc()
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored fake price for DIVA USD at {dt}: {data}")

        return datapoint


def get_variable_source(asset: str, ts: int) -> PriceAggregator:
    """Returns PriceAggregator with sources adjusted based on given asset."""
    if asset == "diva usd":
        return DIVAUSDSource()

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
    pool_id: int,
    node: RPCEndpoint,
    account: ChainedAccount,
    diva_address: Optional[str] = None,
) -> Optional[DataFeed[float]]:
    """Returns datafeed using user input pool ID and corresponding
    asset information.

    Reference assets are currently whitelisted & hard-coded."""

    params = await get_pool_params(pool_id, node, account, diva_address)
    if params is None:
        logger.error("Unable to retrieve pool parameters")
        return None

    ts = params.expiry_date
    ref_asset_token_name = params.reference_asset.split("/")[0].lower()
    collat_token_name = SUPPORTED_COLLATERAL_TOKENS[params.collateral_token].lower()

    diva_source = DivaSource()
    diva_source.reference_asset_source = get_variable_source(ref_asset_token_name, ts)
    diva_source.collat_token_source = get_variable_source(collat_token_name, ts)

    feed = DataFeed(
        query=DIVAProtocolPolygon(pool_id),
        source=diva_source,
    )

    return feed
