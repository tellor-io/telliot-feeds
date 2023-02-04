"""
Subclass AbiQuery to implement the EVMCall query type.
"""
from dataclasses import dataclass

from eth_abi import encode_abi

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery


@dataclass
class EVMCall(AbiQuery):
    """EVMCall query type.

    More info: https://github.com/tellor-io/dataSpecs/blob/main/types/EVMCall.md

    Parameters
    ----------
    chainId: The chain id of the network the contract is deployed on
    contractAddress: The address of the contract on the network(e.g. 0x...)
    calldata: The encoding of the function name and its arguments
    """

    chainId: int
    contractAddress: str
    calldata: bytes

    abi = [
        {"type": "uint256", "name": "chainId"},
        {"type": "address", "name": "contractAddress"},
        {"type": "bytes", "name": "calldata"},
    ]

    @property
    def value_type(self) -> ValueType:
        """Expected response type.

        `bytes` - the encoded value and timestamp
        """
        return ValueType(abi_type="bytes", packed=False)

    @property
    def query_data(self) -> bytes:
        """Encode the query type and parameters to create the query data.

        This method uses ABI encoding to encode the query's parameter values.
        """
        param_values = [getattr(self, p["name"]) for p in self.abi]
        param_types = [p["type"] for p in self.abi]
        encoded_params = encode_abi(param_types, param_values)

        q_data = encode_abi(["string", "bytes"], [type(self).__name__, encoded_params])
        # The function selector (calldata) parameter must be shifted over, so that
        # the query data matches the generated query data in Solidity.
        last_32_bytes = q_data[-32:]
        call_data = []
        # iterate backwards through the last 32 bytes
        # append the remaining bytes to the call_data list
        # when the first non-zero byte is found
        for i in range(31, -1, -1):
            if last_32_bytes[i] != 0:
                call_data.append(last_32_bytes[: i + 1])
                break

        shifted_call_data = call_data.rjust(32, b"\x00")
        # adjusted_q_data = q_data[:-32] + shifted_func_selector
        # return adjusted_q_data
