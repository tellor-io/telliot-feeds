from typing import Any
from typing import Optional

from multicall import Call
from multicall import Multicall
from telliot_core.tellor.tellorflex.autopay import TellorFlexAutopayContract
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus


class AssembleCall:
    """
    Assemble call object for autopay functions to batch call them using multicall
    """

    # set gas limit to None since this will mostly be used for read-only calls
    gas_limit: Optional[int] = None

    def __init__(self) -> None:
        self.autopay: TellorFlexAutopayContract

    async def multi_call(
        self, calls: list[Call], success: bool = False
    ) -> tuple[Optional[dict[Any, Any]], ResponseStatus]:
        """Make multi-call given a list of Calls

        Arg:
        - calls: list of Call objects
        - success: boolean, setting to false will handle any contract logic errors

        Return:
        - dictionary of of Any type key, could be tuple, string, or number
        """
        status = ResponseStatus()
        multi_call = Multicall(
            calls=calls, _w3=self.autopay.node._web3, require_success=success, gas_limit=self.gas_limit
        )
        try:
            data: dict[Any, Any] = await multi_call.coroutine()
            return data, status
        except Exception as e:
            msg = "multicall failed to fetch data"
            return None, error_status(note=msg, e=e)

    def assemble_call_object(self, func_sig: str, returns: list[Any], **kwargs: Any) -> Call:
        """Assemble a single Call object to use in a batch call through multicall

        Args:
        - func_sig: the function to call with params' types and return type
        i.e. "funcsig(paramtype1, paramtype2)(returntype1)"
        - returns: return dictionary object
        - handler_func: optional function to handle call response, default None
        - *kwargs: function arguments to be used in the call

        Return: Call object
        """
        return Call(target=self.autopay.address, function=[func_sig] + list(kwargs.values()), returns=returns)
