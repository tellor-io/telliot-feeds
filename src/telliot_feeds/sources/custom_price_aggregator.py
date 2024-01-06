import asyncio
import statistics
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import List
from typing import Literal

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class CustomPriceAggregator(DataSource[float]):

    # identifier
    identifier: str = ""

    #: Asset
    asset: str = ""

    # : Currency of returned price
    currency: str = ""

    # unit
    unit: str = ""

    #: Callable algorithm that accepts an iterable of floats
    algorithm: Literal["median", "mean"] = "median"

    #: Private storage for actual algorithm function
    _algorithm: Callable[..., float] = field(default=statistics.median, init=False, repr=False)

    #: Data feed sources
    sources: List[PriceSource] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.algorithm == "median":
            self._algorithm = statistics.median
        elif self.algorithm == "mean":
            self._algorithm = statistics.mean

    def __str__(self) -> str:
        """Human-readable representation."""
        asset = self.asset.upper()
        currency = self.currency.upper()
        symbol = asset + "/" + currency
        return f"PriceAggregator {symbol} {self.algorithm}"

    async def update_sources(self) -> List[OptionalDataPoint[float]]:
        """Update data feed sources

        Returns:
            Dictionary of updated source values, mapping data source UID
            to the time-stamped answer for that data source
        """

        async def gather_inputs() -> List[OptionalDataPoint[float]]:
            sources = self.sources
            datapoints = await asyncio.gather(*[source.fetch_new_datapoint() for source in sources])
            return datapoints

        inputs = await gather_inputs()

        return inputs

    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        """Update current value with time-stamped value fetched from source

        Args:
            store:  If true and applicable, updated value will be stored
                    to the database

        Returns:
            Current time-stamped value
        """
        datapoints = await self.update_sources()

        prices = []
        for datapoint in datapoints:
            v, _ = datapoint  # Ignore input timestamps
            # Check for valid answers
            if v is not None and isinstance(v, float):
                prices.append(v)

        if not prices:
            logger.warning(f"No prices retrieved for {self}.")
            return None, None

        # Run the algorithm on all valid prices
        logger.info(f"Running {self.algorithm} on {prices}")
        result = self._algorithm(prices)
        datapoint = (result, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info("Feed Price: {} reported at time {}".format(datapoint[0], datapoint[1]))
        logger.info("Number of sources used in aggregate: {}".format(len(prices)))

        return datapoint
