"""Submits three month rolling average of the USPCE to TellorX on Rinkeby."""
import asyncio
from typing import Optional

from telliot.apps.telliot_config import TelliotConfig
from telliot.contract.contract import Contract
from telliot.contract.gas import fetch_gas_price
from telliot.queries.legacy_query import LegacyRequest
from telliot.utils.abi import rinkeby_tellor_master
from telliot.utils.abi import rinkeby_tellor_oracle
from telliot.utils.response import ResponseStatus


def get_cfg() -> TelliotConfig:
    """Get rinkeby endpoint from config

    If environment variables are defined, they will override the values in config files
    """
    cfg = TelliotConfig()

    # Override configuration for rinkeby testnet
    cfg.main.chain_id = 4

    _ = cfg.get_endpoint()

    return cfg


def get_master(cfg: TelliotConfig) -> Optional[Contract]:
    """Helper function for connecting to a contract at an address"""
    endpoint = cfg.get_endpoint()
    if not endpoint:
        print("Could not connect to master contract.")
        return None

    endpoint.connect()
    master = Contract(
        address="0x657b95c228A5de81cdc3F85be7954072c08A6042",
        abi=rinkeby_tellor_master,  # type: ignore
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    master.connect()
    return master


def get_oracle(cfg: TelliotConfig) -> Optional[Contract]:
    """Helper function for connecting to a contract at an address"""
    endpoint = cfg.get_endpoint()
    if not endpoint:
        print("Could not connect to master contract.")
        return None

    if endpoint:
        endpoint.connect()
    oracle = Contract(
        address="0x07b521108788C6fD79F471D603A2594576D47477",
        abi=rinkeby_tellor_oracle,  # type: ignore
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    oracle.connect()
    return oracle


def parse_user_val() -> int:
    """Parse USPCE value from user input."""
    print("Enter USPCE value (example: 13659.3:")

    uspce = None

    while uspce is None:
        inpt = input()

        try:
            inpt = int(float(inpt) * 1000000)  # type: ignore
        except ValueError:
            print("Invalid input. Enter int or float.")
            continue

        print(f"Submitting value: {inpt}\nPress [ENTER] to confirm.")
        _ = input()

        uspce = inpt

    return uspce


async def submit(
    cfg: TelliotConfig, master: Contract, oracle: Contract
) -> ResponseStatus:
    """Submit USPCE value to TellorX oracle."""

    gas_price = await fetch_gas_price()  # TODO clarify gas price units
    user = master.node.web3.eth.account.from_key(cfg.main.private_key).address
    print("User:", user)

    balance, status = await master.read("balanceOf", _user=user)
    print("Current balance:", balance / 1e18)  # type: ignore

    is_staked, status = await master.read("getStakerInfo", _staker=user)
    print(is_staked)

    if is_staked is not None and is_staked[0] == 0:
        _, status = await master.write_with_retry(
            func_name="depositStake", gas_price=gas_price, extra_gas_price=20, retries=2
        )

    q = LegacyRequest(legacy_id=41)
    usr_input = parse_user_val()
    value = q.value_type.encode(usr_input)

    query_data = q.query_data
    query_id = q.query_id

    value_count, status = await oracle.read(
        func_name="getTimestampCountById", _queryId=query_id
    )

    _, status = await oracle.write_with_retry(
        func_name="submitValue",
        gas_price=gas_price,
        extra_gas_price=40,
        retries=5,
        _queryId=query_id,
        _value=value,
        _nonce=value_count,
        _queryData=query_data,
    )

    return status


if __name__ == "__main__":
    cfg = get_cfg()
    # if not cfg:
    #     return ResponseStatus(ok=False, error="Could not get default configs.", e=None)

    master = get_master(cfg)
    oracle = get_oracle(cfg)

    # if not master or not oracle:
    #     return ResponseStatus(
    #         ok=False, error="Could not connect to master or oracle contract", e=None
    #     )

    _ = asyncio.run(submit(cfg, master, oracle))  # type: ignore
