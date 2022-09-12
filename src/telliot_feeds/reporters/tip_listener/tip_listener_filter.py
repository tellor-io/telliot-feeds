from typing import Iterable
from typing import List
from typing import Tuple

from clamfig.base import Registry
from eth_abi import decode_single

from telliot_feeds.reporters.tip_listener.tip_listener import TipListener


class TipListenerFilter(TipListener):
    def decode_typ_name(self, query_data: bytes) -> str:
        try:
            qtype_name: str = decode_single("(string,bytes)", query_data)[0]
        except OverflowError:
            # string query for some reason encoding isn't the same as the others
            import ast

            qtype_name = ast.literal_eval(query_data.decode("utf-8"))["type"]
        return qtype_name

    def qtype_name_in_registry(self, qtyp_name: str) -> bool:
        if qtyp_name not in Registry.registry:
            return False
        return True

    def qdata_in_feed_catalog(self, query_data: bytes) -> bool:
        pass

    def qtype_in_feed_mapping(self, qtyp_name: str) -> bool:
        pass

    def get_query_from_qtyp_name(self, qtyp_name: str) -> object:
        pass

    def get_max_tip(feed: Iterable[List[Tuple[bytes, int]]]) -> List[Tuple[bytes, int]]:
        return max(feed, key=lambda item: item[1])
