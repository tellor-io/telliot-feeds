# Majority of this code from web3-flashbots:
# https://github.com/flashbots/web3-flashbots
# EIP-1559 subbport by @lekhovitsky
# https://github.com/lekhovitsky
# type: ignore
from typing import Any
from typing import Callable

from eth_utils.toolz import curry
from web3 import Web3
from web3.middleware.base import Web3MiddlewareBuilder
from web3.types import RPCEndpoint
from web3.types import RPCResponse

from .provider import FlashbotProvider

FLASHBOTS_METHODS = [
    "eth_sendBundle",
    "eth_callBundle",
]


class FlashbotsMiddlewareBuilder(Web3MiddlewareBuilder):
    """Web3 v6-compatible Flashbots middleware.

    Intercepts Flashbots RPC methods and routes them to the Flashbots relay
    provider while allowing all other requests to pass through normally.
    """

    flashbots_provider: FlashbotProvider = None  # type: ignore[assignment]

    @staticmethod
    @curry
    def build(w3: Web3, flashbots_provider: FlashbotProvider) -> "FlashbotsMiddlewareBuilder":
        middleware = FlashbotsMiddlewareBuilder(w3)
        middleware.flashbots_provider = flashbots_provider
        return middleware

    def wrap_make_request(
        self, make_request: Callable[[RPCEndpoint, Any], RPCResponse]
    ) -> Callable[[RPCEndpoint, Any], RPCResponse]:
        def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
            if method in FLASHBOTS_METHODS:
                return self.flashbots_provider.make_request(method, params)
            return make_request(method, params)

        return middleware


# Backwards-compatible constructor name used elsewhere in the codebase
construct_flashbots_middleware = FlashbotsMiddlewareBuilder.build
