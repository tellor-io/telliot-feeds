import pytest

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.gas_price_oracle_feed import gas_price_oracle_feed
from telliot_feeds.queries.gas_price_oracle import GasPriceOracle
from telliot_feeds.sources.gas_price_oracle import GasPriceOracleSource


@pytest.mark.asyncio
async def test_gas_price_oracle_feed():
    """Test gas price oracle feed."""

    assert isinstance(gas_price_oracle_feed, DataFeed)
    assert isinstance(gas_price_oracle_feed.source, GasPriceOracleSource)
    assert isinstance(gas_price_oracle_feed.query, GasPriceOracle)
    assert gas_price_oracle_feed.query.chainId is None
    assert gas_price_oracle_feed.query.timestamp is None
