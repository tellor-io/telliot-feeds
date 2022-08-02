import os
from typing import Any
from typing import get_args
from typing import get_type_hints
from typing import Optional

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from dotenv import load_dotenv
from telliot_core.apps.core import TelliotCore
from telliot_core.cli.utils import cli_core

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING


DIVA_PROTOCOL_CHAINS = (137, 80001, 3)

load_dotenv()


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
        try:
            from brownie import chain
        except ModuleNotFoundError:
            print("pip install -r requirements-dev.txt in venv to use test config")

        # core.config.main.chain_id = 1337
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
                    key=key,
                    password="",
                )
            else:
                raise Exception("Need an account for chain_id 1337")

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
    Called when the --build-feed flag is used on the telliot-feeds CLI

    This function takes input from the user for the QueryType
    and its matching QueryParameters, the builds a DataFeed
    object if the QueryType is supported and the QueryParameters
    can be casted to their appropriate data types from an input string.

    Returns: DataFeed[Any]

    """
    try:
        msg = (
            "Enter a valid QueryType from the options listed below:"
            + "\n"
            + "\n".join([i for i in DATAFEED_BUILDER_MAPPING.keys()])
            + "\n"
        )
        query_type = input(msg)
        feed: DataFeed[Any] = DATAFEED_BUILDER_MAPPING[query_type]
    except KeyError:
        click.echo(f"No corresponding datafeed found for QueryType: {query_type}\n")
        return None
    for query_param in feed.query.__dict__.keys():
        # accessing the datatype
        type_hints = get_type_hints(feed.query)
        # get param type if type isn't optional
        try:
            param_dtype = get_args(type_hints[query_param])[0]  # parse out Optional type
        except IndexError:
            param_dtype = type_hints[query_param]

        val = input(f"Enter value for QueryParameter {query_param}: ")

        if val is not None:
            try:
                # cast input from string to datatype of query parameter
                val = param_dtype(val)
                setattr(feed.query, query_param, val)
                setattr(feed.source, query_param, val)
            except ValueError:
                click.echo(f"Value {val} for QueryParameter {query_param} does not match type {param_dtype}")
                return None

        else:
            click.echo(f"Must set QueryParameter {query_param} of QueryType {query_type}")
            return None

    return feed
