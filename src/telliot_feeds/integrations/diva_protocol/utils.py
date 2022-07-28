from typing import Any

from telliot_feeds.integrations.diva_protocol.pool import DivaPool
from telliot_feeds.integrations.diva_protocol import SUPPORTED_HISTORICAL_PRICE_PAIRS
from telliot_feeds.integrations.diva_protocol import SUPPORTED_COLLATERAL_TOKEN_SYMBOLS

from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


def parse_reference_asset(reference_asset: str) -> Any:
    """
    Parse a reference asset string asset & currency strings.

    Args:
        reference_asset: Reference asset string. Example: "ETH/USD".

    Returns:
        Tuple of asset & currency. Example: ("eth", "usd").
    """
    try:
        asset, currency = reference_asset.lower().split("/")
        return asset, currency
    except Exception as e:
        logger.error(f"Error: {e} \nFailed to parse reference asset: {reference_asset}")
        return None, None


def dict_to_pool(pool_dict: dict[str, Any]) -> DivaPool:
    """
    Convert a dictionary to a DivaPool.

    Args:
        pool_dict: Dictionary to convert.

    Returns:
        DivaPool object.
    """
    return DivaPool(
        pool_id=int(pool_dict["id"]),
        reference_asset=pool_dict["referenceAsset"],
        collateral_token_address=pool_dict["collateralToken"]["id"],
        collateral_token_symbol=pool_dict["collateralToken"]["symbol"],
        collateral_balance=int(pool_dict["collateralBalance"]),
        expiry_time=int(pool_dict["expiryTime"]),
    )


def filter_valid_pools(pools: list[dict[str, Any]]) -> list[DivaPool]:
    """
    Filter out pools with unsupported reference assets or
    unsupported collateral tokens.

    Args:
        pools: List of pools to filter.

    Returns:
        List of pools that are valid.
    """
    return [
        dict_to_pool(d)
        for d in pools if
        d["referenceAsset"] in SUPPORTED_HISTORICAL_PRICE_PAIRS
        and d["collateralToken"]["symbol"] in SUPPORTED_COLLATERAL_TOKEN_SYMBOLS
    ]


def filter_unreported_pools(pools: list[DivaPool]) -> list[DivaPool]:
    """
    Filter out pools that have already been reported.

    Args:
        pools: List of pools to filter.

    Returns:
        List of pools that have not yet been reported.
    """
    pass


def find_most_profitable_pool(pools: list[DivaPool]) -> DivaPool:
    """
    Find the pool with the highest profit.

    Args:
        pools: List of pools to search.

    Returns:
        Pool with the highest profit.
    """
    pass
