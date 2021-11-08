"""Pytest Fixtures used for testing Pytelliot"""
import os

import pytest
from telliot.apps.telliot_config import TelliotConfig
from telliot.contract.contract import Contract
from telliot.utils.abi import rinkeby_tellor_master
from telliot.utils.abi import rinkeby_tellor_oracle


@pytest.fixture(scope="session", autouse=True)
def cfg():
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
def master(cfg):
    """Helper function for connecting to a contract at an address"""
    endpoint = cfg.get_endpoint()
    endpoint.connect()
    master = Contract(
        address="0x657b95c228A5de81cdc3F85be7954072c08A6042",
        abi=rinkeby_tellor_master,
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    master.connect()
    return master


@pytest.fixture(scope="session", autouse=True)
def oracle(cfg):
    """Helper function for connecting to a contract at an address"""
    endpoint = cfg.get_endpoint()
    endpoint.connect()
    oracle = Contract(
        address="0x07b521108788C6fD79F471D603A2594576D47477",
        abi=rinkeby_tellor_oracle,
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    oracle.connect()
    return oracle
