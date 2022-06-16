import pytest
from brownie import accounts
from brownie import TellorXOracleMock
from click.testing import CliRunner

import telliot_core.cli.main
from telliot_core.apps.core import TelliotCore
from telliot_core.data.query_catalog import query_catalog
from telliot_core.queries.query import OracleQuery
from telliot_core.reporters.reporter_utils import reporter_sync_schedule
from telliot_core.reporters.reporter_utils import tellor_suggested_report
from telliot_core.tellor.tellorx.oracle import TellorxOracleContract


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


def test_suggested_report_cli():
    """Test suggested report CLI"""
    runner = CliRunner()
    result = runner.invoke(telliot_core.cli.main.main, ["--test_config", "query", "suggest"])
    assert "Suggested query" in result.output


def test_reporter_sync_schedule_list():
    """Test reporter_sync_schedule list"""
    lis = reporter_sync_schedule
    assert len(lis) > 4
    assert "eth-usd-legacy" in lis
    assert "morphware-v1" not in lis
    assert "uspce-legacy" not in lis
