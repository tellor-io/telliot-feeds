""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import click

from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.directory.tellorx import tellor_directory
from telliot_core.contract.contract import Contract
from telliot_feed_examples.feeds.uspce_feed import uspce_feed
from telliot_feed_examples.reporters.interval import IntervalReporter
import asyncio

from telliot_feed_examples.reporters.report_legacy_price import get_user_choices


def get_tellor_contracts():
    """ Get Contract objects per telliot configuration

    """

    cfg = TelliotConfig()

    tellor_oracle = tellor_directory.find(chain_id=4, name="oracle")[0]
    endpoint = cfg.get_endpoint()
    endpoint.connect()
    oracle = Contract(
        address=tellor_oracle.address,  # "0x07b521108788C6fD79F471D603A2594576D47477",
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
    """telliot command line interface"""
    pass


@main.group()
def report() -> None:
    """Report """
    pass


@report.command()
def legacyid() -> None:
    "Report any active legacy query ID."

    cfg, master, oracle, endpoint = get_tellor_contracts()

    legacy_feeds = get_user_choices()

    legacy_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=legacy_feeds
    )

    receipts_statuses = asyncio.run(legacy_reporter.report_once())

    for _, status in receipts_statuses:
        if not status.ok:
            print(status.error)



@report.command()
def uspce() -> None:
    """Report USPCE"""

    print('Reporting USPCE')
    cfg, master, oracle, endpoint = get_tellor_contracts()

    uspce_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=[uspce_feed],
    )

    tx_receipts = asyncio.run(uspce_reporter.report_once())

    print(tx_receipts)


if __name__ == "__main__":
    main()
