""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio
from typing import Tuple

import click
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.contract.contract import Contract
from telliot_core.directory.tellorx import tellor_directory
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feed_examples.feeds.uspce_feed import uspce_feed
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.reporters.report_legacy_price import get_user_choices


def get_tellor_contracts() -> Tuple[TelliotConfig, Contract, Contract, RPCEndpoint]:
    """Get Contract objects per telliot configuration"""

    cfg = TelliotConfig()

    tellor_oracle = tellor_directory.find(chain_id=4, name="oracle")[0]
    endpoint = cfg.get_endpoint()
    endpoint.connect()
    oracle = Contract(
        address=tellor_oracle.address,
        abi=tellor_oracle.abi,
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    oracle.connect()

    tellor_master = tellor_directory.find(chain_id=4, name="master")[0]
    endpoint = cfg.get_endpoint()
    endpoint.connect()
    master = Contract(
        address=tellor_master.address,
        abi=tellor_master.abi,
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    master.connect()

    return cfg, master, oracle, endpoint


@click.group()
def main() -> None:
    """Telliot command line interface"""
    pass


@main.group()
def report() -> None:
    """Report values to Tellor oracle"""
    pass


@report.command()
def legacyid() -> None:
    "Report active legacy query IDs."

    cfg, master, oracle, endpoint = get_tellor_contracts()

    legacy_feeds = get_user_choices()

    if not legacy_feeds:
        click.echo("Given legacy id(s) not supported.")
        return

    legacy_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=legacy_feeds,
    )

    receipts_statuses = asyncio.run(legacy_reporter.report_once())

    for _, status in receipts_statuses:
        if not status.ok:
            click.echo(status.error)


@report.command()
def uspce() -> None:
    """Report USPCE value"""

    click.echo("Reporting USPCE (legacy ID 41)")
    cfg, master, oracle, endpoint = get_tellor_contracts()

    uspce_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[uspce_feed],
    )

    receipts_statuses = asyncio.run(uspce_reporter.report_once())

    for _, status in receipts_statuses:
        if not status.ok:
            click.echo(status.error)


if __name__ == "__main__":
    main()
