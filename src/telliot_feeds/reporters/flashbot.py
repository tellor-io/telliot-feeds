""" BTCUSD Price Reporter

Example of a subclassed Reporter.
"""
from typing import Any
from typing import Optional
from typing import Tuple

from chained_accounts import ChainedAccount
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from eth_utils import to_checksum_address
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import TransactionNotFound

from telliot_feeds.flashbots import flashbot  # type: ignore
from telliot_feeds.flashbots.provider import get_default_endpoint  # type: ignore
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class FlashbotsReporter(Tellor360Reporter):
    """Reports values from given datafeeds to a TellorX Oracle
    every 10 seconds."""

    def __init__(self, signature_account: ChainedAccount, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.account: LocalAccount = Account.from_key(self.account.key)
        self.signature_account: LocalAccount = Account.from_key(signature_account.key)
        self.sig_acct_addr = to_checksum_address(signature_account.address)

        logger.info(f"Reporting with account: {self.acct_addr}")
        logger.info(f"Signature address: {self.sig_acct_addr}")

        flashbots_uri = get_default_endpoint(self.chain_id)
        logger.info(f"Flashbots provider endpoint: {flashbots_uri}")
        flashbot(self.endpoint._web3, self.signature_account, flashbots_uri)

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Report query value once

        This method checks to see if a user is able to submit
        values to the TellorX oracle, given their staker status
        and last submission time. Also, this method does not
        submit values if doing so won't make a profit."""
        staked, status = await self.ensure_staked()
        if not staked and status.ok:
            return None, status

        status = await self.check_reporter_lock()
        if not status.ok:
            return None, status

        datafeed = await self.fetch_datafeed()
        if datafeed is None:
            return None, error_status(note="Unable to fetch datafeed", log=logger.warning)

        logger.info(f"Current query: {datafeed.query.descriptor}")

        status = await self.ensure_profitable(datafeed)
        if not status.ok:
            return None, status

        status = ResponseStatus()

        # Update datafeed value
        await datafeed.source.fetch_new_datapoint()
        latest_data = datafeed.source.latest
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
        timestamp_count, read_status = await self.oracle.read(func_name="getNewValueCountbyQueryId", _queryId=query_id)
        if not read_status.ok:
            status.error = "Unable to retrieve newValueCount: " + read_status.error  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

        # Start transaction build
        submit_val_func = self.oracle.contract.get_function_by_name("submitValue")
        submit_val_tx = submit_val_func(
            _queryId=query_id,
            _value=value,
            _nonce=timestamp_count,
            _queryData=query_data,
        )
        acc_nonce = self.endpoint._web3.eth.get_transaction_count(self.acct_addr)

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
            built_submit_val_tx = submit_val_tx.buildTransaction(
                {
                    "nonce": acc_nonce,
                    "gas": self.gas_limit,
                    "gasPrice": Web3.toWei(self.legacy_gas_price, "gwei"),  # type: ignore
                    "chainId": self.chain_id,
                }
            )

        submit_val_tx_signed = self.account.sign_transaction(built_submit_val_tx)  # type: ignore

        # Create bundle of one pre-signed, EIP-1559 (type 2) transaction
        bundle = [
            {"signed_transaction": submit_val_tx_signed.rawTransaction},
        ]

        # Send bundle to be executed in the next block
        block = self.endpoint._web3.eth.block_number
        # results = []
        # for target_block in [block + k for k in [1, 2, 3, 4, 5]]:
        #     results.append(
        #         self.endpoint._web3.flashbots.send_bundle(
        #             bundle, target_block_number=target_block
        #         )
        #     )
        # result = results[-1]
        result = self.endpoint._web3.flashbots.send_bundle(bundle, target_block_number=block + 1)
        logger.info(f"Bundle sent to miners in block {block}")

        # Wait for transaction confirmation
        result.wait()
        try:
            tx_receipt = result.receipts()[0]
            print(f"Bundle was executed in block {tx_receipt.blockNumber}")
        except TransactionNotFound as e:
            status.error = "Bundle was not executed: " + str(e)
            logger.error(status.error)
            status.e = e
            return None, status

        status = ResponseStatus()
        if status.ok and not status.error:
            # Reset previous submission timestamp
            self.last_submission_timestamp = 0
            tx_hash = tx_receipt["transactionHash"].hex()
            # Point to relevant explorer
            logger.info(f"View reported data: \n{self.endpoint.explorer}/tx/{tx_hash}")
        else:
            logger.error(status)

        return tx_receipt, status
