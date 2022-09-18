import ast
import sys
from typing import Any
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from clamfig.base import Registry
from eth_abi import decode_single
from eth_utils.conversions import to_bytes
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.feeds import LEGACY_DATAFEEDS
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.reporters.tips import CATALOG_QUERY_IDS
from telliot_feeds.reporters.tips.listener.tip_listener import TipListener


class TipListenerFilter(TipListener):
    def decode_typ_name(self, qdata: bytes) -> str:
        try:
            qtype_name: str = decode_single("(string,bytes)", qdata)[0]
        except OverflowError:
            # string query for some reason encoding isn't the same as the others
            qtype_name = ast.literal_eval(qdata.decode("utf-8"))["type"]
        return qtype_name

    def qtype_name_in_registry(self, qdata: bytes) -> bool:
        qtyp_name = self.decode_typ_name(qdata)
        if qtyp_name not in Registry.registry:
            return False
        return True

    def qtag_from_feed_catalog(self, qdata: bytes) -> Optional[str]:
        query_id = to_bytes(hexstr=w3.keccak(qdata).hex())
        if query_id in CATALOG_QUERY_IDS:
            qtag = CATALOG_QUERY_IDS[query_id]
            return qtag
        return None

    def qtag_in_feed_mapping(self, qdata: bytes) -> Optional[DataFeed[Any]]:
        qtag = self.qtag_from_feed_catalog(qdata)
        if qtag in CATALOG_FEEDS:
            datafeed = CATALOG_FEEDS[qtag]
        elif qtag in LEGACY_DATAFEEDS:
            datafeed = LEGACY_DATAFEEDS[qtag]
        else:
            return None
        return datafeed

    def qtype_in_feed_builder_mapping(self, qdata: bytes) -> Optional[DataFeed[Any]]:
        qtyp_name = self.decode_typ_name(qdata)
        if qtyp_name in DATAFEED_BUILDER_MAPPING:
            datafeed = DATAFEED_BUILDER_MAPPING[qtyp_name]
            return datafeed
        return None

    def get_query_from_qtyp_name(self, qdata: bytes) -> Optional[OracleQuery]:
        qtyp_name = self.decode_typ_name(qdata)
        query_object: OracleQuery = getattr(sys.modules["telliot_feeds.queries.query_catalog"], qtyp_name)
        query = query_object.get_query_from_data(qdata)
        return query

    def get_max_tip(feed: Iterable[List[Tuple[bytes, int]]]) -> List[Tuple[bytes, int]]:
        return max(feed, key=lambda item: item[1])
