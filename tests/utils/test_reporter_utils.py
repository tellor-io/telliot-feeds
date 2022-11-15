import pytest
from brownie import accounts
from brownie import TellorXOracleMock
from click.testing import CliRunner
from telliot_core.apps.core import TelliotCore
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract
from web3 import Web3
from unittest import mock

from telliot_feeds.cli.main import main as cli_main
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import reporter_sync_schedule
from telliot_feeds.utils.reporter_utils import tellor_suggested_report


logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_suggested_report(rinkeby_test_cfg):
    async with TelliotCore(config=rinkeby_test_cfg) as core:
        account = core.get_account()
        contract_instance = accounts[0].deploy(TellorXOracleMock)
        oracle = TellorxOracleContract(core.endpoint, account)
        oracle.address = contract_instance.address
        oracle.connect()
        qtag = await tellor_suggested_report(oracle)
        assert isinstance(qtag, str)
        entries = query_catalog.find(tag=qtag)
        assert len(entries) == 1
        catalog_entry = entries[0]
        q = catalog_entry.query
        assert isinstance(q, OracleQuery)


@pytest.mark.skip("Disabled until we need this functionality")
def test_suggested_report_cli():
    """Test suggested report CLI"""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--test_config", "query", "suggest"])
    assert "Suggested query" in result.output


def test_reporter_sync_schedule_list():
    """Test reporter_sync_schedule list"""
    lis = reporter_sync_schedule
    assert len(lis) > 4
    assert "eth-usd-spot" in lis
    assert "morphware-v1" not in lis
    assert "uspce-legacy" not in lis


@pytest.mark.asyncio
async def test_has_native_token_funds(mumbai_test_cfg, caplog, monkeypatch):
    """Test has_native_token_funds"""

    def fake_alert(msg):
        logger.warning("bingo" + msg)

    def fail_balance_read(*args, **kwargs):
        raise Exception("bango")

    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        addr = Web3.toChecksumAddress(account.address)
        endpoint = core.get_endpoint()
        endpoint.connect()

        # Test insufficient funds
        has_funds = has_native_token_funds(
            account=addr, web3=endpoint.web3, alert=fake_alert, min_balance=1e18
        )
        assert has_funds is False
        assert "bingo" in caplog.text
        assert f"Account {addr} has insufficient native token funds" in caplog.text

        # Fund account
        accounts[0].transfer(addr, "2 ether")

        # Test with funds
        has_funds = has_native_token_funds(account=addr, web3=endpoint.web3)
        assert has_funds is True

        # Test fail contract read
        with mock.patch("web3.eth.Eth.get_balance", side_effect=fail_balance_read):
            has_funds = has_native_token_funds(
                account=addr, web3=endpoint.web3, alert=fake_alert
            )
            assert has_funds is False
            assert "bango" in caplog.text
            assert f"Error fetching native token balance for {addr}" in caplog.text
