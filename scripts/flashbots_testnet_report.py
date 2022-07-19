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
from web3.middleware import geth_poa_middleware

from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.flashbots import flashbot
from telliot_feeds.flashbots.provider import get_default_endpoint
from telliot_feeds.sources.etherscan_gas import EtherscanGasPriceSource
from telliot_feeds.utils.abi import gorli_playground_abi


load_dotenv(find_dotenv())


def env(key: str) -> str:
    return os.environ.get(key)


async def main() -> None:
    # account to send the transfer and sign transactions
    account: LocalAccount = Account.from_key(env("SENDER_PRIVATE_KEY"))
    # account to establish flashbots reputation
    # NOTE: it should not store funds
    signature: LocalAccount = Account.from_key(env("SIGNATURE_PRIVATE_KEY"))
    chain_id = 5

    w3 = Web3(HTTPProvider(env("PROVIDER")))
    if chain_id == 5:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    # Goerli endpoint: https://relay-goerli.flashbots.net
    endpoint = env("FLASHBOTS_HTTP_PROVIDER_URI") if chain_id == 5 else get_default_endpoint()
    flashbot(w3, signature, endpoint)

    print(
        f"""Reporter account balance:
        {Web3.fromWei(w3.eth.get_balance(account.address), 'ether')} ETH
        """
    )

    playground_contract = w3.eth.contract(
        address="0x3477EB82263dabb59AC0CAcE47a61292f28A2eA7",  # Gorli contract addr
        abi=gorli_playground_abi,
    )

    _ = await trb_usd_median_feed.source.fetch_new_datapoint()
    latest_data = trb_usd_median_feed.source.latest
    if latest_data[0] is None:
        msg = "Unable to retrieve updated datafeed value."
        print(msg)

    query = trb_usd_median_feed.query
    nonce_getter = playground_contract.get_function_by_name("getNewValueCountbyQueryId")
    timestamp_count = nonce_getter(_queryId=query.query_id).call()
    print("timestamp count (nonce):", timestamp_count)

    submit_val_func = playground_contract.get_function_by_name("submitValue")
    submit_val_tx = submit_val_func(
        _queryId=query.query_id,
        _value=query.value_type.encode(latest_data[0]),
        _nonce=timestamp_count,
        _queryData=query.query_data,
    )
    acc_nonce = w3.eth.get_transaction_count(account.address)

    # fetch tip and base fee
    c = EtherscanGasPriceSource()
    result = await c.fetch_new_datapoint()
    next_base_fee = result[0].suggestBaseFee
    print("next suggested base fee:", next_base_fee)
    max_priority = result[0].FastGasPrice
    print("priority fee:", max_priority)
    max_fee = next_base_fee + max_priority
    print("max fee:", max_fee)

    gas = 350000

    built_submit_val_tx = submit_val_tx.buildTransaction(
        {
            "nonce": acc_nonce,
            "gas": gas,
            "maxFeePerGas": Web3.toWei(max_fee, "gwei"),
            "maxPriorityFeePerGas": Web3.toWei(max_priority, "gwei"),
            "chainId": chain_id,
        }
    )
    submit_val_tx_signed = account.sign_transaction(built_submit_val_tx)

    # bundle one pre-signed, EIP-1559 (type 2) transaction
    # NOTE: chainId is necessary for all EIP-1559 txns
    # NOTE: nonce is required for signed txns

    bundle = [
        {"signed_transaction": submit_val_tx_signed.rawTransaction},
    ]

    # send bundle to be executed in the next blocks
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
    {Web3.fromWei(w3.eth.get_balance(account.address), 'ether')} ETH
    """
    )


if __name__ == "__main__":
    asyncio.run(main())
