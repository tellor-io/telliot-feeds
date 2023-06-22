# Ignoring code formatting errors from flake8:
# flake8: noqa E501 W291
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional

import requests
from requests import JSONDecodeError
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.integrations.diva_protocol import BASE_SUBGRAPH_URL
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class DivaPool:
    """
    Data class for a DIVA Protocol pool.

    Full description of the fields:
    https://github.com/divaprotocol/oracles#diva-smart-contract
    """

    pool_id: str  # bytes32
    reference_asset: str
    collateral_token_address: str
    collateral_token_symbol: str
    collateral_balance: int
    expiry_time: int


def query_valid_pools(data_provider: str, expiry_since: Optional[int] = None) -> str:
    """
    Generate query string to fetch pool data from DIVA Protocol subgraph.

    Args:
        data_provider: Who reports the data for the reference asset.
        expiry_since: Fetch pools w/ expiry >= this timestamp.
    """
    return """
            {
                pools (first: 100, where: {expiryTime_gte: "%s", expiryTime_lte: "%s", statusFinalReferenceValue: "Open", dataProvider: "%s"}) {
                    id
                    referenceAsset
                    collateralToken {
                        symbol
                        id
                    }
                    collateralBalance
                    expiryTime
                  }
                }
            """ % (
        expiry_since or (int(datetime.now().timestamp() - 10) - 86400),  # 1 day ago
        int(datetime.now().timestamp() - 30),  # 30 seconds ago
        data_provider,
    )


retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


async def fetch_from_subgraph(query: str, network: str) -> Optional[list[dict[str, Any]]]:
    """
    Query the DIVA Protocol subgraph.

    Args:
        query: GraphQL query string.
        network: chain network name to query.

    Returns:
        List of dictionaries containing the query results.
    """
    with requests.Session() as s:
        s.mount("https://", adapter)
        try:
            rsp = s.post(
                f"{BASE_SUBGRAPH_URL}{network}",
                json={"query": query},
            )
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timeout fetching from subgraph")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Subgraph API error: {e}")
            return None

        try:
            data = rsp.json()
        except JSONDecodeError:
            logger.error("Subgraph API returned invalid JSON")
            return None

        try:
            return data["data"]["pools"]  # type: ignore
        except KeyError:
            logger.error(f"Subgraph API return JSON missing keys: {data}")
            return None
