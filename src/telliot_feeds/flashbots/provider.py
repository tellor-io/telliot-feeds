# Majority of this code from web3-flashbots:
# https://github.com/flashbots/web3-flashbots
# EIP-1559 subbport by @lekhovitsky
# https://github.com/lekhovitsky
# flake8: noqa
# type: ignore
import logging
import os
from typing import Any
from typing import Optional
from typing import Union

from eth_account import Account
from eth_account import messages
from eth_account.signers.local import LocalAccount
from eth_typing import URI
from web3 import HTTPProvider
from web3 import Web3
from web3._utils.request import make_post_request
from web3.types import RPCEndpoint
from web3.types import RPCResponse


def get_default_endpoint(chain_id: int = 1) -> URI:
    uri = {
        1: URI(os.environ.get("FLASHBOTS_HTTP_PROVIDER_URI", "https://relay.flashbots.net")),
        5: URI(os.environ.get("FLASHBOTS_HTTP_PROVIDER_URI_GOERLI", "https://relay-goerli.flashbots.net")),
        11155111: URI(os.environ.get("FLASHBOTS_HTTP_PROVIDER_URI_SEPOLIA", "https://relay-sepolia.flashbots.net")),
    }
    return uri[chain_id]


class FlashbotProvider(HTTPProvider):
    logger = logging.getLogger("web3.providers.FlashbotProvider")

    def __init__(
        self,
        signature_account: LocalAccount,
        endpoint_uri: Optional[Union[URI, str]] = None,
        request_kwargs: Optional[Any] = None,
        session: Optional[Any] = None,
    ):
        _endpoint_uri = endpoint_uri or get_default_endpoint()
        super().__init__(_endpoint_uri, request_kwargs, session)
        self.signature_account = signature_account

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        self.logger.debug(f"Making request HTTP. URI: {self.endpoint_uri}, Method: {method}")
        request_data = self.encode_rpc_request(method, params)

        message = messages.encode_defunct(text=Web3.keccak(text=request_data.decode("utf-8")).hex())
        signed_message = Account.sign_message(message, private_key=self.signature_account.privateKey.hex())

        headers = self.get_request_headers() | {
            "X-Flashbots-Signature": f"{self.signature_account.address}:{signed_message.signature.hex()}"
        }

        raw_response = make_post_request(self.endpoint_uri, request_data, headers=headers)
        response = self.decode_rpc_response(raw_response)
        self.logger.debug(f"Getting response HTTP. URI: {self.endpoint_uri}, Method: {method}, Response: {response}")
        return response
