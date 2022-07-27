import os
from typing import Any
from typing import Optional

import click
from telliot_core.apps.core import TelliotCore
from telliot_core.cli.utils import cli_core

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING

from brownie import chain
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts


DIVA_PROTOCOL_CHAINS = (137, 80001, 3)


def reporter_cli_core(ctx: click.Context) -> TelliotCore:
    """Get telliot core configured in reporter CLI context"""
    # Delegate to main cli core getter
    # (handles ACCOUNT_NAME, CHAIN_ID, and TEST_CONFIG)
    core = cli_core(ctx)

    # Ensure chain id compatible with flashbots relay
    if ctx.obj["SIGNATURE_ACCOUNT_NAME"] is not None:
        # Only supports mainnet
        assert core.config.main.chain_id == 1

    if ctx.obj["TEST_CONFIG"]:
        core.config.main.chain_id = 1337
        core.config.main.url = "http://127.0.0.1:8545"

        chain.mine(10)

        accounts = find_accounts(chain_id=1337)
        if not accounts:
            # Create a test account using PRIVATE_KEY defined on github.
            key = os.getenv("PRIVATE_KEY", None)
            if key:
                ChainedAccount.add(
                    "git-tellorflex-test-key",
                    chains=1337,
                    key=os.environ["PRIVATE_KEY"],
                    password="",
                )
            else:
                raise Exception(f"Need an account for {1337}")




    assert core.config

    return core


def valid_diva_chain(chain_id: int) -> bool:
    """Ensure given chain ID supports reporting Diva Protocol data."""
    if chain_id not in DIVA_PROTOCOL_CHAINS:
        print(f"Current chain id ({chain_id}) not supported for reporting Diva Protocol data.")
        return False
    return True


def build_feed_from_input() -> Optional[DataFeed[Any]]:
    """
    Build a DataFeed from CLI input
    """
    try:
        query_type = input("Enter a valid Query Type: ")
        feed = DATAFEED_BUILDER_MAPPING[query_type]
    except KeyError:
        click.echo(f"No corresponding datafeed found for Query Type: {query_type}\n")
        return None
    try:
        for query_param in feed.query.__dict__.keys():
            # accessing the datatype
            param_dtype = feed.query.__annotations__[query_param]
            val = input(f"Enter value for Query Parameter {query_param}: ")

            if val is not None:
                # cast input from string to datatype of query parameter
                val = param_dtype(val)
                setattr(feed.query, query_param, val)
                setattr(feed.source, query_param, val)

            else:
                click.echo(f"Must set QueryParameter {query_param} of QueryType {query_type}")
                return None

        return feed

    except ValueError:
        click.echo(f"Value {val} for Query Parameter {query_param} does not match type {param_dtype}")
        return None
