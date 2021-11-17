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

    _ = asyncio.run(uspce_reporter.report_once())


if __name__ == "__main__":
    main()
