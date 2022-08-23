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

gas_price_oracle_feed_example = DataFeed(
    query=GasPriceOracle(1, 1656633600),
    source=GasPriceOracleSource(chainId=1, timestamp=1656633600),
)
