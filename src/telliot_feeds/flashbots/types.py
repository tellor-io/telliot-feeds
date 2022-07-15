# Majority of this code from web3-flashbots:
# https://github.com/flashbots/web3-flashbots
# EIP-1559 subbport by @lekhovitsky
# https://github.com/lekhovitsky
from typing import List
from typing import TypedDict

from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from web3.types import TxParams


# unsigned transaction
FlashbotsBundleTx = TypedDict(
    "FlashbotsBundleTx",
    {
        "transaction": TxParams,
        "signer": LocalAccount,
    },
)

# signed transaction
FlashbotsBundleRawTx = TypedDict(
    "FlashbotsBundleRawTx",
    {
        "signed_transaction": HexBytes,
    },
)

# transaction dict taken from w3.eth.get_block('pending', full_transactions=True)
FlashbotsBundleDictTx = TypedDict(
    "FlashbotsBundleDictTx",
    {
        "blockHash": HexBytes,
        "blockNumber": int,
        "from": str,
        "gas": int,
        "gasPrice": int,
        "maxFeePerGas": int,
        "maxPriorityFeePerGas": int,
        "hash": HexBytes,
        "input": str,
        "nonce": int,
        "r": HexBytes,
        "s": HexBytes,
        "to": str,
        "transactionIndex": int,
        "type": str,
        "v": int,
        "value": int,
    },
)

FlashbotsOpts = TypedDict(
    "FlashbotsOpts",
    {"minTimestamp": int, "maxTimestamp": int, "revertingTxHashes": List[str]},
)
