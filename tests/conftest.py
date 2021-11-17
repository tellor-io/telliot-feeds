"""Pytest Fixtures used for testing Pytelliot"""
import os
import time

import pytest
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.contract.contract import Contract
from telliot_core.directory.tellorx import tellor_directory
from web3.datastructures import AttributeDict

from telliot_feed_examples.feeds.uspce_feed import uspce_feed
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.sources import uspce


@pytest.fixture(scope="session", autouse=True)
def rinkeby_cfg():
    """Get rinkeby endpoint from config

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for rinkeby testnet
    cfg.main.chain_id = 4

    rinkeby_endpoint = cfg.get_endpoint()
    # assert rinkeby_endpoint.network == "rinkeby"

    # Optionally override private key and URL with ENV vars for testing
    if os.getenv("PRIVATE_KEY", None):
        cfg.main.private_key = os.environ["PRIVATE_KEY"]

    if os.getenv("NODE_URL", None):
        rinkeby_endpoint.url = os.environ["NODE_URL"]

    return cfg


@pytest.fixture(scope="session")
def master(rinkeby_cfg):
    """Helper function for connecting to a contract at an address"""
    tellor_master = tellor_directory.find(chain_id=4, name="master")[0]
    endpoint = rinkeby_cfg.get_endpoint()
    endpoint.connect()
    master = Contract(
        address=tellor_master.address,  # "0x657b95c228A5de81cdc3F85be7954072c08A6042",
        abi=tellor_master.abi,
        node=endpoint,
        private_key=rinkeby_cfg.main.private_key,
    )
    master.connect()
    return master


@pytest.fixture(scope="session", autouse=True)
def oracle(rinkeby_cfg):
    """Helper function for connecting to a contract at an address"""
    tellor_oracle = tellor_directory.find(chain_id=4, name="oracle")[0]
    endpoint = rinkeby_cfg.get_endpoint()
    endpoint.connect()
    oracle = Contract(
        address=tellor_oracle.address,  # "0x07b521108788C6fD79F471D603A2594576D47477",
        abi=tellor_oracle.abi,
        node=endpoint,
        private_key=rinkeby_cfg.main.private_key,
    )
    oracle.connect()
    return oracle


async def reporter_submit_once(rinkeby_cfg, master, oracle, feed):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""

    rinkeby_endpoint = rinkeby_cfg.get_endpoint()

    if feed == uspce_feed:
        # Override Python built-in input method
        uspce.input = lambda: "123.456"

    user = rinkeby_endpoint.web3.eth.account.from_key(
        rinkeby_cfg.main.private_key
    ).address
    last_timestamp, read_status = await oracle.read(
        "getReporterLastTimestamp", _reporter=user
    )
    assert read_status.ok

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=rinkeby_cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[feed],
    )

    tx_receipts = await reporter.report_once(retries=3)

    assert tx_receipts is not None

    for receipt, status in tx_receipts:
        # reporter should exit if address is in reporter lock
        if time.time() < last_timestamp + 43200:
            assert receipt is None
            assert not status.ok
            assert "reporter lock" in status.error

        # if reporter is not in lock, should submit
        else:
            assert isinstance(receipt, AttributeDict)
            assert receipt.to == oracle.address
