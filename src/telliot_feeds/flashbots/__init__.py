# Majority of this code from web3-flashbots:
# https://github.com/flashbots/web3-flashbots
# Including it here instead because it ^ doesn't seem to be actively supported.
# EIP-1559 subbport by @lekhovitsky
# https://github.com/lekhovitsky
# type: ignore
from typing import Optional
from typing import Union

from eth_account.signers.local import LocalAccount
from eth_typing import URI
from web3 import Web3

from .flashbots import Flashbots
from .middleware import construct_flashbots_middleware
from .provider import FlashbotProvider

# attach_modules is now a method on Web3 instance


DEFAULT_FLASHBOTS_RELAY = "https://relay.flashbots.net"


def flashbot(
    w3: Web3,
    signature_account: LocalAccount,
    endpoint_uri: Optional[Union[URI, str]] = None,
):
    """
    Injects the flashbots module and middleware to w3.
    """

    flashbots_provider = FlashbotProvider(signature_account, endpoint_uri)
    flash_middleware = construct_flashbots_middleware(flashbots_provider)
    w3.middleware_onion.add(flash_middleware)

    # attach modules to add the new namespace commands
    w3.attach_modules({"flashbots": (Flashbots,)})
