"""Datafeed for reporting responses to the GasPriceOracle query type.

More info:
https://github.com/tellor-io/dataSpecs/blob/main/types/GasPriceOracle.md

 """
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.gas_price_oracle import GasPriceOracle
from telliot_feeds.sources.gas_price_oracle import GasPriceOracleSource

chainId = None
timestamp = None

gas_price_oracle_feed = DataFeed(
    query=GasPriceOracle(chainId, timestamp),
    source=GasPriceOracleSource(chainId=chainId, timestamp=timestamp),
)
