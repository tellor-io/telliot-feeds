"""Helper functions for reporting data for Diva Protocol."""
import logging
from dataclasses import dataclass
from typing import Any
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.api import DataFeed
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from telliot_core.dtypes.datapoint import datetime_now_utc
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.queries.diva_protocol import DIVAProtocolPolygon
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

    return pool_params


@dataclass
class DivaSource(DataSource[Any]):
    """DataSource for Diva Protocol manually-entered data."""

    reference_asset_source: DataSource[float] = None
    collat_token_source: DataSource[float] = None

    async def fetch_new_datapoint(self) -> Optional[DataPoint[float]]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        ref_asset_price, _ = await self.reference_asset_source.fetch_new_datapoint()
        collat_token_price, _ = await self.collat_token_source.fetch_new_datapoint()
        print("ref_asset_price:", ref_asset_price)
        print("collat_token_price:", collat_token_price)

        if ref_asset_price is None or collat_token_price is None:
            logger.warning("Missing reference asset or collateral token price.")
            return None

        # ref_asset_price = 2000.0
        # collat_token_price = 0.996

        data = [int(v * 1e18) for v in [ref_asset_price, collat_token_price]]

        dt = datetime_now_utc()
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored DIVAProtocolPolygon query response at {dt}: {data}")

        return datapoint


def get_ref_asset_source(asset: str, ts: int) -> PriceAggregator:
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
        logger.error("Error getting pool parameters.")
        return None

    asset = params.reference_asset.split("/")[0].lower()
    ts = params.expiry_date

    diva_source = DivaSource()
    diva_source.reference_asset_source = get_ref_asset_source(asset, ts)
    # TODO: Remove hard coded currency. Fetch actual token address from pool params.
    diva_source.collat_token_source = PoloniexHistoricalPriceSource(
        asset=asset, currency="dai", ts=ts
    )

    feed = DataFeed(
        query=DIVAProtocolPolygon(pool_id),
        source=diva_source,
    )

    return feed
