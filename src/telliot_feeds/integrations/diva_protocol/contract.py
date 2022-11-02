import logging
from dataclasses import dataclass
from typing import Any
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.contract.contract import Contract
from telliot_core.directory import contract_directory
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus


logger = logging.getLogger(__name__)


@dataclass
class PoolParameters:
    """Source: https://github.com/tellor-io/dataSpecs/blob/main/types/DIVAProtocolPolygon.md"""

    reference_asset: str  # (string) Reference asset string (e.g., "BTC/USD", "ETH Gas Price (Wei)", "TVL Locked in DeFi", etc.) # noqa: E501
    expiry_time: int  # (uint256) Expiration time of the pool and as of time of final value expressed as a unix timestamp in seconds # noqa: E501
    floor: int  # (uint256) Reference asset value at or below which all collateral will end up in the short pool
    inflection: int  # (uint256) Threshold for rebalancing between the long and the short side of the pool
    cap: int  # (uint256) Reference asset value at or above which all collateral will end up in the long pool
    supply_initial: int  # (uint256) Initial short and long token supply
    collateral_token: str  # (address) Address of ERC20 collateral token
    collateral_balance_short_initial: int  # (uint256) Collateral balance of short side at pool creation
    collateral_balance_long_initial: int  # (uint256) Collateral balance of long side at pool creation
    collateral_balance: int  # (uint256) Current total pool collateral balance
    short_token: str  # (address) Short position token address
    long_token: str  # (address) Long position token address
    final_reference_value: int  # (uint256) Reference asset value at the time of expiration
    status_final_reference_value: int  # (Status) Status of final reference price (0 = Open, 1 = Submitted, 2 = Challenged, 3 = Confirmed) # noqa: E501
    redemption_amount_long_token: int  # (uint256) Payout amount per long position token
    redemption_amount_short_token: int  # (uint256) Payout amount per short position token
    status_timestamp: int  # (uint256) Timestamp of status change
    data_provider: str  # (address) Address of data provider
    redemption_fee: int  # (uint256) Redemption fee prevailing at the time of pool creation
    settlement_fee: int  # (uint256) Settlement fee prevailing at the time of pool creation
    capacity: int  # (uint256) Maximum collateral that the pool can accept; 0 for unlimited


class DivaProtocolContract(Contract):
    """Main Diva Protocol contract."""

    def __init__(self, node: RPCEndpoint, account: Optional[ChainedAccount] = None):
        chain_id = node.chain_id
        assert chain_id is not None and chain_id in (
            137,  # Polygon mainnet
            80001,  # Polygon Mumbai testnet
            3,  # Ropsten
            5,  # Goerli
        )

        contract_info = contract_directory.find(chain_id=chain_id, name="diva-protocol")[0]
        if not contract_info:
            raise Exception(f"Diva Protocol contract not found on chain_id {chain_id}")

        contract_abi = contract_info.get_abi(chain_id=chain_id)

        super().__init__(
            address=contract_info.address[chain_id],
            abi=contract_abi,
            node=node,
            account=account,
        )

    async def get_pool_parameters(self, pool_id: int) -> Optional[tuple[Any]]:
        """Fetches info about a specific pool.

        Used for getting the referenceAsset mostly ('BTC/USD', for example)."""

        pool_params, status = await self.read("getPoolParameters", _poolId=pool_id)

        if status.ok:

            return PoolParameters(*pool_params)  # type: ignore
        else:
            logger.error("Error getting pool params from DivaProtocolContract")
            logger.error(status)
            return None

    async def get_latest_pool_id(self) -> None:
        raise NotImplementedError


class DivaOracleTellorContract(Contract):
    """Diva contract used for settling derivatives pools."""

    def __init__(
        self,
        node: RPCEndpoint,
        account: Optional[ChainedAccount] = None,
    ):
        chain_id = node.chain_id
        try:
            contract_info = contract_directory.find(chain_id=chain_id, name="diva-oracle-tellor")[0]
        except IndexError:
            raise Exception(f"DIVA Tellor middleware contract not found on chain_id {chain_id}")
        if not contract_info:
            raise Exception(f"diva-oracle-tellor contract info not found on chain_id {chain_id}")

        contract_abi = contract_info.get_abi(chain_id=chain_id)

        super().__init__(
            address=contract_info.address[chain_id],
            abi=contract_abi,
            node=node,
            account=account,
        )

    async def get_min_period_undisputed(self) -> Optional[int]:
        """How long the latest value reported must remain uncontested
        before the pool can be settled."""

        seconds, status = await self.read("getMinPeriodUndisputed")

        if status.ok:
            assert isinstance(seconds, int)
            return seconds
        else:
            logger.error("Error getting min period undisputed from DivaOracleTellorContract")
            logger.error(status)
            return None

    async def set_final_reference_value(
        self,
        pool_id: int,
        legacy_gas_price: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        gas_limit: int = 320000,
    ) -> Optional[ResponseStatus]:
        """Settle a pool.

        Must be called after the the minimum period undisputed has elapsed."""

        print(f"setfinalref middleware address: {self.address}")
        _, status = await self.write(
            "setFinalReferenceValue",
            _poolId=pool_id,
            gas_limit=gas_limit,
            legacy_gas_price=legacy_gas_price,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            max_fee_per_gas=max_fee_per_gas,
        )

        if status.ok:
            return status
        else:
            logger.error("Error setting final reference value on DivaOracleTellorContract")
            logger.error(status)
            return None
