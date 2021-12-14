"""Pytest Fixtures used for testing Pytelliot"""
import os

import pytest
from telliot_core.apps.core import TelliotCore
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.datasource import DataSource
from telliot_core.types.datapoint import OptionalDataPoint
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


@pytest.fixture()
def rinkeby_core(rinkeby_cfg):

    app = TelliotCore(config=rinkeby_cfg)

    # Replace staker private key
    staker = app.get_default_staker()
    if os.getenv("PRIVATE_KEY", None):
        staker.private_key = rinkeby_cfg.main.private_key
        staker.address = "0x8D8D2006A485FA4a75dFD8Da8f63dA31401B8fA2"

    app.connect()
    yield app

    # Destroy app instance after test
    TelliotCore.destroy()


EXPECTED_ERRORS = {
    "Current addess disputed. Switch address to continue reporting.",
    "Current address is locked in dispute or for withdrawal.",
    "Current address is in reporter lock.",
    "Estimated profitability below threshold.",
    "Estimated gas price is above maximum gas price.",
    "Unable to retrieve updated datafeed value.",
}


async def reporter_submit_once(rinkeby_core, feed):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""

    rinkeby_endpoint = rinkeby_core.config.get_endpoint()

    if feed == uspce_feed:
        # Override Python built-in input method
        uspce.input = lambda: "123.456"

    private_key = rinkeby_core.get_default_staker().private_key

    user = rinkeby_endpoint.web3.eth.account.from_key(private_key).address
    last_timestamp, read_status = await rinkeby_core.tellorx.oracle.read(
        "getReporterLastTimestamp", _reporter=user
    )
    assert read_status.ok

    reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=private_key,
        master=rinkeby_core.tellorx.master,
        oracle=rinkeby_core.tellorx.oracle,
        datafeed=feed,
    )

    tx_receipt, status = await reporter.report_once()

    # Reporter submitted
    if tx_receipt is not None and status.ok:
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to == rinkeby_core.tellorx.oracle.address
    # Reporter did not submit
    else:
        assert not tx_receipt
        assert not status.ok
        assert status.error in EXPECTED_ERRORS
        print(status.error)


@pytest.fixture(scope="session")
def bad_source():
    """Used for testing no updated value for datafeeds."""

    class BadSource(DataSource[float]):
        """Source that does not return an updated DataPoint."""

        async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
            return None, None

    return BadSource()
