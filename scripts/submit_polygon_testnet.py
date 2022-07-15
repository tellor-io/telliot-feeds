import asyncio
import os

from abi import erc20_abi
from abi import tellor_flex_abi
from dotenv import find_dotenv
from dotenv import load_dotenv
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider
from web3 import Web3
from web3.middleware import geth_poa_middleware

from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed


load_dotenv(find_dotenv())


def env(key: str) -> str:
    return os.environ.get(key)


async def main() -> None:
    account: LocalAccount = Account.from_key(env("polygon_pk"))

    chain_id = 80001
    staking_amount = int(1e18 * 10)  # 10 trb
    print("staking amount:", staking_amount)

    w3 = Web3(HTTPProvider(env("polygon_endpoint_url")))
    if chain_id == 80001:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    print("address:", account.address)
    print(
        f"""Reporter account balance:
        {Web3.fromWei(w3.eth.get_balance(account.address), 'ether')} MATIC
        """
    )

    # Mainnet
    if chain_id == 137:
        flex_address = "0xFd45Ae72E81Adaaf01cC61c8bCe016b7060DD537"
        trb_address = "0xE3322702BEdaaEd36CdDAb233360B939775ae5f1"
    # Mumbai testnet
    else:
        flex_address = "0x41b66dd93b03e89D29114a7613A6f9f0d4F40178"
        trb_address = "0x45cAF1aae42BA5565EC92362896cc8e0d55a2126"

    oracle = w3.eth.contract(
        address=flex_address,
        abi=tellor_flex_abi,
    )

    trb_polygon = w3.eth.contract(
        address=trb_address,
        abi=erc20_abi,
    )

    staker_info_func = oracle.get_function_by_name("getStakerInfo")
    staker_info = staker_info_func(_staker=account.address).call()
    (
        staker_startdate,
        staked_balance,
        locked_balance,
        last_report,
        num_reports,
    ) = staker_info
    print("staker start date:", staker_startdate)
    print("staked balance:", staked_balance)
    print("locked balance:", locked_balance)
    print("last report:", last_report)
    print("num reports:", num_reports)

    # # Transfer TRB & MATIC to dev-acct-9
    # print('testing transfer')
    # transfer_func = trb_polygon.get_function_by_name("transfer")
    # acc_nonce = w3.eth.get_transaction_count(account.address)
    # transfer_tx_dict = {
    #     "nonce": acc_nonce,
    #     "gas": 70000,
    #     "maxFeePerGas": Web3.toWei(1000, "gwei"),
    #     "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),
    #     "chainId": chain_id,
    # }
    # transfer_func = transfer_func(
    #     recipient="0xE0Fe38e04b8952120a8015bE08248aC85891b477", # dev-acct-9
    #     amount=1)
    # built_transfer_func = transfer_func.buildTransaction(transfer_tx_dict)
    # tx_signed = account.sign_transaction(built_transfer_func)
    # tx_hash = w3.eth.send_raw_transaction(tx_signed.rawTransaction)

    # tx_receipt = w3.eth.wait_for_transaction_receipt(
    #     tx_hash, timeout=360
    # )
    # print(tx_receipt)

    # tx_url = f"https://polygonscan.com/tx/{tx_hash.hex()}"

    # print(f"view transfer transaction: ({tx_url})")

    if staker_startdate == 0:
        print()
        print("approving deposit stake")
        approve_func = trb_polygon.get_function_by_name("approve")
        acc_nonce = w3.eth.get_transaction_count(account.address)
        approve_tx_dict = {
            "nonce": acc_nonce,
            "gas": 100000,
            "maxFeePerGas": Web3.toWei(1000, "gwei"),
            "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),
            "chainId": chain_id,
        }
        approve_func = approve_func(spender=flex_address, amount=staking_amount)
        built_approve_func = approve_func.buildTransaction(approve_tx_dict)
        tx_signed = account.sign_transaction(built_approve_func)
        tx_hash = w3.eth.send_raw_transaction(tx_signed.rawTransaction)

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
        print(tx_receipt)

        tx_url = f"https://polygonscan.com/tx/{tx_hash.hex()}"

        print(f"view approve transaction: ({tx_url})")

        print("depositing stake")
        stake_func = oracle.get_function_by_name("depositStake")
        acc_nonce = w3.eth.get_transaction_count(account.address)
        stake_tx_dict = {
            "nonce": acc_nonce,
            "gas": 300000,
            "maxFeePerGas": Web3.toWei(1000, "gwei"),
            "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),
            "chainId": chain_id,
        }
        stake_func = stake_func(_amount=staking_amount)
        built_stake_func = stake_func.buildTransaction(stake_tx_dict)
        tx_signed = account.sign_transaction(built_stake_func)
        tx_hash = w3.eth.send_raw_transaction(tx_signed.rawTransaction)

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
        print(tx_receipt)

        tx_url = f"https://polygonscan.com/tx/{tx_hash.hex()}"

        print(f"view deposit stake transaction: ({tx_url})")

    _ = await trb_usd_median_feed.source.fetch_new_datapoint()
    latest_data = trb_usd_median_feed.source.latest
    if latest_data[0] is None:
        msg = "Unable to retrieve updated datafeed value."
        print(msg)

    query = trb_usd_median_feed.query
    nonce_getter = oracle.get_function_by_name("getNewValueCountbyQueryId")
    timestamp_count = nonce_getter(_queryId=query.query_id).call()
    print("timestamp count (nonce):", timestamp_count)

    submit_val_func = oracle.get_function_by_name("submitValue")
    submit_val_tx = submit_val_func(
        _queryId=query.query_id,
        _value=query.value_type.encode(latest_data[0]),
        _nonce=timestamp_count,
        _queryData=query.query_data,
    )
    acc_nonce = w3.eth.get_transaction_count(account.address)

    gas = 350000

    built_submit_val_tx = submit_val_tx.buildTransaction(
        {
            "nonce": acc_nonce,
            "gas": gas,
            "maxFeePerGas": Web3.toWei(1000, "gwei"),
            "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),
            "chainId": chain_id,
        }
    )
    tx_signed = account.sign_transaction(built_submit_val_tx)

    tx_hash = w3.eth.send_raw_transaction(tx_signed.rawTransaction)

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
    print(tx_receipt)

    tx_url = f"https://polygonscan.com/tx/{tx_hash.hex()}"

    print(f"transaction succeeded. ({tx_url})")


if __name__ == "__main__":
    asyncio.run(main())
