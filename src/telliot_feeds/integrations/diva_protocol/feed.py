"""Helper functions for reporting data for Diva Protocol."""
from typing import Optional

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import SUPPORTED_COLLATERAL_TOKEN_SYMBOLS
from telliot_feeds.integrations.diva_protocol import SUPPORTED_HISTORICAL_PRICE_PAIRS
from telliot_feeds.integrations.diva_protocol.pool import DivaPool
from telliot_feeds.integrations.diva_protocol.sources import DivaSource
from telliot_feeds.integrations.diva_protocol.sources import get_historical_price_source
from telliot_feeds.integrations.diva_protocol.utils import parse_reference_asset
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def assemble_diva_datafeed(
    pool: DivaPool, diva_diamond: str = DIVA_DIAMOND_ADDRESS, chain_id: int = 5
) -> Optional[DataFeed[float]]:
    """
    Assemble DataFeed based on given pool parameters.

    Args:
        pool: DIVA Protocol pool to assemble DataFeed for.

    Returns:
        DataFeed for given pool.
    """
    ref_asset, ref_currency = parse_reference_asset(pool.reference_asset)
    if ref_asset is None or ref_currency is None:
        logger.error("Unable to assemble DIVA datafeed")
        return None

    # Filter out unsupported asset/currency pairs
    if pool.reference_asset not in SUPPORTED_HISTORICAL_PRICE_PAIRS:
        logger.warning(f"Unable to assemble DIVA datafeed. Unsupported reference asset: {pool.reference_asset}")
        return None
    if pool.collateral_token_symbol not in SUPPORTED_COLLATERAL_TOKEN_SYMBOLS:
        logger.warning(f"Unable to asseble DIVA datafeed. Unsupported collateral token: {pool.collateral_token_symbol}")
        return None

    source = DivaSource()
    source.reference_asset_source = get_historical_price_source(
        asset=ref_asset, currency=ref_currency, timestamp=pool.expiry_time
    )
    source.collat_token_source = get_historical_price_source(
        asset=pool.collateral_token_symbol.lower(), currency="usd", timestamp=pool.expiry_time
    )

    feed = DataFeed(
        query=DIVAProtocol(pool.pool_id, divaDiamond=diva_diamond, chainId=chain_id),
        source=source,
    )

    return feed
