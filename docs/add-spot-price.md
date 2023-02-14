# Add support for reporting a new spot price
### Prerequisites
- Python >= 3.9, < 3.10
- Setup environment (see [here](contributing.md))

### Steps
1. Add spot price to catalog. See `src/telliot_feeds/queries/query_catalog.py`. For example adding `ETH/USD`:
```python
query_catalog.add_entry(
    tag="eth-usd-spot",
    title="ETH/USD spot price",
    q=SpotPrice(asset="eth", currency="usd"),
)
```
2. Add data feed in `src/telliot_feeds/feeds/`. For example, for adding `ETH/USD`, create file `src/telliot_feeds/feeds/eth_usd_feed.py`:
```python
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

eth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="ETH", currency="USD"),
    source=PriceAggregator(
        asset="eth",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
            BinanceSpotPriceSource(asset="eth", currency="usdt"),
            CoinbaseSpotPriceSource(asset="eth", currency="usd"),
            GeminiSpotPriceSource(asset="eth", currency="usd"),
            KrakenSpotPriceSource(asset="eth", currency="usd"),
        ],
    ),
)
```
    Above, we use the `PriceAggregator` to aggregate the price from multiple sources (automatic API fetches, not sources that require manual entry). The `algorithm` can be `median` or `mean`. The `sources` can be any combination of those found in `src/telliot_feeds/sources/price/spot/`, or you can add your own.

    You're limited by what asset and currency pairs are supported by the underlying APIs (data providers). For example, if you want to add `ETH/JPY`, you might use the `CoinGeckoSpotPriceSource` and `BinanceSpotPriceSource` (which support `ETH/JPY`), but not the `CoinbaseSpotPriceSource` (which does not support `ETH/JPY`). You'll have to check the documentation of the underlying APIs for which pairs they support.

3. Add feed to `CATALOG_FEEDS` constant in `src/telliot_feeds/feeds/__init__.py`:
```python
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed

CATALOG_FEEDS = {
    ...
    "eth-usd-spot": eth_usd_median_feed,
}
```
4. Add currency/asset to supported lists in `src/telliot_feeds/queries/price/spot_price.py`. For example, for adding `ETH/USD`:
```python
CURRENCIES = ["usd", "jpy", "eth"]
SPOT_PRICE_PAIRS = [
    ...
    "ETH/USD",
]
```
4. Test your new feed in `tests/feeds/`. For example, once you've created a datafeed for an `ETH/USD` spot price using an aggregate of a few price sourcees, create file `tests/feeds/test_eth_usd_feed.py`:
```python
import statistics

import pytest

from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed


@pytest.mark.asyncio
async def test_eth_usd_median_feed(caplog):
    """Retrieve median ETH/USD price."""
    v, _ = await eth_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    assert (
        "sources used in aggregate: 4" in caplog.text.lower() or "sources used in aggregate: 5" in caplog.text.lower()
    )
    print(f"ETH/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in eth_usd_median_feed.source.sources if source.latest[0]]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
```
5. Create a pull request to merge your changes into the `main` branch [here](https://github.com/tellor-io/telliot-feeds/compare).
