""" BTCUSD Price Reporter

Example of a subclassed Reporter.
"""
import asyncio
import os
from typing import Any
from typing import Optional
from typing import Tuple

from dotenv import find_dotenv
from dotenv import load_dotenv
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.gas.etherscan_gas import EtherscanGasPriceSource
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import TransactionNotFound

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feed_examples.flashbots import flashbot
from telliot_feed_examples.flashbots.provider import get_default_endpoint
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger


load_dotenv(find_dotenv())
logger = get_logger(__name__)


class FlashbotsReporter(IntervalReporter):
    """Reports values from given datafeeds to a TellorX Oracle
    every 10 seconds."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        private_key: str,
        chain_id: int,
        master: Contract,
        oracle: Contract,
        datafeed: DataFeed[Any],
        expected_profit: float = 100.0,
        gas_limit: int = 300000,
        priority_fee: float = 2.0,
    ) -> None:

        self.endpoint = endpoint
        self.master = master
        self.oracle = oracle
        self.datafeed = datafeed
        self.chain_id = chain_id
        self.user = self.endpoint.web3.eth.account.from_key(private_key).address
        self.last_submission_timestamp = 0
        self.expected_profit = expected_profit
        self.priority_fee = priority_fee
        self.gas_limit = gas_limit

        logger.info(f"Reporting with account: {self.user}")

        staked, status = asyncio.run(self.ensure_staked())
        assert staked and status.ok

        # Set up flashbots
        self.account: LocalAccount = Account.from_key(private_key)
        self.signature: LocalAccount = Account.from_key(
            os.environ.get("SIGNATURE_PRIVATE_KEY")
        )

        assert self.signature is not None
        assert self.user == self.account.address

        flashbots_uri = get_default_endpoint()
        flashbot(self.endpoint._web3, self.signature, flashbots_uri)

    async def ensure_profitable(
        self,
        base_fee: float,
    ) -> Tuple[bool, ResponseStatus]:
        """Estimate profitability

        Returns a bool signifying whether submitting for a given
        queryID would generate a net profit."""
        status = ResponseStatus()

        if self.expected_profit == "YOLO":
            return True, status  # Don't check profitability

        # Get current tips and time-based reward for given queryID
        rewards, read_status = await self.oracle.read(
            "getCurrentReward", _queryId=self.datafeed.query.query_id
        )

        # Log web3 errors
        if (not read_status.ok) or (rewards is None):
            status.ok = False
            status.error = (
                "Unable to retrieve queryID's current rewards:" + read_status.error
            )
            logger.error(status.error)
            status.e = read_status.e
            return False, status

        # Fetch token prices in USD
        price_feeds = [eth_usd_median_feed, trb_usd_median_feed]
        _ = await asyncio.gather(
            *[feed.source.fetch_new_datapoint() for feed in price_feeds]
        )
        price_eth_usd = eth_usd_median_feed.source.latest[0]
        price_trb_usd = trb_usd_median_feed.source.latest[0]

        tips, tb_reward = rewards
        max_fee = self.priority_fee + base_fee

        logger.info(
            f"""
            tips: {tips / 1e18} TRB
            time-based reward: {tb_reward / 1e18} TRB
            gas limit: {self.gas_limit}
            base fee: {base_fee}
            priority fee: {self.priority_fee}
            max fee: {max_fee}
            """
        )

        revenue = tb_reward + tips
        rev_usd = revenue / 1e18 * price_trb_usd
        costs = self.gas_limit * max_fee
        costs_usd = costs / 1e9 * price_eth_usd
        profit_usd = rev_usd - costs_usd
        logger.info(f"Estimated profit: ${round(profit_usd, 2)}")

        percent_profit = ((profit_usd) / costs_usd) * 100
        logger.info(f"Estimated percent profit: {round(percent_profit, 2)}%")

        if not percent_profit >= self.expected_profit:
            status.ok = False
            status.error = "Estimated profitability below threshold."
            logger.info(status.error)
            return False, status

        return True, status

    async def get_fee_info(self) -> int:
        """Fetch fee into from Etherscan API.
        Source: https://etherscan.io/apis"""
        c = EtherscanGasPriceSource()
        result = await c.fetch_new_datapoint()
        return result

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once

        This method checks to see if a user is able to submit
        values to the TellorX oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""

        # reporter_locked, status = await self.check_reporter_lock()
        # if reporter_locked:
        #     return None, status

        fee_info = await self.get_fee_info()
        next_base_fee = fee_info[0].suggestBaseFee

        profitable, status = await self.ensure_profitable(base_fee=next_base_fee)
        if not profitable:
            return None, status

        status = ResponseStatus()

        # Update value
        await self.datafeed.source.fetch_new_datapoint()
        latest_data = self.datafeed.source.latest

        if latest_data[0] is None:
            msg = "Unable to retrieve updated datafeed value."
            return None, error_status(msg, log=logger.info)

        query = self.datafeed.query

        try:
            value = query.value_type.encode(latest_data[0])
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        query_id = query.query_id
        query_data = query.query_data

        timestamp_count, read_status = await self.oracle.read(
            func_name="getTimestampCountById", _queryId=query_id
        )

        # Log web3 errors
        if not read_status.ok:
            status.error = (
                "Unable to retrieve timestampCount: " + read_status.error
            )  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        submit_val_func = self.oracle.contract.get_function_by_name("submitValue")
        submit_val_tx = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=timestamp_count,
            _queryData=query_data,
        )
        acc_nonce = self.endpoint._web3.eth.get_transaction_count(self.account.address)

        max_fee = next_base_fee + self.priority_fee
        logger.info(f"maxFeePerGas used: {max_fee}")
        logger.info(f"maxPriorityFeePerGas used: {self.priority_fee}")

        built_submit_val_tx = submit_val_tx.buildTransaction(
            {
                "nonce": acc_nonce,
                "gas": self.gas_limit,
                "maxFeePerGas": Web3.toWei(max_fee, "gwei"),
                # TODO: Investigate more why etherscan txs using Flashbots have
                # the same maxFeePerGas and maxPriorityFeePerGas. Example:
                # https://etherscan.io/tx/0x0bd2c8b986be4f183c0a2667ef48ab1d8863c59510f3226ef056e46658541288
                "maxPriorityFeePerGas": Web3.toWei(self.priority_fee, "gwei"),
                "chainId": self.chain_id,
            }
        )
        submit_val_tx_signed = self.account.sign_transaction(built_submit_val_tx)

        # Create bundle of one pre-signed, EIP-1559 (type 2) transaction
        bundle = [
            {"signed_transaction": submit_val_tx_signed.rawTransaction},
        ]

        # Send bundle to be executed in the next block
        block = self.endpoint._web3.eth.block_number
        result = self.endpoint._web3.flashbots.send_bundle(
            bundle, target_block_number=block + 1
        )
        logger.info(f"Bundle sent to miners in block {block}")

        # Wait for transaction confirmation
        result.wait()
        try:
            tx_receipt = result.receipts()
            print(f"Bundle was executed in block {tx_receipt[0].blockNumber}")
        except TransactionNotFound:
            print("Bundle was not executed")
            return

        status = ResponseStatus()
        if status.ok and not status.error:
            logger.info(str(tx_receipt))
            # Reset previous submission timestamp
            self.last_submission_timestamp = 0
            tx_hash = tx_receipt["transactionHash"].hex()
            # Point to relevant explorer
            logger.info(f"View reported data: \n{self.endpoint.explorer}/tx/{tx_hash}")
        else:
            logger.error(status)

        return tx_receipt, status

    async def report(self) -> None:
        """Submit latest values to the TellorX oracle every 12 hours."""

        while True:
            _, _ = await self.report_once()
            await asyncio.sleep(10)
