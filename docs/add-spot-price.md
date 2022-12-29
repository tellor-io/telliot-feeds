# Add support for reporting a new spot price
## Prerequisites
- Python >= 3.9, < 3.10
- Setup environment (see [here](contributing.md))

1. Add spot price to catalog. See `src/telliot_feeds/queries/query_catalog.py`. For example adding `TWTR/USD`:
```python
query_catalog.add_entry(
    tag="twtr-usd-spot",
    title="TWTR/USD spot price",
    q=SpotPrice(asset="twtr", currency="usd"),
)
```

2. Add data feed in `src/telliot_feeds/feeds/`. For example, for adding `TWTR/USD`, create file `src/telliot_feeds/feeds/twtr_usd_feed.py`:
```python
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.manual.spot_price_input_source import SpotPriceManualSource


twtr_usd_manual_feed = DataFeed(query=SpotPrice(asset="twtr", currency="usd"), source=SpotPriceManualSource())
```

3. Add feed to `CATALOG_FEEDS` constant in `src/telliot_feeds/feeds/__init__.py`:
```python
from telliot_feeds.feeds.twtr_usd_feed import twtr_usd_manual_feed

CATALOG_FEEDS = {
    ...
    "twtr-usd-spot": twtr_usd_manual_feed,
}
```

4. Add currency/asset to supported lists in `src/telliot_feeds/queries/price/spot_price.py`. For example, for adding `TWTR/USD`:
```python
CURRENCIES = ["usd", "jpy", "eth"]
SPOT_PRICE_PAIRS = [
    ...
    "TWTR/USD",
]
```

Add spot price with a bunch of different sources
