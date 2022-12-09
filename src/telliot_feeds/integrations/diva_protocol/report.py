"""
DIVA Protocol Reporter
"""
import asyncio
import time
from typing import Any
from typing import Optional
from typing import Tuple

from eth_utils import to_checksum_address
from telliot_core.utils.key_helpers import lazy_unlock_account
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.integrations.diva_protocol import DIVA_TELLOR_MIDDLEWARE_ADDRESS
from telliot_feeds.integrations.diva_protocol.contract import DivaOracleTellorContract
from telliot_feeds.integrations.diva_protocol.feed import assemble_diva_datafeed
from telliot_feeds.integrations.diva_protocol.pool import DivaPool
from telliot_feeds.integrations.diva_protocol.pool import fetch_from_subgraph
from telliot_feeds.integrations.diva_protocol.pool import query_valid_pools
from telliot_feeds.integrations.diva_protocol.utils import filter_valid_pools
from telliot_feeds.integrations.diva_protocol.utils import get_reported_pools
from telliot_feeds.integrations.diva_protocol.utils import update_reported_pools
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import has_native_token_funds


logger = get_logger(__name__)


class DIVAProtocolReporter(Tellor360Reporter):
    """
    DIVA Protocol Reporter
    """

    def __init__(  # type: ignore
        self,
        middleware_address: str = DIVA_TELLOR_MIDDLEWARE_ADDRESS,
        diva_diamond_address: str = DIVA_DIAMOND_ADDRESS,
        network_name: str = "goerli",
        extra_undisputed_time: int = 0,
        wait_before_settle: int = 0,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.extra_undisputed_time = extra_undisputed_time
        self.wait_before_settle = wait_before_settle
        self.settle_period: Optional[int] = None
        self.network_name = network_name
        self.diva_diamond_address = diva_diamond_address
        self.middleware_contract = DivaOracleTellorContract(
            node=self.endpoint,
            account=self.account,
        )
        self.middleware_contract.address = middleware_address
        self.middleware_contract.connect()

    async def filter_unreported_pools(self, pools: list[DivaPool]) -> list[DivaPool]:
        """
        Retrieves first unreported pool.
        """
        # also check against local cache of reported pools
        local_stored_reported = get_reported_pools()
        unreported_pools = []
        for pool in pools:
            if pool.pool_id in local_stored_reported:
                logger.info(f"Pool {pool.pool_id} already reported. Checked against local storage.")
                continue

            query = DIVAProtocol(
                poolId=pool.pool_id, divaDiamond=self.diva_diamond_address, chainId=self.endpoint.chain_id
            )
            report_count, read_status = await self.get_num_reports_by_id(query.query_id)

            if not read_status.ok:
                logger.error(f"Unable to read from tellor oracle: {read_status.error}")
                continue

            if report_count > 0:
                logger.info(f"Pool {pool.pool_id} already reported. Checked against Tellor oracle.")
                continue

            unreported_pools.append(pool)
            if len(unreported_pools) > 0:
                break
        return unreported_pools

    async def fetch_unfiltered_pools(self, query: str, network: str) -> Optional[list[dict[str, Any]]]:
        """
        Fetch unfiltered derivates pools.
        """
        return await fetch_from_subgraph(
            query=query,
            network=network,
        )

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        """Fetch datafeed"""
        # fetch pools from DIVA subgraph
        query = query_valid_pools(
            last_id=0,
            data_provider=self.middleware_contract.address,
        )
        pools = await self.fetch_unfiltered_pools(
            query=query,
            network=self.network_name,
        )
        if pools is None or len(pools) == 0:
            logger.info("No pools found from subgraph query")
            return None

        # filter for supported pools & pools that haven't been reported for yet
        valid_pools = filter_valid_pools(pools)
        unreported_pools = await self.filter_unreported_pools(valid_pools)
        if unreported_pools is None or len(unreported_pools) == 0:
            logger.info("No pools found to report to")
            return None

        # choose a pool to report for (fake profit calculation, just choose 1st)
        pool = unreported_pools[0]
        logger.info(f"Reporting pool expiry time: {pool.expiry_time}")
        logger.info(f"Current time: {int(time.time())}")

        # create datafeed
        datafeed = assemble_diva_datafeed(
            pool=pool,
            diva_diamond=self.diva_diamond_address,
            chain_id=self.endpoint.chain_id,
        )
        if datafeed is None:
            msg = "Unable to assemble DIVA Protocol datafeed"
            error_status(note=msg, log=logger.warning)
            return None
        self.datafeed = datafeed
        return datafeed

    async def set_final_ref_value(self, pool_id: int, gas_price: int) -> ResponseStatus:
        return await self.middleware_contract.set_final_reference_value(pool_id=pool_id, legacy_gas_price=gas_price)

    async def settle_pool(self, pool_id: int) -> ResponseStatus:
        """Settle pool"""
        if not self.legacy_gas_price:
            gas_price = await self.fetch_gas_price(self.gas_price_speed)
            if not gas_price:
                msg = "Unable to fetch gas price for tx type 0"
                return error_status(note=msg, log=logger.warning)
        else:
            gas_price = self.legacy_gas_price

        status = await self.set_final_ref_value(pool_id=pool_id, gas_price=gas_price)
        if status is not None and status.ok:
            logger.info(f"Pool {pool_id} settled.")
            return status
        else:
            msg = f"Unable to settle pool: {pool_id}"
            return error_status(note=msg, log=logger.warning)

    async def settle_pools(self) -> ResponseStatus:
        """
        Settle pools

        Fetch available pools to settle from pickled dictionary,
        settle them by calling setFinalReferenceValue, & update
        pickled dictionary.
        """
        logger.info("Settling pools...")
        # Get pools to settle
        reported_pools = get_reported_pools()
        if reported_pools is None or len(reported_pools) == 0:
            return error_status(note="No pools to settle", log=logger.info)

        if self.settle_period is None:
            self.settle_period = await self.middleware_contract.get_min_period_undisputed()
        if self.settle_period is None:
            return error_status(note="Unable to get min period undisputed from middleware contract", log=logger.warning)

        # Settle pools
        pools_settled = []
        for pool_id, (time_submitted, pool_status) in reported_pools.items():
            if pool_status == "settled":
                continue
            if pool_status == "error":
                continue
            cur_time = int(time.time())
            if (time_submitted + self.settle_period + self.extra_undisputed_time) < cur_time:
                logger.info(
                    f"Settling pool {pool_id} reported at {time_submitted} given "
                    f"current time {cur_time} and settle period {self.settle_period} plus {self.extra_undisputed_time}"
                )
                status = await self.settle_pool(pool_id)
                if not status.ok:
                    logger.error(f"Unable to settle pool {status.error}")
                    reported_pools[pool_id] = [time_submitted, "error"]
                    continue
                pools_settled.append(pool_id)

        # Update pickled dictionary
        for pool_id in pools_settled:
            reported_pools[pool_id][1] = "settled"

        if len(pools_settled) > 0:
            logger.info(f"Settled {len(pools_settled)} pools")
        else:
            logger.info("No pools settled")
        # Update pickled dictionary
        update_reported_pools(pools=reported_pools)
        return ResponseStatus()

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query response to a TellorFlex oracle."""
        staked, status = await self.ensure_staked()
        if not staked or not status.ok:
            logger.warning(status.error)
            return None, status

        status = await self.check_reporter_lock()
        if not status.ok:
            return None, status

        datafeed = await self.fetch_datafeed()
        if not datafeed:
            msg = "Unable to fetch DIVA Protocol datafeed."
            return None, error_status(note=msg, log=logger.info)

        logger.info(f"Current query: {datafeed.query.descriptor}")

        status = ResponseStatus()

        address = to_checksum_address(self.account.address)

        # Update datafeed value
        latest_data = await datafeed.source.fetch_new_datapoint()
        if latest_data[0] is None:
            msg = "Unable to retrieve updated datafeed value."
            return None, error_status(msg, log=logger.info)

        # Get query info & encode value to bytes
        query = datafeed.query
        query_id = query.query_id
        query_data = query.query_data
        try:
            value = query.value_type.encode(latest_data[0])
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        # Get nonce
        report_count, read_status = await self.get_num_reports_by_id(query_id)

        if not read_status.ok:
            status.error = "Unable to retrieve report count: " + read_status.error  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        # Start transaction build
        submit_val_func = self.oracle.contract.get_function_by_name("submitValue")
        submit_val_tx = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=report_count,
            _queryData=query_data,
        )
        acc_nonce = self.endpoint._web3.eth.get_transaction_count(address)

        # Add transaction type 2 (EIP-1559) data
        if self.transaction_type == 2:
            logger.info(f"maxFeePerGas: {self.max_fee}")
            logger.info(f"maxPriorityFeePerGas: {self.priority_fee}")

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "maxFeePerGas": Web3.toWei(self.max_fee, "gwei"),  # type: ignore
                    # TODO: Investigate more why etherscan txs using Flashbots have
                    # the same maxFeePerGas and maxPriorityFeePerGas. Example:
                    # https://etherscan.io/tx/0x0bd2c8b986be4f183c0a2667ef48ab1d8863c59510f3226ef056e46658541288 # noqa: E501
                    "maxPriorityFeePerGas": Web3.toWei(self.priority_fee, "gwei"),  # noqa: E501
                    "chainId": self.chain_id,
                }
            )
        # Add transaction type 0 (legacy) data
        else:
            # Fetch legacy gas price if not provided by user
            if not self.legacy_gas_price:
                gas_price = await self.fetch_gas_price(self.gas_price_speed)
                if not gas_price:
                    note = "Unable to fetch gas price for tx type 0"
                    return None, error_status(note, log=logger.warning)
            else:
                gas_price = self.legacy_gas_price

            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "gasPrice": Web3.toWei(gas_price, "gwei"),
                    "chainId": self.chain_id,
                }
            )

        lazy_unlock_account(self.account)
        local_account = self.account.local_account
        tx_signed = local_account.sign_transaction(built_submit_val_tx)

        try:
            logger.debug("Sending submitValue transaction")
            tx_hash = self.endpoint._web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        except Exception as e:
            note = "Send transaction failed"
            return None, error_status(note, log=logger.error, e=e)

        # Confirm submitValue transaction
        try:
            tx_receipt = self.endpoint._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
            tx_url = f"{self.endpoint.explorer}/tx/{tx_hash.hex()}"

            if tx_receipt["status"] == 0:
                msg = f"Transaction reverted: {tx_url}"
                return tx_receipt, error_status(msg, log=logger.error)
        except Exception as e:
            note = "Failed to confirm transaction"
            return None, error_status(note, log=logger.error, e=e)

        if status.ok and not status.error:
            self.last_submission_timestamp = 0
            # Update reported pools
            pools = get_reported_pools()
            cur_time = int(time.time())
            update_reported_pools(pools=pools, add=[[datafeed.query.poolId, [cur_time, "not settled"]]])
            logger.info(f"View reported data at timestamp {cur_time}: \n{tx_url}")
        else:
            logger.error(status)

        return tx_receipt, status

    async def report(self, report_count: Optional[int] = None) -> None:
        """Report values for pool reference assets & settle pools."""
        while report_count is None or report_count > 0:
            online = await self.is_online()
            if not online:
                logger.warning("Unable to connect to the internet!")
            else:
                if has_native_token_funds(self.acct_addr, self.endpoint._web3):
                    _, _ = await self.report_once()
                    await asyncio.sleep(self.wait_before_settle)
                    _ = await self.settle_pools()

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)
            if report_count is not None:
                report_count -= 1
