# Add New Data Type (Custom Oracle Query)

### Steps
1. Your new data type, or query, should be defined in the [dataSpecs](https:://github.com/tellor-io/dataSpecs) repo. If not, [create the spec there](https://github.com/tellor-io/dataSpecs/issues/new?assignees=&labels=&template=new_query_type.yaml&title=%5BNew+Query+Type%5D%3A+) first. Once that's done, follow the steps below.
2. Create a subclass of `AbiQuery` in `src/telliot_feeds/queries/`. For example, if you wanted to implement the [Snapshot query type](https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md), it would look like this:
```python
import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class Snapshot(AbiQuery):
    """Returns the proposal result for a given proposal id (an IPFS hash for a certain proposal) coming from Snapshot.
       A boolean value indicating whether a proposal succeeded (True) or failed (False) should be returned.

    Attributes:
        proposal_id:
            Specifies the requested data a of a valid proposal on Snapshot.

    See https://snapshot.org/ for proposal results.
    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md
    """

    proposalId: Optional[str]

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "proposalId", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a Snapshot query.

        - `bool`: a boolean value true or false equivalent to uint8 restricted to the values 0 and 1
        - `packed`: false
        """

        return ValueType(abi_type="bool", packed=False)
```
3. Next you'll need to add a data source for your query type in `src/telliot_feeds/sources/`. For an example of an automated data source, see `src/telliot_feeds/sources/etherscan_gas.py`. For an example of a data source that requires manual entry, see `src/telliot_feeds/sources/manual/snapshot.py`.
4. Create an instance of the `DataFeed` class in `src/telliot_feeds/feeds/`. For example, if you had implemented the `SpotPrice` query type and added sources for `MATIC/USD`, the `DataFeed` subclass would look like this (`src/telliot_feeds/feeds/matic_usd_feed.py`):
```python
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

matic_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MATIC", currency="USD"),
    source=PriceAggregator(
        asset="matic",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="matic", currency="usd"),
            BinanceSpotPriceSource(asset="matic", currency="usdt"),
            CoinbaseSpotPriceSource(asset="matic", currency="usd"),
            GeminiSpotPriceSource(asset="matic", currency="usd"),
            KrakenSpotPriceSource(asset="matic", currency="usd"),
        ],
    ),
)
```
5. Add example instance of the query type to catalog. For example, if you wanted an example `Snapshot` query instance in the catalog, edit `src/telliot_feeds/queries/query_catalog.py` to include:
```python
query_catalog.add_entry(
    tag="snapshot-proposal-example",
    title="Snapshot proposal example",
    q=Snapshot(proposalId="cce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57"),
)
```
7. Make sure you've added tests for your new query type, data sources, data feed, & changes to the CLI.
8. Submit a PR to the `telliot-feeds` repo. Included an example `submitValue` transaction for your new query type in the PR description. For example [this PR]().
