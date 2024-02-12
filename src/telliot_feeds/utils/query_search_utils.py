import ast
from typing import Any
from typing import Optional

from clamfig.base import Registry
from eth_abi import decode_single
from eth_abi.exceptions import NonEmptyPaddingBytes
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.feeds import MANUAL_FEEDS
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


def decode_typ_name(qdata: bytes) -> str:
    """Decode query type name from query data

    Args:
    - qdata: query data in bytes

    Return: string query type name
    """
    qtype_name: str
    try:
        qtype_name, _ = decode_single("(string,bytes)", qdata)
    except OverflowError:
        # string query for some reason encoding isn't the same as the others
        qtype_name = ast.literal_eval(qdata.decode("utf-8"))["type"]
    except NonEmptyPaddingBytes:
        logger.error(f"NonEmptyPaddingBytes error for query data: {qdata.hex()}")
        return ""
    except Exception as e:
        logger.error(f"Error decoding query type name for query data: {qdata.hex()}; error: {e}")
        return ""
    return qtype_name


def qtype_name_in_registry(qdata: bytes) -> bool:
    """Check if query type exists in telliot registry

    Args:
    - qdata: query data in bytes

    Return: bool
    """
    qtyp_name = decode_typ_name(qdata)

    return qtyp_name in Registry.registry


def feed_from_catalog_feeds(qdata: bytes) -> Optional[DataFeed[Any]]:
    """Get feed if query tag in CATALOG_FEEDS

    Args:
    - qdata: query data in bytes

    Return: DataFeed
    """
    qid = w3.keccak(qdata).hex()
    qtag = qtag_from_query_catalog(qid=qid)
    return CATALOG_FEEDS.get(qtag) if qtag else None


def feed_in_feed_builder_mapping(qdata: bytes, skip_manual_feeds: bool = False) -> Optional[DataFeed[Any]]:
    """Get feed if query type in DATAFEED_BUILDER_MAPPING

    Args:
    - qdata: query data in bytes

    Return: DataFeed
    """
    qtyp_name = decode_typ_name(qdata)
    if skip_manual_feeds:
        if qtyp_name in MANUAL_FEEDS:
            logger.info(f"There is a tip for this query type: {qtyp_name}. Query data: {qdata.hex()}, (manual feed)")
            return None

    return DATAFEED_BUILDER_MAPPING.get(qtyp_name)


def get_query_from_qtyp_name(qdata: bytes) -> Optional[OracleQuery]:
    """Get query from query type name

    Args:
    - qdata: query data in bytes

    Return: query
    """
    qtyp_name = decode_typ_name(qdata)
    query_object: Optional[OracleQuery] = Registry.registry.get(qtyp_name)

    return query_object.get_query_from_data(qdata) if query_object is not None else None


def query_from_query_catalog(*, qid: Optional[str] = None, qtype_name: Optional[str] = None) -> Optional[OracleQuery]:
    """Check if query for given query data is available in CATALOG_FEEDS

    Args:
    - qid: query id
    - qtype_name: query type name
    Return: query
    """
    if qid:
        query = query_catalog.find(query_id=qid)
    else:
        query = query_catalog.find(query_type=qtype_name)
    return query[0] if query else None


def qtag_from_query_catalog(qid: str) -> Optional[str]:
    """Get query tag from query catalog

    Args:
    - qid: query id

    Return: qtag
    """
    query = query_from_query_catalog(qid=qid)
    return query.tag if query else None
