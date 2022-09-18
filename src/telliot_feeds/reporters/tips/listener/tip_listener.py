from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

from telliot_feeds.feeds import DataFeed


class TipListener(ABC):
    """Check if query data supported"""

    @abstractmethod
    def decode_typ_name(self, qdata: bytes) -> str:
        """Decode query type name from query data

        Return: string query type name
        """

    @abstractmethod
    def qtype_name_in_registry(self, qtyp_name: str) -> bool:
        """Check if query type exists in telliot registry

        Return: bool
        """

    @abstractmethod
    def qtag_from_feed_catalog(self, qdata: bytes) -> Optional[str]:
        """Check if query tag for given query data is available in CATALOG_FEEDS

        Return: str
        """

    @abstractmethod
    def qtag_in_feed_mapping(self, qdata: bytes) -> Optional[DataFeed[Any]]:
        """Check if query type in DATAFEED_BUILDER_MAPPING

        Return: DataFeed
        """

    @abstractmethod
    def get_query_from_qtyp_name(self, qdata: bytes, qtyp_name: str) -> DataFeed[Any]:
        """Get query from query type name

        Return: query
        """

    @abstractmethod
    def get_max_tip(feed: List[Tuple[bytes, int]]) -> List[Tuple[bytes, int]]:
        """Get max tip and it query data given a list of tuples

        Arg:
        - feed list of tuples

        :return: tuple
        """
