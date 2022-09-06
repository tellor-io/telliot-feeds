from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import ResponseStatus


class TipListener(ABC):
    """Calculator of feed with highest tip"""

    def __init__(self, autopay: TellorFlexAutopayContract) -> None:
        self.autopay = autopay

    @abstractmethod
    async def autopay_function_call(self, func_name: str, **kwargs: Dict[str, Any]) -> Tuple[Any, ResponseStatus]:
        """Make autopay function calls
        Args:
        - func_name: function name
        - kwargs: any params require for function contrac call

        :return: data
        """

    @abstractmethod
    def decode_typ_name(self, query_data: bytes) -> str:
        """Decode query type name from query data"""

    @abstractmethod
    def qtype_name_in_registry(self, qtyp_name: str) -> bool:
        """Check if query type exists in telliot registry

        :return: bool
        """

    @abstractmethod
    def get_max_tip(feed: List[Tuple[bytes, int]]) -> List[Tuple[bytes, int]]:
        """Get max tip and it query data given a list of tuples

        Arg:
        - feed list of tuples

        :return: tuple
        """
