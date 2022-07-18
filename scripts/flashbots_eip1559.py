# Majority of this code from web3-flashbots:
# https://github.com/flashbots/web3-flashbots
"""
Minimal viable example of flashbots usage with dynamic fee transactions.
"""
import asyncio
import os

from dotenv import find_dotenv
from dotenv import load_dotenv
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams

from telliot_feeds.flashbots import flashbot
from telliot_feeds.sources.etherscan_gas import EtherscanGasPriceSource


load_dotenv(find_dotenv())


def env(key: str) -> str:
    return os.environ.get(key)


async def main() -> None:
    # account to send the transfer and sign transactions
    sender: LocalAccount = Account.from_key(env("SENDER_PRIVATE_KEY"))
    # account to receive the transfer
    receiver: LocalAccount = Account.from_key(env("RECEIVER_PRIVATE_KEY"))
    # account to establish flashbots reputation
    # NOTE: it should not store funds
    signature: LocalAccount = Account.from_key(env("SIGNATURE_PRIVATE_KEY"))

    w3 = Web3(HTTPProvider(env("PROVIDER")))
    flashbot(w3, signature, env("FLASHBOTS_HTTP_PROVIDER_URI"))

    print(
        f"""
        Sender account balance:
        {Web3.fromWei(w3.eth.get_balance(sender.address), 'ether')} ETH
        """
    )
    print(
        f"""
        Receiver account balance:
        {Web3.fromWei(w3.eth.get_balance(receiver.address), 'ether')} ETH
        """
    )

    # bundle two EIP-1559 (type 2) transactions, pre-sign one of them
    # NOTE: chainId is necessary for all EIP-1559 txns
    # NOTE: nonce is required for signed txns
    chain_id = 1
    print("chain id:", chain_id)

    c = EtherscanGasPriceSource()
    result = await c.fetch_new_datapoint()
    next_base_fee = result[0].suggestBaseFee
    print("next suggested base fee:", next_base_fee)
    max_priority = result[0].FastGasPrice
    print("priority fee:", max_priority)
    max_fee = next_base_fee + max_priority
    print("max fee:", max_fee)

    nonce = w3.eth.get_transaction_count(sender.address)
    tx1: TxParams = {
        "to": receiver.address,
        "value": Web3.toWei(0.00001, "ether"),
        "gas": 25000,
        "maxFeePerGas": Web3.toWei(max_fee, "gwei"),
        "maxPriorityFeePerGas": Web3.toWei(5, "gwei"),
        "nonce": nonce,
        "chainId": chain_id,
    }
    tx1_signed = sender.sign_transaction(tx1)

    tx2: TxParams = {
        "to": receiver.address,
        "value": Web3.toWei(0.00001, "ether"),
        "gas": 25000,
        "maxFeePerGas": Web3.toWei(max_fee, "gwei"),
        "maxPriorityFeePerGas": Web3.toWei(max_priority, "gwei"),
        "chainId": chain_id,
    }

    bundle = [
        {"signed_transaction": tx1_signed.rawTransaction},
        {"signer": sender, "transaction": tx2},
    ]

    # send bundle to be executed in the next 5 blocks
    block = w3.eth.block_number
    results = []
    for target_block in [block + k for k in [1, 2, 3, 4, 5]]:
        results.append(w3.flashbots.send_bundle(bundle, target_block_number=target_block))
    print(f"Bundle sent to miners in block {block}")

    # wait for the results
    results[-1].wait()
    try:
        receipt = results[-1].receipts()
        print(f"Bundle was executed in block {receipt[0].blockNumber}")
    except TransactionNotFound:
        print("Bundle was not executed")
        return

    print(
        f"""
        Sender account balance:
        {Web3.fromWei(w3.eth.get_balance(sender.address), 'ether')} ETH
        """
    )
    print(
        f"""
        Receiver account balance:
        {Web3.fromWei(w3.eth.get_balance(receiver.address), 'ether')} ETH
        """
    )


if __name__ == "__main__":
    asyncio.run(main())
