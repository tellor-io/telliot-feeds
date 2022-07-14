"""Datafeed for reporting responses to the GasPriceOracle query type.

This GasPriceOracle data feed example queries the
gas price on Mainnet Ethereum on April 1, 2022

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/GasPriceOracle.md

 """
from telliot_feed_examples.datafeed import DataFeed
from telliot_feed_examples.queries.gas_price_oracle import GasPriceOracle
from telliot_feed_examples.sources.gas_price_oracle import GasPriceOracleSource

chainId = 0
timestamp = 0  # april 1, 2022 unix time

gas_price_oracle_feed = DataFeed(
    query=GasPriceOracle(chainId, timestamp),
    source=GasPriceOracleSource(chainId=chainId, timestamp=timestamp),
)
