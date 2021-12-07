"""Helper functions for TellorX contracts."""
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.directory.tellorx import tellor_directory
from telliot_core.model.endpoints import RPCEndpoint


def get_tellor_contracts(
    private_key: str, chain_id: int, endpoint: RPCEndpoint
) -> Tuple[Contract, Contract]:
    """Get Contract objects per telliot configuration and
    CLI flag options."""
    endpoint.connect()

    tellor_oracle = tellor_directory.find(chain_id=chain_id, name="oracle")[0]
    oracle = Contract(
        address=tellor_oracle.address,
        abi=tellor_oracle.abi,
        node=endpoint,
        private_key=private_key,
    )
    oracle.connect()

    tellor_master = tellor_directory.find(chain_id=chain_id, name="master")[0]
    master = Contract(
        address=tellor_master.address,
        abi=tellor_master.abi,
        node=endpoint,
        private_key=private_key,
    )
    master.connect()

    return master, oracle
