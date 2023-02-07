"""
Tests for EVMCallSource

import asyncio
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger

from telliot_core.apps.telliot_config import TelliotConfig

from web3 import Web3


logger = get_logger(__name__)


@dataclass
class EVMCallSource(DataSource[Optional[bytes]]):
    "DataSource for returning the result of a read function on an EVM contract."
    chain_id: Optional[bytes] = None
    contract_address: Optional[str] = None  # example: '0x1234567890123456789012345678901234567890'
    calldata: Optional[bytes] = None
    web3: Optional[Web3] = None
    cfg: TelliotConfig = TelliotConfig()

    def update_web3(self) -> None:
        "Return a web3 instance for the given chain ID."
        if not self.chain_id:
            raise ValueError("Chain ID not provided")
        
        eps = self.cfg.endpoints.find(chain_id=self.chain_id)
        if len(eps) > 0:
            endpoint = eps[0]
        else:
            raise ValueError(f"Endpoint not found for chain_id={self.chain_id}")
        
        if not endpoint.connect():
            raise Exception(f"Endpoint not connected for chain_id={self.chain_id}")
        
        self.web3 = endpoint.web3


    def get_response(self) -> Optional[bytes]:
        "Return the response from the EVM contract."
        if not self.contract_address:
            raise ValueError("Contract address not provided")
        if not self.calldata:
            raise ValueError("Calldata not provided")
        if not self.web3:
            raise ValueError("Web3 not provided")
        result = self.w3.eth.call(
            {'to': self.contract_address, 'data': self.calldata},
            'latest'
        )
        return result

    async def fetch_new_datapoint(self) -> OptionalDataPoint[bytes]:
        "Update current value with time-stamped value fetched from EVM contract.

        Returns:
            Current time-stamped value
        "
        try:
            self.update_web3()
        except Exception as e:
            logger.warning(f"Error occurred while updating web3 instance: {e}")
            return None, None
        
        try:
            val = self.get_response()
        except Exception as e:
            logger.warning(f"Error occurred while getting response: {e}")
            return None, None

        datapoint = (val, datetime_now_utc())
        self.store_datapoint(datapoint)

        return datapoint
    """
import pytest

from telliot_feeds.sources.evm_call import EVMCallSource
from telliot_core.apps.telliot_config import TelliotConfig

from eth_abi import decode_abi


@pytest.mark.asyncio
async def test_source():
    """Test initialization of EVMCallSource."""
    s = EVMCallSource()
    assert s.chain_id is None
    assert s.contract_address is None
    assert s.calldata is None
    assert s.web3 is None
    assert s.cfg is not None
    assert s.cfg.main.chain_id == TelliotConfig().main.chain_id

    s2 = EVMCallSource(
        chain_id = 80001,
        contract_address = "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata = b"\x18\x16\x0d\xdd",
    )
    assert s2.chain_id == 80001
    assert s2.contract_address == "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
    assert s2.calldata == b"\x18\x16\x0d\xdd"

    # test update_web3
    s2.update_web3()
    assert s2.web3 is not None

    # test get_response
    response = s2.get_response()
    assert response is not None
    assert isinstance(response, bytes)

    # test fetch_new_datapoint
    v, t = await s2.fetch_new_datapoint()
    assert v is not None
    assert t is not None

