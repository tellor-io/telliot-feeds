from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple

from multicall import Call
from multicall import Multicall
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import ResponseStatus


class AssembleCall:
    """
    Assemble call object for autopay functions to batch call them using multicall
    """

    def __init__(self) -> None:
        self.autopay: TellorFlexAutopayContract

    async def multi_call(self, calls: List[Call], success: bool = False) -> Tuple[Dict[Any, Any], ResponseStatus]:
        """Make multi-call given a list of Calls

        Arg:
        - calls: list of Call objects
        - success: boolean, setting to false will handle any contract logic errors

        Return:
        - dictionary of of Any type key, could be tuple, string, or number
        """
        status = ResponseStatus()
        multi_call = Multicall(calls=calls, _w3=self.autopay.node._web3, require_success=success)
        try:
            data: Dict[Any, Any] = await multi_call.coroutine()
        except Exception as e:
            status.ok = False
            status.e = e
            status.error = "multicall failed to fetch data"
        return data, status

    def assemble_call_object(
        self, func_sig: str, returns: Iterable[Tuple[str, Callable[..., Any]]], **kwargs: Dict[Any, Any]
    ) -> Call:
        """Assemble a single Call object to use in a batch call through multicall

        Args:
        - func_sig: the function to call with params' types and return type
        i.e. "funcsig(paramtype1, paramtype2)(returntype1)"
        - returns: return dictionary object
        - handler_func: optional function to handle call response, default None
        - *kwargs: function arguments to be used in the call

        Return: Call object
        """
        return Call(
            target=self.autopay.address, function=[func_sig] + list(kwargs.values()), returns=returns  # type: ignore
        )
