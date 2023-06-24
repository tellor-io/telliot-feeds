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
from requests.exceptions import HTTPError
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt

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
        self.account._local_account = Account.from_key(self.account.key)
        self.signature_account: LocalAccount = Account.from_key(signature_account.key)
        self.sig_acct_addr = to_checksum_address(signature_account.address)

        logger.info(f"Reporting with account: {self.acct_addr}")
        logger.info(f"Signature address: {self.sig_acct_addr}")

        flashbots_uri = get_default_endpoint(self.chain_id)
        logger.info(f"Flashbots provider endpoint: {flashbots_uri}")
        flashbot(self.endpoint._web3, self.signature_account, flashbots_uri)

    def sign_n_send_transaction(self, built_tx: Any) -> Tuple[Optional[TxReceipt], ResponseStatus]:
        status = ResponseStatus()
        # Create bundle of one pre-signed, EIP-1559 (type 2) transaction
        tx_signed = self.account.local_account.sign_transaction(built_tx)
        bundle = [
            {"signed_transaction": tx_signed.rawTransaction},
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
        try:
            result = self.endpoint._web3.flashbots.send_bundle(bundle, target_block_number=block + 1)
        except HTTPError as e:
            msg = "Unable to send bundle to miners due to HTTP error"
            return None, error_status(note=msg, e=e, log=logger.error)

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

        tx_hash = tx_receipt["transactionHash"].hex()
        # Point to relevant explorer
        logger.info(f"View reported data: \n{self.endpoint.explorer}/tx/{tx_hash}")

        return tx_receipt, status
