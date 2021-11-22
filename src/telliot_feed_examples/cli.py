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
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


report_command_options = [
    click.option('--private-key', '-pk', 'private_key', help="override the config's private key"),
    click.option('--chain-id', '-c', 'chain_id', help="override the config's chain id")
]

def check_report_flags(cfg, kwargs):

    if kwargs['private_key'] is not None:
        private_key = kwargs['private_key']
    else:
        private_key = cfg.main.private_key

    return private_key
    # if kwargs['chain_id'] is not None:
    #     chain_id = kwargs['chain_id']
    # else:
    #     chain_id = cfg.main.chain_id


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

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
def report(**kwargs) -> None:
    """Report values to Tellor oracle"""
    pass


@report.command()
@add_options(report_command_options)
def legacyid() -> None:
    "Report active legacy query IDs."

    cfg, master, oracle, endpoint = get_tellor_contracts()

    private_key = check_report_flags(cfg)

    legacy_feeds = get_user_choices()

    if not legacy_feeds:
        click.echo("Given legacy id(s) not supported.")
        return

    legacy_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=private_key,
        master=master,
        oracle=oracle,
        datafeeds=legacy_feeds,
    )

    receipts_statuses = asyncio.run(legacy_reporter.report_once())

    for _, status in receipts_statuses:
        if not status.ok:
            logger.error(status)
            # click.echo(status.error)


@report.command()
@add_options(report_command_options)
def uspce(**kwargs) -> None:
    """Report USPCE value"""

    click.echo("Reporting USPCE (legacy ID 41)")
    cfg, master, oracle, endpoint = get_tellor_contracts()

    private_key = check_report_flags(cfg, kwargs)

    uspce_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=private_key,
        master=master,
        oracle=oracle,
        datafeeds=[uspce_feed],
    )

    receipts_statuses = asyncio.run(uspce_reporter.report_once())

    for _, status in receipts_statuses:
        if not status.ok:
            logger.error(status)
            # click.echo(status.error)


if __name__ == "__main__":
    main()
