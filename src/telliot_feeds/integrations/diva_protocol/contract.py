import logging
from dataclasses import dataclass
from typing import Any
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.contract.contract import Contract
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.abi import DIVA_ABI


logger = logging.getLogger(__name__)


@dataclass
class PoolParameters:
    """Source: https://github.com/divaprotocol/diva-protocol-v1/blob/main/diamondABI/diamond.json#L1674"""

    floor: int
    inflection: int
    cap: int
    gradient: int
    collateral_balance: int
    final_reference_value: int
    capacity: int
    status_timestamp: int
    short_token: str
    payout_short: int
    long_token: str
    payout_long: int
    collateral_token: str
    expiry_time: int
    data_provider: str
    protocol_fee: int
    settlement_fee: int
    status_final_reference_value: int
    reference_asset: str


class DivaProtocolContract(Contract):
    """Main Diva Protocol contract."""

    def __init__(self, node: RPCEndpoint, account: Optional[ChainedAccount] = None):
        super().__init__(
            address=DIVA_DIAMOND_ADDRESS,
            abi=DIVA_ABI,
            node=node,
            account=account,
        )

    async def get_pool_parameters(self, pool_id: str) -> Optional[tuple[Any]]:
        """Fetches info about a specific pool.

        Used for getting the referenceAsset mostly ('BTC/USD', for example)."""
        pool_params, status = await self.read("getPoolParameters", _poolId=pool_id)

        if status.ok:
            return PoolParameters(*pool_params)  # type: ignore
        else:
            logger.error("Error getting pool params from DivaProtocolContract")
            logger.error(status)
            return None


class DivaOracleTellorContract(Contract):
    """Diva contract used for settling derivatives pools."""

    def __init__(
        self,
        node: RPCEndpoint,
        account: Optional[ChainedAccount] = None,
    ):
        super().__init__(
            address=DIVA_TELLOR_MIDDLEWARE_ADDRESS,
            abi=DIVA_ABI,
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
        pool_id: str,
        legacy_gas_price: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        gas_limit: Optional[int] = None,
    ) -> Optional[ResponseStatus]:
        """Settle a pool.

        Must be called after the the minimum period undisputed has elapsed."""
        _, status = await self.write(
            "setFinalReferenceValue",
            _poolId=pool_id,
            _tippingTokens=[],
            _claimDIVAReward=False,
            gas_limit=gas_limit,
            legacy_gas_price=legacy_gas_price,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            max_fee_per_gas=max_fee_per_gas,
        )

        if status.ok:
            return status
        else:
            logger.error("Error setting final reference value on DivaOracleTellorContract")
            logger.info(f"Pool ID: {pool_id}")
            logger.info(f"Middleware address: {self.address}")
            logger.error(status)
            return None
