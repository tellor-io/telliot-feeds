import pytest
from brownie import accounts
from brownie import TellorXOracleMock
from click.testing import CliRunner
from telliot_core.apps.core import TelliotCore
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract
from telliot_core.utils.response import error_status

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
        print("bingo" + msg)

    def fail_contract_read(*args, **kwargs):
        return None, error_status(note="Fake error", log=logger.warning)

    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        contracts = core.get_tellor360_contracts()

        # Test with funds
        has_funds = await has_native_token_funds(account=account.address, token_contract=contracts.token)
        assert has_funds is True

        # Test without funds
        has_funds = await has_native_token_funds(
            account=account.address, token_contract=contracts.token, alert_func=fake_alert
        )
        assert has_funds is False
        assert "bingo" in caplog.text
        assert f"Account {account.address} has insufficient native token funds" in caplog.text

        # Test fail contract read
        monkeypatch.setattr("telliot_core.contract.contract.Contract.read", lambda: fail_contract_read())
        has_funds = await has_native_token_funds(
            account=account.address, token_contract=contracts.token, alert_func=fake_alert
        )
        assert has_funds is False
        assert "bingo" in caplog.text
        assert f"Unable to fetch native token balance for account {account.address}" in caplog.text
