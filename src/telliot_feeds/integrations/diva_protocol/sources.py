from dataclasses import dataclass
from typing import Any
from typing import Optional

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.sources.price.historical.cryptowatch import (
    CryptowatchHistoricalPriceSource,
)
from telliot_feeds.sources.price.historical.kraken import (
    KrakenHistoricalPriceSource,
)
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


class dUSDSource(DataSource[Any]):
    """Fake source that returns dummy price data"""

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Fetch fake data"""
        price = 1.0
        dt = datetime_now_utc()
        datapoint = (price, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored fake price for DIVA USD at {dt}: {price}")

        return datapoint


@dataclass
class DivaSource(DataSource[Any]):
    """DataSource for Diva Protocol manually-entered data."""

    reference_asset_source: Optional[DataSource[float]] = None
    collat_token_source: Optional[DataSource[float]] = None

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Retrieve new datapoint from sources."""

        if self.reference_asset_source is None or self.collat_token_source is None:
            logger.warning("Diva source not configured.")
            return None, None
        ref_asset_price, _ = await self.reference_asset_source.fetch_new_datapoint()
        collat_token_price, _ = await self.collat_token_source.fetch_new_datapoint()

        if ref_asset_price is None or collat_token_price is None:
            logger.warning("Missing reference asset or collateral token price.")
            return None, None

        data = [ref_asset_price, collat_token_price]
        dt = datetime_now_utc()
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored DIVAProtocol query response at {dt}: {data}")

        return datapoint


def get_historical_price_source(asset: str, currency: str, timestamp: int) -> PriceAggregator:
    """
    Returns PriceAggregator with sources adjusted based on given asset & currency.
    """
    # Use fake testnet source if collateral token is dUSD (DIVA dollar)
    if asset == "dusd" and currency == "usd":
        return dUSDSource()

    source = PriceAggregator(
        asset=asset,
        currency=currency,
        algorithm="median",
        sources=[
            CryptowatchHistoricalPriceSource(asset=asset, currency=currency, ts=timestamp),
            KrakenHistoricalPriceSource(asset="xbt" if asset == "btc" else asset, currency=currency, ts=timestamp),
            # PoloniexHistoricalPriceSource(
            #     asset=asset, currency="tusd" if currency == "usd" else currency, ts=timestamp
            # ),
        ],
    )
    return source
