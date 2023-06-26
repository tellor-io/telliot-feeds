import pickle
from typing import Any
from typing import Optional

from telliot_core.utils.home import default_homedir

from telliot_feeds.integrations.diva_protocol import SUPPORTED_COLLATERAL_TOKEN_SYMBOLS
from telliot_feeds.integrations.diva_protocol import SUPPORTED_HISTORICAL_PRICE_PAIRS
from telliot_feeds.integrations.diva_protocol.pool import DivaPool
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
        pool_id=str(pool_dict["id"]),
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
        for d in pools
        if d["referenceAsset"] in SUPPORTED_HISTORICAL_PRICE_PAIRS
        and d["collateralToken"]["symbol"] in SUPPORTED_COLLATERAL_TOKEN_SYMBOLS
    ]


def get_reported_pools() -> Any:
    """
    Retrieve dictionary of reoprted pools from telliot default dir
    """
    pools_file = str(default_homedir()) + "/reported_pools.pickle"

    try:
        reported_pools = pickle.load(open(pools_file, "rb"))
    except OSError:
        reported_pools = {}
        pickle.dump(reported_pools, open(pools_file, "wb"))

    return reported_pools


def update_reported_pools(
    pools: dict[str, int], add: Optional[list[Any]] = None, remove: Optional[list[str]] = None
) -> None:
    """
    Remove settled pools from reported pools dict & save to pickle file in
    telliot default dir
    """
    pools_file = str(default_homedir()) + "/reported_pools.pickle"

    if add:
        for pool in add:
            # pool is a tuple of pool_id and [expiry_time, "not settled"]
            pools[pool[0]] = pool[1]
    if remove:
        for pool_id in remove:
            del pools[pool_id]

    pickle.dump(pools, open(pools_file, "wb"))
