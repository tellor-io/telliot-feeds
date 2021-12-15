import asyncio
import os

from dotenv import find_dotenv
from dotenv import load_dotenv
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from flashbots import flashbot
from flashbots.types import SignTx
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.contract.contract import Contract
from telliot_core.queries.legacy_query import LegacyRequest
from web3 import HTTPProvider
from web3 import Web3
from web3.exceptions import TimeExhausted
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.middleware import geth_poa_middleware

from telliot_feed_examples.utils.abi import gorli_playground_abi
from telliot_feed_examples.utils.log import get_logger


load_dotenv(find_dotenv())
logger = get_logger(__name__)

# Get configs
cfg = TelliotConfig()
ETH_ACCOUNT_SIGNATURE: LocalAccount = Account.from_key(os.getenv("SIG_ADDR"))
ETH_ACCOUNT_FROM: LocalAccount = Account.from_key(cfg.main.private_key)
endpoint = cfg.get_endpoint()

# Setup w3, flashbots, and TellorX playground contract
w3 = Web3(HTTPProvider(endpoint.url))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # only for POA chains
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(ETH_ACCOUNT_FROM))
flashbot(w3, ETH_ACCOUNT_SIGNATURE)
endpoint._web3 = w3
print("Flashbot connected to goerli relay")

playground = Contract(
    address="0x3477EB82263dabb59AC0CAcE47a61292f28A2eA7",  # Gorli playground addr
    abi=gorli_playground_abi,
    node=endpoint,
    private_key=cfg.main.private_key,
)
playground.connect()

# Submit value
query = LegacyRequest(legacy_id=99)
timestamp_count, status = asyncio.run(
    playground.read(func_name="getNewValueCountbyQueryId", _queryId=query.query_id)
)
print("Timestamp count:", timestamp_count)

acc = endpoint.web3.eth.account.from_key(cfg.main.private_key)
acc_nonce = endpoint.web3.eth.get_transaction_count(acc.address)

tx_receipt, status = asyncio.run(
    playground.write(
        func_name="submitValue",
        gas_price="3",
        acc_nonce=acc_nonce,
        _queryId=query.query_id,
        _value=query.value_type.encode(420.0),
        _nonce=timestamp_count,
        _queryData=query.query_data,
    )
)
print(status)
# print(tx_receipt)
tx_hash = tx_receipt['transactionHash'].hex()
logger.info(
    f"""View reported data: \n
    {endpoint.explorer}/tx/{tx_hash}
    """
)

print("Setting up flashbots request")

# Build bribe
nonce = w3.eth.get_transaction_count(ETH_ACCOUNT_FROM.address)
bribe = w3.toWei("0.01", "ether")

signed_tx: SignTx = {
    "to": ETH_ACCOUNT_FROM.address,
    "value": bribe,
    "nonce": nonce + 1,
    "gasPrice": 100,
    "gas": 41000,
}

signed_transaction = ETH_ACCOUNT_FROM.sign_transaction(signed_tx)  # type: ignore

# Build transaction
contract_function = playground.contract.get_function_by_name("submitValue")
transaction = contract_function(
    _queryId=query.query_id,
    _value=query.value_type.encode(420.0),
    _nonce=timestamp_count + 1,
    _queryData=query.query_data,
)
gas_limit = 400000
acc_nonce = endpoint.web3.eth.get_transaction_count(acc.address)
built_tx = transaction.buildTransaction(
    {
        "from": acc.address,
        "nonce": acc_nonce,
        "gas": gas_limit,
        "gasPrice": endpoint.web3.toWei("300", "gwei"),
        "chainId": endpoint.chain_id,
    }
)
import json
print(json.dumps(built_tx, indent=4))
# submit_tx_signed = acc.sign_transaction(built_tx)

# Assemble bundle
bundle = [
    #  some transaction
    {"signer": ETH_ACCOUNT_FROM, "transaction": built_tx},
    # the bribe
    {"signed_transaction": signed_transaction.rawTransaction},
]

# Send bundle
block = w3.eth.block_number
wait_blocks = 10
result = w3.flashbots.send_bundle(bundle, target_block_number=block + wait_blocks)  # type: ignore

print('Waiting for mined tx...')
# Wait for the transaction to get mined
while True:
    try:
        w3.eth.waitForTransactionReceipt(
            signed_transaction.hash, timeout=360, poll_latency=0.1
        )
        break

    except TimeExhausted:
        if w3.eth.blockNumber >= (block + wait_blocks):
            print("ERROR: transaction was not mined")
            exit(1)

print(f"transaction confirmed at block {w3.eth.block_number}")
