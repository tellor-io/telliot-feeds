"""
Listen and filter for valid pools to report to.

Fetch new pools from the DIVA Protocol subgraph.
Filter out pools that have already been reported.
Filter out pools that have already been settled.
Filter out pools with unsupported reference assets or
unsupported collateral tokens."""

import pytest
import time
from telliot_core.apps.telliot_config import TelliotConfig
from .abi import DIVA_ABI
from web3.types import TxReceipt


@pytest.mark.asyncio
async def test_listen_new_pools():

    pass


@pytest.mark.asyncio
async def test_listen_new_pools_fail():
    pass


def test_filter_retrieved_pools():
    pass


def test_filter_retrieved_pools_fail():
    pass

"""Get and parse NewReport events from Tellor oracles."""
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Union

from dateutil import tz
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_core.directory import contract_directory
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.legacy_query import LegacyRequest
from web3 import Web3
from web3.contract import Contract
from web3.datastructures import AttributeDict
from web3.exceptions import TransactionNotFound

from hexbytes import HexBytes
from telliot_feeds import feeds
from web3.datastructures import AttributeDict


# OHM/ETH SpotPrice
EXAMPLE_NEW_REPORT_EVENT = AttributeDict(
    {
        "address": "0x41b66dd93b03e89D29114a7613A6f9f0d4F40178",
        "blockHash": HexBytes("0x61967b410ac2ef5352e1bc0c06ab63fb84ba9161276a4645aca389fd01409ef7"),
        "blockNumber": 25541322,
        "data": "0xee4fcdeed773931af0bcd16cfcea5b366682ffbd4994cf78b4f0a6a40b570"
        "3400000000000000000000000000000000000000000000000000000000062321"
        "eec0000000000000000000000000000000000000000000000000000000000000"
        "0c000000000000000000000000000000000000000000000000000000000000000"
        "3a000000000000000000000000000000000000000000000000000000000000010"
        "0000000000000000000000000d5f1cc896542c111c7aa7d7fae2c3d654f34b927"
        "00000000000000000000000000000000000000000000000000000000000000200"
        "0000000000000000000000000000000000000000000000000248c37b20efbff000"
        "000000000000000000000000000000000000000000000000000000000016000000"
        "0000000000000000000000000000000000000000000000000000000004000000000"
        "00000000000000000000000000000000000000000000000000000080000000000000"
        "000000000000000000000000000000000000000000000000000953706f7450726963"
        "65000000000000000000000000000000000000000000000000000000000000000000"
        "000000000000000000000000000000000000000000c00000000000000000000000"
        "0000000000000000000000000000000000000000400000000000000000000000000"
        "00000000000000000000000000000000000008000000000000000000000000000000"
        "000000000000000000000000000000000036f686d0000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000000"
        "000000000000000000000000000003657468000000000000000000000000000000"
        "0000000000000000000000000000",
        "logIndex": 101,
        "removed": False,
        "topics": [HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95")],
        "transactionHash": HexBytes("0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4"),
        "transactionIndex": 1,
    }
)

# OHM/ETH SpotPrice
EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT = (
    AttributeDict(
        {
            "args": AttributeDict(
                {
                    "_queryId": b"\xeeO\xcd\xee\xd7s\x93\x1a\xf0\xbc\xd1l\xfc"
                    b"\xea[6f\x82\xff\xbdI\x94\xcfx\xb4\xf0\xa6\xa4\x0bW\x03@",
                    "_time": 1647451884,
                    "_value": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$\x8c7\xb2\x0e\xfb\xff",
                    "_nonce": 58,
                    "_queryData": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03ohm\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03eth\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    "_reporter": "0xd5f1Cc896542C111c7Aa7D7fae2C3D654f34b927",
                }
            ),
            "event": "NewReport",
            "logIndex": 101,
            "transactionIndex": 1,
            "transactionHash": HexBytes("0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4"),
            "address": "0x41b66dd93b03e89D29114a7613A6f9f0d4F40178",
            "blockHash": HexBytes("0x61967b410ac2ef5352e1bc0c06ab63fb84ba9161276a4645aca389fd01409ef7"),
            "blockNumber": 25541322,
        }
    ),
)


def get_contract(web3: Web3, addr: str, abi: str) -> Contract:
    """Get a contract instance for the given address and ABI."""
    return web3.eth.contract(  # type: ignore
        address=addr,
        abi=abi,
    )


async def log_loop(web3: Web3, addr: str) -> list[tuple[int, Any]]:
    """Generate a list of recent events from a contract."""
    num = web3.eth.get_block_number()
    events = web3.eth.get_logs({"fromBlock": num, "toBlock": num + 100, "address": addr})  # type: ignore

    unique_events = {}
    unique_events_lis = []

    for event in events:
        txhash = event["transactionHash"]

        if txhash not in unique_events:
            unique_events[txhash] = event
            unique_events_lis.append((web3.eth.chain_id, event))

    return unique_events_lis


async def get_events(
    _web3: Web3,
    contract_addr: str,
) -> tuple[list[tuple[int, Any]], list[tuple[int, Any]]]:
    """Get all events from the Ethereum and Polygon chains."""

    events_lists = await asyncio.gather(
        log_loop(_web3, contract_addr),
    )
    return events_lists


def get_tx_receipt(tx_hash: str, web3: Web3) -> Any:
    """Get the transaction receipt for the given transaction hash."""
    try:
        receipt = web3.eth.get_transaction_receipt(tx_hash)
    except TimeoutError:
        print("timeout error")
        return None
    except TransactionNotFound:
        print("transaction not found")
        return None

    if receipt is None:
        print("no receipt")
        return None
    return receipt


def process_pool_issued_receipt(diva_contract: Contract, receipt: TxReceipt) -> Optional[AttributeDict]:
    processed_receipt = diva_contract.events.PoolIssued().processReceipt(receipt)
    if processed_receipt is None or not processed_receipt:
        print("No processed receipt because not PoolIssued event")
        return None

    return processed_receipt[0]


def parse_new_pool_issued_event(event: AttributeDict[str, Any], web3: Web3, contract: Contract) -> Optional[NewReport]:
    """Parse a NewReport event."""
    tx_hash = event["transactionHash"]

    receipt = get_tx_receipt(tx_hash, web3)
    if receipt is None:
        return None

    processed_receipt = process_pool_issued_receipt(contract, receipt)
    if processed_receipt is None:
        return None

    args = processed_receipt["args"]
    return NewPoolIssued(
        args["poolId"],
        args["from"],
        args["collateralAmount"]
    )
    

@dataclass
class NewPoolIssued:
    """NewPoolIssued event."""

    pool_id: int
    from_addr: str
    collateral_amount: int


def test_listen():
    """Main function."""
    cfg = TelliotConfig()

    # Override configuration for ropsten testnet
    cfg.main.chain_id = 3

    endpt = cfg.get_endpoint()
    if "INFURA_API_KEY" in endpt.url:
        endpt.url = f'wss://ropsten.infura.io/ws/v3/{os.environ["INFURA_API_KEY"]}'

    endpt.connect()
    ropsten_web3 = endpt._web3

    DIVA_ADDR = "0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211"

    ropsten_contract = get_contract(ropsten_web3, DIVA_ADDR, DIVA_ABI)
    print("ropsten contract addr", ropsten_contract.address)

    while True:
        # Fetch NewReport events
        event_lists = asyncio.run(
            get_events(
                ropsten_web3,
                ropsten_contract.address,
            )
        )

        for event_list in event_lists:
            # event_list = [(80001, EXAMPLE_NEW_REPORT_EVENT)]
            for event_info in event_list:
                chain_id, event_data = event_info
                # print("New event:", event_data)
                new_pool = parse_new_pool_issued_event(event_data, ropsten_web3, ropsten_contract)
                if new_pool is not None:
                    print("New Pool Issued:", new_pool)
        time.sleep(1)

# check in pool params if tellor oracle is provider
