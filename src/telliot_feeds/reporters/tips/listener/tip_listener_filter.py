import ast
import sys
from typing import Any
from typing import Optional

from clamfig.base import Registry
from eth_abi import decode_single
from eth_utils.conversions import to_bytes
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS


class TipListenerFilter:
    """Check if query data supported"""

    def decode_typ_name(self, qdata: bytes) -> str:
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
        return qtype_name

    def qtype_name_in_registry(self, qdata: bytes) -> bool:
        """Check if query type exists in telliot registry

        Args:
        - qdata: query data in bytes

        Return: bool
        """
        qtyp_name = self.decode_typ_name(qdata)

        if qtyp_name == "TellorRNG":
            return False

        return qtyp_name in Registry.registry

    def qtag_from_feed_catalog(self, qdata: bytes) -> Optional[str]:
        """Check if query tag for given query data is available in CATALOG_FEEDS

        Args:
        - qdata: query data in bytes

        Return: qtag
        """
        query_id = to_bytes(hexstr=w3.keccak(qdata).hex())
        return CATALOG_QUERY_IDS[query_id] if query_id in CATALOG_QUERY_IDS else None

    def qtag_in_feed_mapping(self, qdata: bytes) -> Optional[DataFeed[Any]]:
        """Check if query type in  CATALOG_FEEDS

        Args:
        - qdata: query data in bytes

        Return: DataFeed
        """
        qtag = self.qtag_from_feed_catalog(qdata)
        if qtag is None:
            return None
        if qtag in CATALOG_FEEDS:
            datafeed = CATALOG_FEEDS[qtag]
            return datafeed  # type: ignore
        else:
            return None

    def qtype_in_feed_builder_mapping(self, qdata: bytes) -> Optional[DataFeed[Any]]:
        """Check if query type in DATAFEED_BUILDER_MAPPING

        Args:
        - qdata: query data in bytes

        Return: DataFeed
        """
        qtyp_name = self.decode_typ_name(qdata)
        return DATAFEED_BUILDER_MAPPING[qtyp_name] if qtyp_name in DATAFEED_BUILDER_MAPPING else None

    def get_query_from_qtyp_name(self, qdata: bytes) -> Optional[OracleQuery]:
        """Get query from query type name

        Args:
        - qdata: query data in bytes

        Return: query
        """
        qtyp_name = self.decode_typ_name(qdata)
        query_object: OracleQuery = getattr(sys.modules["telliot_feeds.queries.query_catalog"], qtyp_name)
        return query_object.get_query_from_data(qdata)
