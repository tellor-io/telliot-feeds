"""TellorRNG auto submitter.
submits TellorRNG values at a fixed time interval
"""
import asyncio
import calendar
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
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.tellor_rng_feed import assemble_rng_datafeed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.queries.tellor_rng import TellorRNG
from telliot_feeds.reporters.reporter_autopay_utils import get_feed_tip
from telliot_feeds.reporters.tellorflex import TellorFlexReporter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

INTERVAL = 60 * 30  # 30 minutes
START_TIME = 1653350400  # 2022-5-24 00:00:00 GMT


def get_next_timestamp() -> int:
    """get next target timestamp"""
    now = calendar.timegm(time.gmtime())
    target_ts = START_TIME + (now - START_TIME) // INTERVAL * INTERVAL
    return target_ts


class RNGReporter(TellorFlexReporter):
    """Reports TellorRNG values at a fixed interval to TellorFlex
    on Polygon."""

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        status = ResponseStatus()

        rng_timestamp = get_next_timestamp()
        query = TellorRNG(rng_timestamp)
        report_count, read_status = await self.get_num_reports_by_id(query.query_id)

        if not read_status.ok:
            status.error = "Unable to retrieve report count: " + read_status.error  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None

        if report_count > 0:
            status.ok = False
            status.error = f"Latest timestamp in interval {rng_timestamp} already reported"
            logger.info(status.error)
            return None

        datafeed = await assemble_rng_datafeed(timestamp=rng_timestamp, node=self.endpoint, account=self.account)
        if datafeed is None:
            msg = "Unable to assemble RNG datafeed"
            error_status(note=msg, log=logger.warning)
            return None
        self.datafeed = datafeed
        tip = 0

        single_tip, status = await self.autopay.get_current_tip(datafeed.query.query_id)
        if not status.ok:
            msg = "Unable to fetch single tip"
            error_status(msg, log=logger.warning)
            return None
        tip += single_tip

        feed_tip = await get_feed_tip(
            datafeed.query.query_data, self.autopay
        )  # input query data instead of query id to use tip listener
        if feed_tip is None:
            msg = "Unable to fetch feed tip"
            error_status(msg, log=logger.warning)
            return None
        tip += feed_tip

        # Fetch token prices in USD
        price_feeds = [matic_usd_median_feed, trb_usd_median_feed]
        _ = await asyncio.gather(*[feed.source.fetch_new_datapoint() for feed in price_feeds])
        price_matic_usd = matic_usd_median_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]
        if price_matic_usd is None or price_trb_usd is None:
            msg = "Unable to fetch token prices"
            error_status(msg, log=logger.warning)
            return None

        # Using transaction type 2 (EIP-1559)
        if self.transaction_type == 2:
            fee_info = await self.get_fee_info()
            base_fee = fee_info[0].suggestBaseFee

            # No miner tip provided by user
            if self.priority_fee is None:
                # From etherscan docs:
                # "Safe/Proposed/Fast gas price recommendations are now modeled as Priority Fees."  # noqa: E501
                # Source: https://docs.etherscan.io/api-endpoints/gas-tracker
                priority_fee = fee_info[0].SafeGasPrice
                self.priority_fee = priority_fee

            if self.max_fee is None:
                # From Alchemy docs:
                # "maxFeePerGas = baseFeePerGas + maxPriorityFeePerGas"
                # Source: https://docs.alchemy.com/alchemy/guides/eip-1559/maxpriorityfeepergas-vs-maxfeepergas  # noqa: E501
                self.max_fee = self.priority_fee + base_fee

            logger.info(
                f"""
                tips: {tip} TRB
                gas limit: {self.gas_limit}
                base fee: {base_fee}
                priority fee: {self.priority_fee}
                max fee: {self.max_fee}
                """
            )

            costs = self.gas_limit * self.max_fee

        # Using transaction type 0 (legacy)
        else:
            # Fetch legacy gas price if not provided by user
            if not self.legacy_gas_price:
                gas_price = await self.fetch_gas_price()
                self.legacy_gas_price = gas_price

            if not self.legacy_gas_price:
                note = "unable to fetch gas price from api"
                error_status(note, log=logger.info)
                return None
            logger.info(
                f"""
                tips: {tip/1e18} TRB
                gas limit: {self.gas_limit}
                legacy gas price: {self.legacy_gas_price}
                """
            )
            costs = self.gas_limit * self.legacy_gas_price

        # Calculate profit
        rev_usd = tip / 1e18 * price_trb_usd
        costs_usd = costs / 1e9 * price_matic_usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")
        logger.info(f"tip price: {round(rev_usd, 2)}, gas costs: {costs_usd}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")
        if (self.expected_profit != "YOLO") and (
            isinstance(self.expected_profit, float) and percent_profit < self.expected_profit
        ):
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            return None

        return datafeed

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once
        This method checks to see if a user is able to submit
        values to the Tellor oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""
        # Check staker status
        staked, status = await self.ensure_staked()
        if not staked or not status.ok:
            logger.warning(status.error)
            return None, status

        status = await self.check_reporter_lock()
        if not status.ok:
            return None, status

        # Get suggested datafeed if none provided
        datafeed = await self.fetch_datafeed()
        if not datafeed:
            msg = "no datafeed suggestions available"
            return None, error_status(note=msg, log=logger.info)

        logger.info(f"Current query: {datafeed.query.descriptor}")

        status = await self.ensure_profitable(datafeed)
        if not status.ok:
            return None, status

        status = ResponseStatus()

        address = to_checksum_address(self.account.address)

        # Update datafeed value
        latest_data = await datafeed.source.fetch_new_datapoint()
        # latest_data = datafeed.source.latest
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

        try:
            # Confirm transaction
            tx_receipt = self.endpoint._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)

            tx_url = f"{self.endpoint.explorer}/tx/{tx_hash.hex()}"

            if tx_receipt["status"] == 0:
                msg = f"Transaction reverted. ({tx_url})"
                return tx_receipt, error_status(msg, log=logger.error)

        except Exception as e:
            note = "Failed to confirm transaction"
            return None, error_status(note, log=logger.error, e=e)

        if status.ok and not status.error:
            # Reset previous submission timestamp
            self.last_submission_timestamp = 0
            # Point to relevant explorer
            logger.info(f"View reported data: \n{tx_url}")
        else:
            logger.error(status)

        return tx_receipt, status

    async def report(self) -> None:
        """Submit latest values to the TellorFlex oracle."""
        logger.info(f"RNG reporting interval: {INTERVAL} seconds")
        while True:
            _, _ = await self.report_once()
            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)
