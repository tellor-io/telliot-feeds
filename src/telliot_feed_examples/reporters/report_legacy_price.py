"""Submits legacy query values to TellorX on Rinkeby."""
import asyncio
from typing import List
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.contract.contract import Contract
from telliot_core.datafeed import DataFeed
from telliot_core.directory.tellorx import tellor_directory

from telliot_feed_examples.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed
from telliot_feed_examples.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feed_examples.feeds.eth_jpy_feed import eth_jpy_median_feed
from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter


def get_rinkeby_config() -> TelliotConfig:
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

    tellor_master_rinkeby = tellor_directory.find(
        org="tellor", name="master", chain_id=4
    )

    endpoint.connect()
    master = Contract(
        address="0x657b95c228A5de81cdc3F85be7954072c08A6042",
        abi=tellor_master_rinkeby,
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

    tellor_oracle_rinkeby = tellor_directory.find(
        org="tellor", name="master", chain_id=4
    )

    oracle = Contract(
        address="0x07b521108788C6fD79F471D603A2594576D47477",
        abi=tellor_oracle_rinkeby,
        node=endpoint,
        private_key=cfg.main.private_key,
    )
    oracle.connect()
    return oracle


datafeed_lookup = {
    "1": eth_usd_median_feed,
    "2": btc_usd_median_feed,
    "10": ampl_usd_vwap_feed,
    "50": trb_usd_median_feed,
    "59": eth_jpy_median_feed,
}


def get_user_choices() -> List[DataFeed]:
    print('Enter one or more legacy query ids to select datafeeds (example: "1, 50"):')

    good_input = False
    while not good_input:
        selected = input()
        try:
            # Parse user input
            selected = [s.strip() for s in selected.split(",")]  # type: ignore
            good_input = True
        except ValueError:
            print(
                """Invalid user input. \
                Enter integers separated by commas (example: "2, 50, 59")."""
            )

    selected_datafeeds = []
    msg = "Reporting values for the following legacy query ids:\n"
    for legacy_id in selected:
        if legacy_id in datafeed_lookup:
            selected_datafeeds.append(datafeed_lookup[legacy_id])
            msg += f"{legacy_id}\n"

    return selected_datafeeds


if __name__ == "__main__":
    cfg = get_rinkeby_config()

    master = get_master(cfg)
    oracle = get_oracle(cfg)

    rinkeby_endpoint = cfg.get_endpoint()

    datafeeds = get_user_choices()

    legacy_price_reporter = IntervalReporter(
        endpoint=rinkeby_endpoint,
        private_key=cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeeds=datafeeds,
    )

    _ = asyncio.run(legacy_price_reporter.report_once())
