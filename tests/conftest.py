"""Pytest Fixtures used for testing Pytelliot"""
import os

import pytest
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.datasource import DataSource
from telliot_core.types.datapoint import OptionalDataPoint


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

    if os.getenv("NODE_URL", None):
        rinkeby_endpoint.url = os.environ["NODE_URL"]

    # Replace staker private key
    if os.getenv("PRIVATE_KEY", None):
        private_key = os.environ["PRIVATE_KEY"]
        rinkeby_stakers = cfg.stakers.find(chain_id=4)
        if len(rinkeby_stakers) == 0:
            raise Exception("No staker/private key defined for rinkeby")
        rinkeby_staker = rinkeby_stakers[0]
        rinkeby_staker.private_key = private_key
        rinkeby_staker.address = "0x8D8D2006A485FA4a75dFD8Da8f63dA31401B8fA2"

    return cfg


@pytest.fixture(scope="session")
def bad_source():
    """Used for testing no updated value for datafeeds."""

    class BadSource(DataSource[float]):
        """Source that does not return an updated DataPoint."""

        async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
            return None, None

    return BadSource()
