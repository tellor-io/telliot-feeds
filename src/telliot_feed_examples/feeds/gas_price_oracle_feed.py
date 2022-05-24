"""Datafeed for reporting responses to the GasPriceOracle query type.

This GasPriceOracle data feed example queries the
gas price on Mainnet Ethereum on April 1, 2022

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/GasPriceOracle.md

 """
from telliot_core.datafeed import DataFeed
from telliot_core.queries.gas_price_oracle import GasPriceOracle
from telliot_core.sources.gas_price_oracle import GasPriceOracleSource

chain_id = 1
timestamp = 1648771200  # april 1, 2022 unix time

gas_price_oracle_feed = DataFeed(
    query=GasPriceOracle(chain_id, timestamp),
    source=GasPriceOracleSource(chain_id=chain_id, timestamp=timestamp),
)
