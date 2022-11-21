import pytest
import pytest_asyncio
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.reporters.rng_interval import RNGReporter


@pytest_asyncio.fixture(scope="function")
async def rng_reporter(mumbai_test_cfg, tellor_360):
    async with TelliotCore(config=mumbai_test_cfg) as core:
        contracts, account = tellor_360
        r = RNGReporter(
            oracle=contracts.oracle,
            token=contracts.token,
            autopay=contracts.autopay,
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            transaction_type=0,
        )

        return r


@pytest.mark.asyncio
async def test_rng_reporter_submit_once(rng_reporter):
    """Test reporting once to the Tellor playground on Rinkeby
    with three retries."""
    r = rng_reporter

    EXPECTED_ERRORS = {
        "Current addess disputed. Switch address to continue reporting.",
        "Current address is locked in dispute or for withdrawal.",
        "Current address is in reporter lock.",
        "Estimated profitability below threshold.",
        "Estimated gas price is above maximum gas price.",
        "Unable to retrieve updated datafeed value.",
        "Unable to approve staking",
    }

    ORACLE_ADDRESSES = {r.oracle.address}

    tx_receipt, status = await r.report_once()

    # Reporter submitted
    if tx_receipt is not None and status.ok:
        assert isinstance(tx_receipt, AttributeDict)
        assert tx_receipt.to in ORACLE_ADDRESSES
    # Reporter did not submit
    else:
        assert not tx_receipt
        assert not status.ok
        assert status.error in EXPECTED_ERRORS
