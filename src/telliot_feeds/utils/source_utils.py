from typing import Optional

from web3 import Web3

from telliot_feeds.utils.cfg import TelliotConfig


def update_web3(chainId: int, cfg: TelliotConfig) -> Optional[Web3]:
    """Return a web3 instance for the given chain ID."""

    eps = cfg.endpoints.find(chain_id=chainId)
    if len(eps) > 0:
        endpoint = eps[0]
    else:
        raise ValueError(f"Endpoint not found for chain_id={chainId}")

    if not endpoint.connect():
        raise Exception(f"Endpoint not connected for chain_id={chainId}")
    w3: Web3 = endpoint._web3
    return w3
