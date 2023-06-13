import pytest
from brownie import accounts
from brownie import DIVAProtocolMock
from brownie import DIVATellorOracleMock
from telliot_core.apps.core import TelliotCore

from telliot_feeds.integrations.diva_protocol.contract import DivaOracleTellorContract
from telliot_feeds.integrations.diva_protocol.contract import DivaProtocolContract
from telliot_feeds.integrations.diva_protocol.contract import PoolParameters

# from telliot_core.utils.response import ResponseStatus


@pytest.fixture
def diva_mock_contract():
    """Mock the DIVA contract"""
    return accounts[0].deploy(DIVAProtocolMock)


@pytest.fixture
def diva_oracle_mock_contract():
    """Mock the DIVAOracle contract"""
    return accounts[0].deploy(DIVATellorOracleMock, 3600, "0x0000000000000000000000000000000000001234")


@pytest.mark.asyncio
async def test_diva_protocol_contract(mumbai_test_cfg, diva_mock_contract):
    """Test the DIVAProtocol contract"""
    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        diva = DivaProtocolContract(core.endpoint, account)
        diva.address = diva_mock_contract.address  # Override with locally-deployed mock contract address
        diva.connect()

        assert diva.address == diva_mock_contract.address

        pool_id_example = "0x0ccf69d6832bcb70d201cd5d4014799d4e5b9944d7644522bfabecfe147ec2a0"
        p = await diva.get_pool_parameters(pool_id=pool_id_example)
        print(p)
        assert isinstance(p, PoolParameters)
        assert isinstance(p.reference_asset, str)
        assert isinstance(p.expiry_time, int)
        assert isinstance(p.floor, int)
        assert isinstance(p.inflection, int)
        assert isinstance(p.cap, int)
        assert isinstance(p.collateral_token, str)
        assert isinstance(p.collateral_balance, int)
        assert isinstance(p.short_token, str)
        assert isinstance(p.long_token, str)
        assert isinstance(p.final_reference_value, int)
        assert isinstance(p.status_final_reference_value, int)
        assert isinstance(p.status_timestamp, int)
        assert isinstance(p.data_provider, str)
        assert isinstance(p.settlement_fee, int)
        assert isinstance(p.capacity, int)

        assert p.reference_asset == "ETH/USD"
        assert p.expiry_time == 1657349074
        assert p.floor == 2000000000000000000000
        assert p.inflection == 2000000000000000000000
        assert p.cap == 4500000000000000000000
        assert p.collateral_token == "0x867e53feDe91d27101E062BF7002143EbaEA3e30"
        assert p.collateral_balance >= 214199598796389167516
        assert p.short_token == "0x91E75Aebda86a6B02d5510438f2981AC4Af1A44d"
        assert p.long_token == "0x945b1fA4DB6Fb1f8d3C7501968F6549C8c147D4e"
        assert p.final_reference_value == 0
        assert p.status_final_reference_value == 0
        assert p.status_timestamp == 1647349398
        assert p.data_provider == "0xED6D661645a11C45F4B82274db677867a7D32675"
        assert p.settlement_fee == 500000000000000
        assert p.capacity == 0


@pytest.mark.asyncio
async def test_diva_tellor_oracle_contract(mumbai_test_cfg, diva_oracle_mock_contract):
    """Test the DIVAOracleTellor contract"""
    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        oracle = DivaOracleTellorContract(core.endpoint, account)
        oracle.address = diva_oracle_mock_contract.address  # Override with locally-deployed mock contract address
        oracle.connect()

        assert oracle.address == diva_oracle_mock_contract.address

        t = await oracle.get_min_period_undisputed()
        print(t)
        assert isinstance(t, int)
        assert t == 3600  # seconds

        # status = await oracle.set_final_reference_value(
        # pool_id=159, legacy_gas_price=100
        # )
        # assert isinstance(status, ResponseStatus)
        # assert status.ok
